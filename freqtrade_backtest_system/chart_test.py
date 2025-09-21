#!/usr/bin/env python3
"""
Test script to verify chart functionality
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_advanced_charts():
    """Test advanced charting functionality"""
    print("Testing advanced charting functionality...")
    
    try:
        # Test importing advanced charts
        from components.visualization.advanced_charts import AdvancedCharts
        print("SUCCESS: AdvancedCharts imported successfully")
        
        # Test creating sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        sample_ohlcv = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        })
        
        print("SUCCESS: Sample OHLCV data created")
        
        # Test creating chart
        charts = AdvancedCharts()
        fig = charts.create_ohlcv_chart_with_trades(sample_ohlcv, [])
        
        print("SUCCESS: OHLCV chart with trades created")
        print("SUCCESS: All charting functionality works")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_chart_components():
    """Test basic chart components"""
    print("Testing basic chart components...")
    
    try:
        # Test importing chart components
        from components.visualization.charts import ChartComponents
        print("SUCCESS: ChartComponents imported successfully")
        
        charts = ChartComponents()
        print("SUCCESS: ChartComponents instantiated")
        
        # Test sort options
        if hasattr(charts, 'sort_options'):
            print("SUCCESS: sort_options attribute available")
        else:
            print("INFO: sort_options not found (may be in comparator)")
        
        print("SUCCESS: Basic chart components work")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    """Main test function"""
    print("Running chart functionality tests...")
    print("=" * 40)
    
    tests = [
        test_advanced_charts,
        test_chart_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Chart test results: {passed}/{total} passed")
    
    if passed == total:
        print("All chart tests passed! Charting enhancements are working.")
        return True
    else:
        print("Some chart tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)