import unittest
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.results.parser import ResultParser
from utils.data_models import BacktestConfig

class TestAnalytics(unittest.TestCase):

    def setUp(self):
        self.parser = ResultParser()
        self.fixture_path = Path(__file__).parent / 'fixtures' / 'sample_backtest_output.txt'
        with open(self.fixture_path, 'r') as f:
            self.sample_output = f.read()

    def test_parse_metrics(self):
        config = BacktestConfig(
            start_date='2024-01-01',
            end_date='2024-01-31',
            timeframe='5m',
            pairs=['BTC/USDT', 'ETH/USDT'],
            initial_balance=10000,
            max_open_trades=2
        )
        result = self.parser.parse_backtest_output(self.sample_output, 'TestStrategy', config)

        self.assertAlmostEqual(result.metrics.total_return, 25.00)
        self.assertEqual(result.metrics.total_trades, 15)
        self.assertEqual(result.metrics.winning_trades, 7)
        self.assertEqual(result.metrics.losing_trades, 8)
        self.assertAlmostEqual(result.metrics.win_rate, 46.666666666666664)
        self.assertAlmostEqual(result.metrics.max_drawdown, 150.00)
        self.assertAlmostEqual(result.metrics.sharpe_ratio, 0.5)
        self.assertAlmostEqual(result.metrics.sortino_ratio, 0.7)
        self.assertAlmostEqual(result.metrics.calmar_ratio, 0.16666666666666666)

if __name__ == '__main__':
    unittest.main()