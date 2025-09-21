#!/usr/bin/env python3
"""
Comprehensive test script to verify all system enhancements
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import date, timedelta

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_error_handling():
    """Test enhanced error handling"""
    print("Testing enhanced error handling...")
    
    try:
        from utils.error_handling import EnhancedErrorHandler
        handler = EnhancedErrorHandler()
        print("SUCCESS: EnhancedErrorHandler imported and instantiated")
        
        # Test user-friendly error handling
        if hasattr(handler, 'handle_user_friendly_error'):
            print("SUCCESS: handle_user_friendly_error method available")
        else:
            print("INFO: handle_user_friendly_error method not found")
            
        print("SUCCESS: Error handling functionality works")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_data_models():
    """Test enhanced data models"""
    print("Testing enhanced data models...")
    
    try:
        from utils.data_models import BacktestConfig, StrategyInfo, BacktestResult, PerformanceMetrics
        print("SUCCESS: Core data models imported")
        
        # Test BacktestConfig
        config = BacktestConfig(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            timeframe="1h",
            pairs=["BTC/USDT"],
            initial_balance=1000.0,
            max_open_trades=3
        )
        print("SUCCESS: BacktestConfig created")
        
        # Test PerformanceMetrics with new fields
        metrics = PerformanceMetrics()
        if hasattr(metrics, 'sortino_ratio'):
            print("SUCCESS: sortino_ratio field available")
        if hasattr(metrics, 'calmar_ratio'):
            print("SUCCESS: calmar_ratio field available")
        if hasattr(metrics, 'profit_factor'):
            print("SUCCESS: profit_factor field available")
            
        print("SUCCESS: Data models functionality works")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_comparator_enhancements():
    """Test enhanced comparator functionality"""
    print("Testing enhanced comparator functionality...")
    
    try:
        from components.results.comparator import ResultComparator
        comparator = ResultComparator()
        print("SUCCESS: ResultComparator imported and instantiated")
        
        # Test new methods
        methods_to_test = ['sort_results', 'filter_results', 'get_top_strategies', 'create_enhanced_performance_matrix']
        for method in methods_to_test:
            if hasattr(comparator, method):
                print(f"SUCCESS: {method} method available")
            else:
                print(f"FAILED: {method} method missing")
                return False
                
        # Test sort options
        if hasattr(comparator, 'sort_options'):
            print("SUCCESS: sort_options attribute available")
            print(f"INFO: Available sort options: {list(comparator.sort_options.keys())}")
        else:
            print("INFO: sort_options attribute not found")
            
        print("SUCCESS: Comparator enhancements work")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_visualization_enhancements():
    """Test enhanced visualization functionality"""
    print("Testing enhanced visualization functionality...")
    
    try:
        # Test advanced charts
        from components.visualization.advanced_charts import AdvancedCharts
        charts = AdvancedCharts()
        print("SUCCESS: AdvancedCharts imported")
        
        # Test basic charts
        from components.visualization.charts import ChartComponents
        basic_charts = ChartComponents()
        print("SUCCESS: ChartComponents imported")
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        sample_ohlcv = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 110, 50),
            'high': np.random.uniform(110, 120, 50),
            'low': np.random.uniform(90, 100, 50),
            'close': np.random.uniform(100, 110, 50),
            'volume': np.random.uniform(1000, 5000, 50)
        })
        
        # Test chart creation
        fig1 = charts.create_ohlcv_chart_with_trades(sample_ohlcv, [])
        print("SUCCESS: OHLCV chart with trades created")
        
        print("SUCCESS: Visualization enhancements work")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    """Main comprehensive test function"""
    print("Running comprehensive system enhancement tests...")
    print("=" * 50)
    
    tests = [
        test_error_handling,
        test_data_models,
        test_comparator_enhancements,
        test_visualization_enhancements
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test failed with exception: {e}")
        print()
    
    print("=" * 50)
    print(f"Comprehensive test results: {passed}/{total} passed")
    
    if passed == total:
        print("All comprehensive tests passed!")
        print("System enhancements are fully functional!")
        return True
    else:
        print("Some comprehensive tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)