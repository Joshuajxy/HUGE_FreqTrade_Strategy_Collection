"""
Unit tests for backtest config panel component
"""
import pytest
from datetime import date, timedelta

from components.backtest_config.panel import BacktestConfigPanel
from utils.data_models import BacktestConfig


class TestBacktestConfigPanel:
    """Test cases for BacktestConfigPanel class"""
    
    def test_init(self):
        """Test initialization"""
        panel = BacktestConfigPanel()
        assert panel.config is None
    
    def test_validate_config_valid(self):
        """Test validating a valid configuration"""
        panel = BacktestConfigPanel()
        
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
        
        assert panel._validate_config(config_data) == True
    
    def test_validate_config_invalid_dates(self):
        """Test validating configuration with invalid dates"""
        panel = BacktestConfigPanel()
        
        config_data = {
            'start_date': date.today(),
            'end_date': date.today() - timedelta(days=30),
            'timeframe': '1h',
            'pairs': ['BTC/USDT'],
            'initial_balance': 1000.0,
            'max_open_trades': 3,
            'stake_amount': 'unlimited',
            'fee': 0.001,
            'dry_run_wallet': 1000.0,
            'enable_position_stacking': False
        }
        
        assert panel._validate_config(config_data) == False
    
    def test_validate_config_no_pairs(self):
        """Test validating configuration with no pairs"""
        panel = BacktestConfigPanel()
        
        config_data = {
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today(),
            'timeframe': '1h',
            'pairs': [],
            'initial_balance': 1000.0,
            'max_open_trades': 3,
            'stake_amount': 'unlimited',
            'fee': 0.001,
            'dry_run_wallet': 1000.0,
            'enable_position_stacking': False
        }
        
        assert panel._validate_config(config_data) == False
    
    def test_validate_config_invalid_balance(self):
        """Test validating configuration with invalid balance"""
        panel = BacktestConfigPanel()
        
        config_data = {
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today(),
            'timeframe': '1h',
            'pairs': ['BTC/USDT'],
            'initial_balance': -1000.0,
            'max_open_trades': 3,
            'stake_amount': 'unlimited',
            'fee': 0.001,
            'dry_run_wallet': 1000.0,
            'enable_position_stacking': False
        }
        
        assert panel._validate_config(config_data) == False
    
    def test_get_estimated_execution_time(self):
        """Test estimating execution time"""
        panel = BacktestConfigPanel()
        
        config = BacktestConfig(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            timeframe='1h',
            pairs=['BTC/USDT', 'ETH/USDT'],
            initial_balance=1000.0,
            max_open_trades=3
        )
        
        # Test with different strategy counts
        time_1 = panel.get_estimated_execution_time(config, 1)
        time_2 = panel.get_estimated_execution_time(config, 2)
        
        # Should return a string with estimated time
        assert isinstance(time_1, str)
        assert isinstance(time_2, str)
        assert len(time_1) > 0
        assert len(time_2) > 0


if __name__ == "__main__":
    pytest.main([__file__])