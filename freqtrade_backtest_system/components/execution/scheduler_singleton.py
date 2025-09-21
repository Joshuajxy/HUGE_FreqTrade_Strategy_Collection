"""
Singleton provider for the application-wide scheduler and thread pool executor.
"""
from concurrent.futures import ThreadPoolExecutor
from .serializable_scheduler import SerializableScheduler

# Centralized configuration for the number of parallel backtest workers
_MAX_WORKERS = 4 

_thread_pool_executor = None
_scheduler_data = None

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
        # Pass the configured number of workers to the data object
        _scheduler_data = SerializableScheduler(max_workers=_MAX_WORKERS)
    return _scheduler_data
