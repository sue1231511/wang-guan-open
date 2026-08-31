"""Shared bounded background executor used by the gateway."""
import concurrent.futures
import logging

log = logging.getLogger(__name__)
_MAX_WORKERS = 20
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="bg-worker")
_bg_tasks: set = set()


def _run_with_log(fn, args, kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        log.error("background task failed fn=%s: %s", getattr(fn, "__name__", repr(fn)), exc, exc_info=True)


def submit_background(fn, *args, **kwargs) -> None:
    try:
        _executor.submit(_run_with_log, fn, args, kwargs)
    except Exception as exc:
        log.error("failed to submit background task fn=%s: %s", getattr(fn, "__name__", repr(fn)), exc, exc_info=True)


def track_task(task) -> None:
    """Keep a strong reference to fire-and-forget asyncio tasks until completion."""
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
