"""
Integration tests for the backtest system
"""
import pytest
import tempfile
from pathlib import Path
from datetime import date, timedelta

from components.strategy_manager.scanner import StrategyScanner
from components.strategy_manager.selector import StrategySelector
from components.backtest_config.panel import BacktestConfigPanel
from utils.data_models import BacktestConfig


class TestIntegration:
    """Integration test cases for the backtest system"""
    
    def test_strategy_scanner_to_selector_flow(self):
        """Test the flow from strategy scanning to selection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a mock strategy file
            strategy_content = '''
"""
A test strategy
"""
__author__ = "Test Author"
__version__ = "1.0"

from freqtrade.strategy import IStrategy

class TestStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        return dataframe
        
    def populate_entry_trend(self, dataframe, metadata):
        return dataframe
        
    def populate_exit_trend(self, dataframe, metadata):
        return dataframe
'''
            
            strategy_file = tmp_path / "test_strategy.py"
            with open(strategy_file, 'w') as f:
                f.write(strategy_content)
            
            # Test scanning
            scanner = StrategyScanner([str(tmp_path)])
            strategies = scanner.scan_strategies()
            
            # Should find our test strategy
            assert len(strategies) == 1
            assert strategies[0].name == "TestStrategy"
            assert strategies[0].author == "Test Author"
            assert strategies[0].version == "1.0"
            
            # Test selection
            selector = StrategySelector()
            # Note: We can't fully test the Streamlit UI components in unit tests
            # But we can test the filtering logic
            selector.search_term = "Test"
            filtered = selector._filter_strategies(strategies)
            assert len(filtered) == 1
    
    def test_config_creation_and_validation(self):
        """Test creating and validating backtest configuration"""
        panel = BacktestConfigPanel()
        
        # Test basic config data
        config_data = {
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today(),
            'timeframe': '1h',
            'pairs': ['BTC/USDT'],
            'initial_balance': 1000.0,
            'max_open_trades': 3,
            'stake_amount': 'unlimited',
            'fee': 0.001,
            'dry_run_wallet': 1000.0,
            'enable_position_stacking': False
        }
        
        # Validate config
        assert panel._validate_config(config_data) == True
        
        # Create BacktestConfig object
        config = BacktestConfig(**config_data)
        
        # Convert to freqtrade config
        freqtrade_config = config.to_freqtrade_config("TestStrategy")
        
        # Check key fields
        assert freqtrade_config['strategy'] == "TestStrategy"
        assert freqtrade_config['timeframe'] == "1h"
        assert "BTC/USDT" in freqtrade_config['exchange']['pair_whitelist']
        assert freqtrade_config['max_open_trades'] == 3


if __name__ == "__main__":
    pytest.main([__file__])