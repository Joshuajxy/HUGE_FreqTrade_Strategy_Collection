"""
Singleton pattern for the BacktestExecutor.
Ensures a single, shared instance of the executor is used throughout the application,
especially for the scheduler to submit tasks.
"""
from .backtest_executor import BacktestExecutor

_executor_instance = None

def get_executor():
    """
    Returns the single, shared instance of the BacktestExecutor.
    """
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = BacktestExecutor()
    return _executor_instance
