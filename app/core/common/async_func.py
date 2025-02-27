import asyncio
import concurrent.futures
import threading
from typing import Any


def run_async_function(
    async_func,
    *args: Any,
    **kwargs: Any,
):
    """Run an async function in a new event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # use a thread pool to run the async function, in the case of nested event loops
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:

                def run_in_new_loop():
                    # create a new event loop
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(async_func(*args, **kwargs))
                    finally:
                        new_loop.close()

                # submit the task to the thread pool and wait for the result
                future = executor.submit(run_in_new_loop)
                return future.result()
        else:
            # if the loop exists but is not running, use it directly
            return loop.run_until_complete(async_func(*args, **kwargs))
    except RuntimeError:
        # create a new one, if no event loop is found
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()


def run_in_thread(func, *args, **kwargs):
    """Run a function in a new thread without blocking the current thread."""

    def thread_target():
        return func(*args, **kwargs)

    thread = threading.Thread(target=thread_target)
    thread.daemon = True
    thread.start()

    # return thread object to allow caller to choose to thread.join and wait
    return thread
