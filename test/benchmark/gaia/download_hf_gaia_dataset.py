from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from datasets import (
    load_dataset,  # type: ignore
    load_from_disk,  # type: ignore
)
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError
from tqdm import tqdm  # type: ignore

# define paths and constants
project_root = Path(__file__).resolve().parent.parent.parent.parent
local_data_path = project_root / ".gaia_tmp" / "gaia_dataset"
REPO_ID = "gaia-benchmark/GAIA"
# number of threads for parallel download
MAX_WORKERS = 10
# target download directory (must align with run_test.py search path)
DOWNLOAD_CACHE_DIR = Path.home() / ".cache" / "huggingface" / "datasets" / "downloads"


# download function using hf_hub_download
def download_file_with_hub(file_name: str, split: str, pbar: tqdm):
    """Use huggingface_hub to download a single file and update the progress bar."""
    if not file_name:
        pbar.update(1)
        return "skipped_empty_name"

    # check if file already exists in target cache directory
    # note: hf_hub_download downloads to its own cache; we use local_dir to specify desired location
    target_path = DOWNLOAD_CACHE_DIR / file_name
    if target_path.exists() and target_path.stat().st_size > 0:
        pbar.update(1)
        return "skipped_exists"

    try:
        # build dynamic path inside the repo
        filename_in_repo = f"2023/{split}/{file_name}"

        hf_hub_download(
            repo_id=REPO_ID,
            filename=filename_in_repo,
            repo_type="dataset",
            # download directly into directory expected by run_test.py
            local_dir=DOWNLOAD_CACHE_DIR,
        )
        pbar.update(1)
        return "success"
    except HfHubHTTPError as e:
        if "404" in str(e):
            pbar.write(f"❌ file not found in repo (404): {filename_in_repo}")
        else:
            pbar.write(f"❌ download failed (HTTP Error): {file_name} - {e}")
        pbar.update(1)
        return f"failed: {e}"
    except Exception as e:
        pbar.write(f"❌ unknown error: {file_name} - {e}")
        pbar.update(1)
        return f"failed: {e}"


def main():
    """Main function to orchestrate the dataset download and verification."""
    print(f"📁 loading dataset metadata from local path: {local_data_path}")
    if not local_data_path.exists():
        print(f"  - local dataset path not found: '{local_data_path}'")
        print("  - downloading from hub...")

        dataset = load_dataset(REPO_ID)
        dataset.save_to_disk(str(local_data_path))
        print(f"✅ dataset metadata downloaded and saved to {local_data_path}")
    dataset = load_from_disk(str(local_data_path))
    print("✅ dataset metadata loaded successfully.")

    # collect (file_name, split) tuples
    files_to_download = set()
    for split in dataset.keys():
        for sample in dataset[split]:
            if sample.get("file_name"):
                # store file name with its split
                files_to_download.add((sample["file_name"], split))

    if not files_to_download:
        print("✅ no files need to be downloaded.")
        return

    print(f"\n found {len(files_to_download)} unique files to download/verify.")
    DOWNLOAD_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📂 target directory: {DOWNLOAD_CACHE_DIR}")

    # parallel download with thread pool
    with tqdm(total=len(files_to_download), desc="下载/验证 GAIA 文件") as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(download_file_with_hub, fname, fsplit, pbar)
                for fname, fsplit in files_to_download
            ]
            for future in as_completed(futures):
                future.result()

    print("\n🎉 all files downloaded/verified!")
    print("   you can now safely run the evaluation script.")


if __name__ == "__main__":
    main()
