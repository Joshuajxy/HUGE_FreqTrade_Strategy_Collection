import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from utils.data_models import BacktestConfig
from utils.error_handling import ErrorHandler, ExecutionError, DataError

class HyperoptExecutor:
    def __init__(self, config_dir: Path = Path("configs"), temp_dir: Path = Path("temp")):
        self.config_dir = config_dir
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def execute_hyperopt(self, strategy_name: str, config: BacktestConfig, hyperopt_params: Dict[str, Any]) -> str:
        temp_config_path = self.temp_dir / f"hyperopt_config_{strategy_name}.json"
        temp_output_path = self.temp_dir / f"hyperopt_results_{strategy_name}.json"

        # Create a temporary config file for freqtrade
        freqtrade_config = config.to_freqtrade_config(strategy_name)
        # Add hyperopt specific configurations
        freqtrade_config["hyperopt"] = hyperopt_params

        with open(temp_config_path, "w") as f:
            import json
            json.dump(freqtrade_config, f, indent=2)

        cmd = [
            "freqtrade", "hyperopt",
            "--config", str(temp_config_path),
            "--strategy", strategy_name,
            "--epochs", str(hyperopt_params.get("epochs", 100)),
            "--spaces", "default", # Can be customized later
            "--hyperopt-loss", hyperopt_params.get("loss", "ShortTradeDurHyperoptLoss"),
            "--export-filename", str(temp_output_path)
        ]

        try:
            ErrorHandler.log_info(f"Executing Hyperopt for {strategy_name} with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ErrorHandler.log_info(f"Hyperopt for {strategy_name} completed successfully.")
            return str(temp_output_path)
        except subprocess.CalledProcessError as e:
            ErrorHandler.log_error(f"Hyperopt for {strategy_name} failed: {e.stderr}")
            raise ExecutionError(f"Hyperopt execution failed: {e.stderr}")
        except FileNotFoundError:
            ErrorHandler.log_error("Freqtrade command not found. Please ensure Freqtrade is installed and in your PATH.")
            raise ExecutionError("Freqtrade command not found.")
        except Exception as e:
            ErrorHandler.log_error(f"An unexpected error occurred during Hyperopt: {e}")
            raise ExecutionError(f"An unexpected error occurred: {e}")

    def parse_hyperopt_results(self, result_file_path: Path) -> Dict[str, Any]:
        try:
            with open(result_file_path, "r") as f:
                import json
                results = json.load(f)
            return results
        except FileNotFoundError:
            ErrorHandler.log_error(f"Hyperopt result file not found: {result_file_path}")
            raise DataError(f"Hyperopt result file not found: {result_file_path}")
        except json.JSONDecodeError:
            ErrorHandler.log_error(f"Invalid JSON in Hyperopt result file: {result_file_path}")
            raise DataError(f"Invalid JSON in Hyperopt result file: {result_file_path}")
        except Exception as e:
            ErrorHandler.log_error(f"Failed to parse Hyperopt results: {e}")
            raise DataError(f"Failed to parse Hyperopt results: {e}")
