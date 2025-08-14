import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import redirect_stdout
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import string
from typing import Union, cast
import warnings

import datasets
from litellm import completion
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import ModelResponse

from app.core.common.system_env import SystemEnv
from app.core.model.message import HybridMessage, TextMessage
from app.core.sdk.agentic_service import AgenticService

parser = argparse.ArgumentParser()
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# prompt template customized for GAIA evaluation
GAIA_SUMMARY_PROMPT_TEMPLATE = """You are an expert in formatting answers for academic benchmarks. Your task is to extract the final answer from a detailed thought process provided by an AI agent.

Based on the original question and the agent's verbose answer below, provide ONLY the final answer.

**Formatting Rules (Follow Strictly):**
- Your response must contain ONLY the final answer, with no extra text, explanations, or prefixes like "FINAL ANSWER:".
- If the answer is a number, return only the number without any units unless specified otherwise.
- If the answer is a string, don't use abbreviations (e.g. for states).
- If the answer is a comma separated list, apply the above rules to each element in the list.

**Original Question:**
{question}

---

**Agent's Verbose Answer:**
{verbose_answer}

---

Now, provide the extracted and formatted final answer below:"""  # noqa: E501


def load_gaia_dataset(split: str, level: str) -> datasets.Dataset:
    """
    Loads the GAIA dataset from local disk and filters it by the specified split and level.
    """
    local_data_path = os.path.join(project_root, ".gaia_tmp", "gaia_dataset")
    if not os.path.exists(local_data_path):
        raise FileNotFoundError(
            f"Error: Local dataset not found at '{local_data_path}'. "
            "Please run the `hugging_face_dataset.py` script first to download and save the data."
        )

    print(f"✅ Loading dataset from local disk: '{local_data_path}'")
    gaia_dataset = datasets.load_from_disk(local_data_path)

    if split not in gaia_dataset:
        available_splits = list(gaia_dataset.keys())
        raise ValueError(
            f"Error: Split '{split}' not found in dataset. Available splits: {available_splits}"
        )

    dataset = gaia_dataset[split]
    assert isinstance(dataset, datasets.Dataset), "Loaded data is not of type datasets.Dataset"
    if level != "all":
        print(f"ℹ️  Filtering for level '{level}' samples...")
        original_size = len(dataset)
        dataset = dataset.filter(lambda example: str(example["Level"]) == level)
        print(f"  - Filtered samples: {len(dataset)} (from {original_size})")

    return dataset


def load_processed_task_ids(log_dir: Path, split: str, level: str) -> set[str]:
    """
    Scan existing gaia_results_{split}_level-{level}_*.jsonl files and
    collect previously processed task_ids to avoid re-running them.
    """
    processed: set[str] = set()
    if not log_dir.exists():
        return processed
    pattern = f"gaia_results_{split}_level-{level}_*.jsonl"
    for fp in log_dir.glob(pattern):
        try:
            with fp.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        tid = obj.get("task_id")
                        if isinstance(tid, str):
                            processed.add(tid)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue
    return processed


def process_single_sample(
    sample: dict, agent_config_path: str, project_root_path: str, split: str
) -> dict:
    """
    Processes a single sample through the full evaluation pipeline: calling the agent,
    summarizing the output, scoring the result, and returning a results dictionary.
    This function is designed to be run in a separate process.
    """
    task_id = sample["task_id"]
    question = sample["Question"]
    ground_truth_answer = sample["Final answer"]
    level = sample.get("Level", "N/A")
    file_name = sample.get("file_name", "")

    # --- setup logging ---
    log_dir = Path(project_root_path) / "test/benchmark/gaia/running_logs"
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / f"gaia_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id}.log"

    with open(log_file_path, "w", encoding="utf-8", buffering=1) as log_file:
        path_for_agent = ""
        if file_name:
            # 2. define and create local file staging directory
            local_file_staging_dir = Path(project_root_path) / ".gaia_tmp" / "files"
            local_file_staging_dir.mkdir(parents=True, exist_ok=True)

            source_file_path = None
            hf_downloads_cache = Path.home() / ".cache" / "huggingface" / "datasets" / "downloads"
            year = "2023"  # GAIA 2023 dataset

            # 3. locate the source file
            direct_path = hf_downloads_cache / year / split / file_name
            print(f"ℹ️  Attempting to find source file at direct path: {direct_path}")
            if direct_path.exists():
                source_file_path = direct_path
                print(f"✅ Source file found directly at: {source_file_path}")
            else:
                print(
                    f"⚠️  Direct path not found. Falling back to recursive search in '{hf_downloads_cache}'..."
                )
                found_files = list(hf_downloads_cache.rglob(file_name))
                if found_files:
                    if len(found_files) > 1:
                        print(
                            f"⚠️  WARNING: Found multiple files named '{file_name}'. Using the first one: {found_files[0]}"
                        )
                    source_file_path = found_files[0]
                    print(f"✅ Source file found via fallback search at: {source_file_path}")

            # 4. if source file is found, copy it to the staging area and generate relative path
            if source_file_path:
                try:
                    staged_file_path = local_file_staging_dir / file_name
                    shutil.copy2(source_file_path, staged_file_path)
                    print(f"✅ Copied file to local staging area: {staged_file_path}")

                    # 5. generate path relative to project root for agent usage
                    relative_path = staged_file_path.relative_to(project_root_path)
                    path_for_agent = str(relative_path)
                    print(f"✅ Generated relative path for agent: {path_for_agent}")

                except Exception as e:
                    print(
                        f"❌ CRITICAL ERROR: Failed to copy file '{source_file_path}' to staging area: {e}"
                    )
                    path_for_agent = ""  # copy failed, do not pass path
            else:
                print(f"❌ CRITICAL ERROR: File '{file_name}' not found in Hugging Face cache.")
                print("   Please ensure you have run the data download script on this machine.")
                print("   The file path will not be passed to the agent.")

        # --- construct the full question using the relative path ---
        full_question = "Current time: 2025-08-01 12:00:00\n\n" + question
        if file_name and path_for_agent:
            full_question += f"\n\nThe following file is uploaded by the user with the question: {path_for_agent}"

        with redirect_stdout(log_file):
            # --- task header ---
            print("=" * 80)
            print(f"🚀 PROCESSING TASK: {task_id}")
            print(f"   Level: {level}, Split: {split}")
            print(f"   Timestamp: {datetime.now()}")
            if file_name:
                print(
                    f"   Attached File: {file_name} -> {path_for_agent if path_for_agent else 'NOT FOUND / FAILED TO STAGE'}"
                )
            print("-" * 80)
            print(f"❓ QUESTION (Passed to Agent):\n{full_question}\n")
            print(f"🎯 GROUND TRUTH:\n{ground_truth_answer}\n")

            # --- agent initialization and execution ---
            print("=" * 80)
            print("--- 1. agent invocation ---")
            mas = AgenticService.load(agent_config_path)
            user_message = TextMessage(payload=full_question)

            print("🤖 Calling Chat2Graph Agent...")
            service_message = mas.session().submit(user_message).wait()

            # --- process agent output ---
            if isinstance(service_message, TextMessage):
                model_output = service_message.get_payload()
            elif isinstance(service_message, HybridMessage):
                text_message = service_message.get_instruction_message()
                model_output = text_message.get_payload()
            else:
                model_output = f"Error: Unexpected response type {type(service_message)}"
            print("Agent execution complete.\n")

            print("--- 2. agent's verbose output ---")
            print("=" * 80)
            print(model_output)
            print("-" * 80 + "\n")

            # --- summarization and formatting ---
            print("--- 3. answer summarization ---")
            print("=" * 80)
            print("✨ Summarizing and formatting final answer using LLM...")
            summarized_answer = summarize(question, model_output)
            print(f"Formatted Answer: '{summarized_answer}'\n")

            # --- scoring ---
            print("--- 4. scoring ---")
            print("=" * 80)
            print("⚖️  Evaluating using the official scorer...")
            is_correct = question_scorer(summarized_answer, ground_truth_answer)
            result_str = "✅ CORRECT" if is_correct else "❌ INCORRECT"
            print(f"Result: {result_str}")
            print(f"  - Model Answer: '{summarized_answer}'")
            print(f"  - Ground Truth: '{ground_truth_answer}'\n")

            # --- prepare submission entry ---
            submission_entry = {
                "task_id": task_id,
                "model_answer": summarized_answer,
                "reasoning_trace": model_output,
                "is_correct": is_correct,  # Temporary field for final statistics
            }
            return submission_entry


def main():
    """
    Main function to parse command-line arguments, load data, process samples
    in parallel, and report the final results.
    """
    parser.add_argument("--sample_num", type=int, default=1, help="Number of samples to run.")
    parser.add_argument(
        "--split",
        type=str,
        choices=["validation", "test"],
        default="validation",
        help="Dataset split to use.",
    )
    parser.add_argument(
        "--level",
        type=str,
        default="all",
        choices=["1", "2", "3", "all"],
        help="GAIA task difficulty level to run (1, 2, 3, or all).",
    )
    parser.add_argument(
        "--parallel_num", type=int, default=2, help="Maximum number of parallel processes."
    )
    parser.add_argument("--task_ids", type=str, nargs="+", help="Specific task IDs to run.")
    parser.add_argument(
        "--random",
        action="store_true",
        help="If set, randomly select samples instead of taking them from the start.",
    )
    args = parser.parse_args()

    print("--- GAIA evaluation script started ---")
    print(
        f"Config: Level={args.level}, Samples={args.sample_num}, Split={args.split}, "
        f"Parallelism={args.parallel_num}"
    )
    if args.task_ids:
        print(f"Specified task IDs: {args.task_ids}")

    # --- load dataset ---
    try:
        dataset = load_gaia_dataset(args.split, args.level)
        if args.task_ids:
            print("ℹ️  Filtering samples by specified task_id...")
            samples_to_run = dataset.filter(lambda example: example["task_id"] in args.task_ids)
            if len(samples_to_run) != len(args.task_ids):
                found_ids = {s["task_id"] for s in samples_to_run}
                missing_ids = set(args.task_ids) - found_ids
                print(
                    f"⚠️  Warning: The following task_id not found in dataset: {list(missing_ids)}"
                )
        else:
            log_dir = Path(project_root) / "test/benchmark/gaia/running_logs"
            processed_ids = load_processed_task_ids(log_dir, args.split, args.level)
            if processed_ids:
                print(
                    f"ℹ️  Found {len(processed_ids)} previously processed task_ids. Skipping them."
                )
                before = len(dataset)
                dataset = dataset.filter(lambda example: example["task_id"] not in processed_ids)
                print(f"   Remaining unprocessed samples: {len(dataset)} (from {before})")

            if len(dataset) == 0:
                print(
                    "✅ All tasks for this split & level have already been processed. Nothing to do."
                )
                return
            if args.random:
                print("ℹ️  Selecting random samples...")
                samples_to_run = dataset.shuffle().select(
                    range(min(args.sample_num, len(dataset)))
                )
            else:
                samples_to_run = dataset.select(range(min(args.sample_num, len(dataset))))
        print(f"✅ Loaded {len(samples_to_run)} samples for evaluation.")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Data loading failed: {e}")
        return

    # --- parallel processing ---
    results = []
    agent_config_path = os.path.join(project_root, "gaia_agents.yml")

    with ProcessPoolExecutor(max_workers=args.parallel_num) as executor:
        future_to_sample = {
            executor.submit(
                process_single_sample, sample, agent_config_path, project_root, args.split
            ): sample
            for sample in samples_to_run
        }

        for future in as_completed(future_to_sample):
            sample = future_to_sample[future]
            try:
                result = future.result()
                results.append(result)
                print(f"✅ Finished processing task: {sample['task_id']}")
            except Exception as exc:
                print(f"❌ Task {sample['task_id']} raised exception: {exc}")
                results.append(
                    {
                        "task_id": sample["task_id"],
                        "model_answer": "EXECUTION_ERROR",
                        "reasoning_trace": str(exc),
                        "is_correct": False,
                    }
                )

    # --- save and report results ---
    log_dir = Path(project_root) / "test/benchmark/gaia/running_logs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"gaia_results_{args.split}_level-{args.level}_{timestamp}.jsonl"
    output_path = log_dir / output_filename

    correct_count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for res in results:
            if res.get("is_correct"):
                correct_count += 1
            # Remove temporary fields from the results to comply with the official submission format.
            submission_entry = {k: v for k, v in res.items() if k != "is_correct"}
            f.write(json.dumps(submission_entry) + "\n")

    total_processed = len(results)
    accuracy = (correct_count / total_processed * 100) if total_processed > 0 else 0

    print("\n" + "=" * 50)
    print("🎉 Evaluation complete!")
    print("--- Final results summary ---")
    print(f"  - Total processed samples: {total_processed}")
    print(f"  - Correct samples: {correct_count}")
    print(f"  - Accuracy: {accuracy:.2f}%")
    print(f"\n📄 Detailed submission file saved to: {output_path}")
    print(f"🪵 Individual task logs stored in: {log_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()


def summarize(question: str, verbose_answer: str) -> str:
    """
    Uses an LLM to summarize the agent's verbose output into a concise final answer
    that conforms to GAIA specifications.
    """
    messages = [
        {
            "role": "user",
            "content": GAIA_SUMMARY_PROMPT_TEMPLATE.format(
                question=question, verbose_answer=verbose_answer
            ),
        }
    ]

    try:
        model_response: Union[ModelResponse, CustomStreamWrapper] = completion(
            model=SystemEnv.LLM_NAME,
            api_base=SystemEnv.LLM_ENDPOINT,
            api_key=SystemEnv.LLM_APIKEY,
            messages=messages,
            temperature=0.0,  # Use a low temperature for deterministic formatting
        )
        summarized_content = cast(str, model_response.choices[0].message.content)
        return summarized_content.strip()
    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        return f"Error during summarization: {e}"


# =============
# scorer.py
# =============


def normalize_number_str(number_str: str) -> float:
    # we replace these common units and commas to allow
    # conversion to float
    for char in ["$", "%", ","]:
        number_str = number_str.replace(char, "")
    try:
        return float(number_str)
    except ValueError:
        print(f"String {number_str} cannot be normalized to number str.")
        return float("inf")


def split_string(
    s: str,
    char_list: list[str] | None = None,
) -> list[str]:
    if char_list is None:
        char_list = [",", ";"]
    pattern = f"[{''.join(char_list)}]"
    return re.split(pattern, s)


def question_scorer(
    model_answer: str,
    ground_truth: str,
) -> bool:
    def is_float(element: any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False

    if model_answer is None:
        model_answer = "None"

    # if gt is a number
    if is_float(ground_truth):
        print(f"Evaluating {model_answer} as a number.")
        normalized_answer = normalize_number_str(model_answer)
        return normalized_answer == float(ground_truth)

    # if gt is a list
    elif any(char in ground_truth for char in [",", ";"]):
        print(f"Evaluating {model_answer} as a comma separated list.")
        # question with the fish: normalization removes punct

        gt_elems = split_string(ground_truth)
        ma_elems = split_string(model_answer)

        # check length is the same
        if len(gt_elems) != len(ma_elems):
            warnings.warn(
                "Answer lists have different lengths, returning False.",
                UserWarning,
                stacklevel=2,
            )
            return False

        # compare each element as float or str
        comparisons = []
        for ma_elem, gt_elem in zip(ma_elems, gt_elems, strict=False):
            if is_float(gt_elem):
                normalized_ma_elem = normalize_number_str(ma_elem)
                comparisons.append(normalized_ma_elem == float(gt_elem))
            else:
                # we do not remove punct since comparisons can include punct
                comparisons.append(
                    normalize_str(ma_elem, remove_punct=False)
                    == normalize_str(gt_elem, remove_punct=False)
                )
        return all(comparisons)

    # if gt is a str
    else:
        print(f"Evaluating {model_answer} as a string.")
        return normalize_str(model_answer) == normalize_str(ground_truth)


def normalize_str(input_str, remove_punct=True) -> str:
    """
    Normalize a string by:
    - Removing all white spaces
    - Optionally removing punctuation (if remove_punct is True)
    - Converting to lowercase
    Parameters:
    - input_str: str, the string to normalize
    - remove_punct: bool, whether to remove punctuation (default: True)
    Returns:
    - str, the normalized string
    """
    # Remove all white spaces. Required e.g for seagull vs. sea gull
    no_spaces = re.sub(r"\s", "", input_str)

    # Remove punctuation, if specified.
    if remove_punct:
        translator = str.maketrans("", "", string.punctuation)
        return no_spaces.lower().translate(translator)
    else:
        return no_spaces.lower()
