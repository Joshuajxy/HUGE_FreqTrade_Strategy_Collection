#!/usr/bin/env python3
"""
System test script
"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test module imports"""
    print("🧪 Testing module imports...")
    
    try:
        from utils.data_models import BacktestConfig, StrategyInfo, BacktestResult
        from utils.error_handling import ErrorHandler
        from components.strategy_manager.scanner import StrategyScanner
        from components.strategy_manager.selector import StrategySelector
        from components.backtest_config.panel import BacktestConfigPanel
        from components.backtest_config.manager import ConfigManager
        from components.execution.scheduler import ExecutionScheduler
        from components.execution.backtest_executor import BacktestExecutor
        from components.results.parser import ResultParser
        from components.results.comparator import ResultComparator
        from components.ui.main_layout import MainLayout
        
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Module import failed: {e}")
        return False

def test_data_models():
    """Test data models"""
    print("🧪 Testing data models...")
    
    try:
        from utils.data_models import BacktestConfig, StrategyInfo
        
        # Test BacktestConfig
        config = BacktestConfig(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            timeframe="1h",
            pairs=["BTC/USDT"],
            initial_balance=1000.0,
            max_open_trades=3
        )
        
        # Test serialization
        config_dict = config.to_dict()
        config_restored = BacktestConfig.from_dict(config_dict)
        
        assert config.timeframe == config_restored.timeframe
        
        # Test StrategyInfo
        strategy = StrategyInfo(
            name="TestStrategy",
            file_path=Path("test.py"),
            description="Test strategy"
        )
        
        strategy_dict = strategy.to_dict()
        strategy_restored = StrategyInfo.from_dict(strategy_dict)
        
        assert strategy.name == strategy_restored.name
        
        print("✅ Data models test passed")
        return True
    except Exception as e:
        print(f"❌ Data models test failed: {e}")
        return False

def test_strategy_scanner():
    """Test strategy scanner"""
    print("🧪 Testing strategy scanner...")
    
    try:
        from components.strategy_manager.scanner import StrategyScanner
        
        scanner = StrategyScanner(["."])
        
        # Test scanning (may have no strategy files)
        strategies = scanner.scan_strategies()
        
        print(f"✅ Strategy scanner test passed, found {len(strategies)} strategies")
        return True
    except Exception as e:
        print(f"❌ Strategy scanner test failed: {e}")
        return False

def test_config_manager():
    """Test configuration manager"""
    print("🧪 Testing configuration manager...")
    
    try:
        from components.backtest_config.manager import ConfigManager
        from utils.data_models import BacktestConfig
        
        manager = ConfigManager("test_configs")
        
        # Create test configuration
        config = BacktestConfig(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            timeframe="1h",
            pairs=["BTC/USDT"],
            initial_balance=1000.0,
            max_open_trades=3
        )
        
        # Test save and load
        test_name = "test_config"
        if manager.save_config(config, test_name, "Test configuration"):
            loaded_config = manager.load_config(test_name)
            if loaded_config:
                assert loaded_config.timeframe == config.timeframe
                # Clean up test file
                manager.delete_config(test_name)
        
        print("✅ Configuration manager test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration manager test failed: {e}")
        return False

def test_execution_scheduler():
    """Test execution scheduler"""
    print("🧪 Testing execution scheduler...")
    
    try:
        from components.execution.scheduler import ExecutionScheduler
        
        scheduler = ExecutionScheduler(max_workers=2)
        
        # Test basic functionality
        stats = scheduler.get_execution_statistics()
        assert 'total_tasks' in stats
        assert 'max_workers' in stats
        assert stats['max_workers'] == 2
        
        # Clean up
        scheduler.shutdown(wait=False)
        
        print("✅ Execution scheduler test passed")
        return True
    except Exception as e:
        print(f"❌ Execution scheduler test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting system tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_data_models,
        test_strategy_scanner,
        test_config_manager,
        test_execution_scheduler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test exception: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 Test results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to run")
        return True
    else:
        print("⚠️  Some tests failed, please check related components")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)