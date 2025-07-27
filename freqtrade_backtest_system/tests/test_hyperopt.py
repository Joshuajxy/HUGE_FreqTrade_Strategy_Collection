import unittest
import sys
from pathlib import Path
from datetime import date
import json
import subprocess
from unittest.mock import patch, MagicMock

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.execution.hyperopt_executor import HyperoptExecutor
from utils.data_models import BacktestConfig
from utils.error_handling import ExecutionError, DataError

class TestHyperoptExecutor(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(__file__).parent / "temp_test_hyperopt"
        self.test_dir.mkdir(exist_ok=True)
        self.config_dir = self.test_dir / "configs"
        self.temp_dir = self.test_dir / "temp"
        self.config_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

        self.executor = HyperoptExecutor(config_dir=self.config_dir, temp_dir=self.temp_dir)
        self.mock_freqtrade_path = Path(__file__).parent / "fixtures" / "mock_freqtrade.py"

    def tearDown(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch.object(subprocess, 'run')
    def test_execute_hyperopt_success(self, mock_run):
        # Configure the mock to simulate a successful freqtrade hyperopt call
        mock_run.return_value = MagicMock(spec=subprocess.CompletedProcess)
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Hyperopt completed successfully."
        mock_run.return_value.stderr = ""

        # Manually create the expected output file for the test
        expected_output_file = self.temp_dir / "hyperopt_results_TestStrategy.json"
        with open(expected_output_file, "w") as f:
            json.dump({
                "results_metrics": {"profit_total": 100.0},
                "best_params": {"buy_rsi": 30},
                "hyperopt_results": []
            }, f)

        strategy_name = "TestStrategy"
        config = BacktestConfig(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            timeframe="5m",
            pairs=["BTC/USDT"],
            initial_balance=1000,
            max_open_trades=3
        )
        hyperopt_params = {"epochs": 10, "loss": "ProfitHyperoptLoss"}

        result_file = self.executor.execute_hyperopt(strategy_name, config, hyperopt_params)
        self.assertTrue(Path(result_file).exists())

        results = self.executor.parse_hyperopt_results(Path(result_file))
        self.assertIn("best_params", results)
        self.assertIn("hyperopt_results", results)

    @patch.object(subprocess, 'run')
    def test_execute_hyperopt_freqtrade_failure(self, mock_run):
        # Configure the mock to simulate a failed freqtrade hyperopt call
        mock_run.side_effect = subprocess.CalledProcessError(1, "freqtrade hyperopt", stderr="Simulated Freqtrade Error")

        strategy_name = "FailingStrategy"
        config = BacktestConfig(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            timeframe="5m",
            pairs=["BTC/USDT"],
            initial_balance=1000,
            max_open_trades=3
        )
        hyperopt_params = {"epochs": 10, "loss": "ProfitHyperoptLoss"}

        with self.assertRaises(ExecutionError):
            self.executor.execute_hyperopt(strategy_name, config, hyperopt_params)

    def test_parse_hyperopt_results_file_not_found(self):
        with self.assertRaises(DataError):
            self.executor.parse_hyperopt_results(Path("non_existent_file.json"))

    def test_parse_hyperopt_results_invalid_json(self):
        invalid_json_file = self.temp_dir / "invalid.json"
        with open(invalid_json_file, "w") as f:
            f.write("{\"key\": \"value") # Malformed JSON
        
        with self.assertRaises(DataError):
            self.executor.parse_hyperopt_results(invalid_json_file)

if __name__ == '__main__':
    unittest.main()