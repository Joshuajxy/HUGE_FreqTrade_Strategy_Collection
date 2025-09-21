"""
Singleton provider for the application-wide scheduler and thread pool executor.
"""
import queue
from concurrent.futures import ThreadPoolExecutor
from .serializable_scheduler import SerializableScheduler

# Centralized configuration for the number of parallel backtest workers
_MAX_WORKERS = 4 

_thread_pool_executor = None
_scheduler_data = None
_log_queue = None

def get_thread_pool_executor() -> ThreadPoolExecutor:
    """
    Returns the single, shared instance of the ThreadPoolExecutor.
    This is the actual engine that runs tasks in the background.
    """
    global _thread_pool_executor
    if _thread_pool_executor is None:
        _thread_pool_executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS)
    return _thread_pool_executor

def get_scheduler() -> SerializableScheduler:
    """
    Returns the single, shared instance of the scheduler's data container.
    This holds the information about tasks, but does not execute them.
    """
    global _scheduler_data
    if _scheduler_data is None:
        _scheduler_data = SerializableScheduler(max_workers=_MAX_WORKERS)
    return _scheduler_data

def get_log_queue() -> queue.Queue:
    """
    Returns the single, shared instance of the log queue.
    This is used to pass log messages from background threads to the main UI thread.
    """
    global _log_queue
    if _log_queue is None:
        _log_queue = queue.Queue()
    return _log_queue