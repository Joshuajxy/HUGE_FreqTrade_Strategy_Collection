
from components.execution.executor_singleton import get_executor
from utils.data_models import BacktestConfig, StrategyInfo

def run_backtest_task(task_id: str, strategy_info: StrategyInfo, config: BacktestConfig):
    """
    Function to be executed in a separate process to run a backtest.
    """
    # Get the singleton executor instance
    executor = get_executor()
    return executor.execute_backtest(task_id, strategy_info, config)
