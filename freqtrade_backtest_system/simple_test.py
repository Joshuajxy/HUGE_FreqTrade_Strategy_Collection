#!/usr/bin/env python3
"""
Simple test script to verify system functionality
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Test basic imports"""
    print("Testing basic imports...")
    
    try:
        # Test core imports
        from utils.data_models import BacktestConfig, StrategyInfo
        from utils.error_handling import ErrorHandler
        from components.strategy_manager.scanner import StrategyScanner
        from components.results.comparator import ResultComparator
        
        print("SUCCESS: Basic imports work")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_enhanced_features():
    """Test enhanced features"""
    print("Testing enhanced features...")
    
    try:
        # Test new comparator features
        from components.results.comparator import ResultComparator
        comparator = ResultComparator()
        
        # Check if new methods exist
        if hasattr(comparator, 'sort_results'):
            print("SUCCESS: sort_results method available")
        else:
            print("FAILED: sort_results method missing")
            return False
            
        if hasattr(comparator, 'filter_results'):
            print("SUCCESS: filter_results method available")
        else:
            print("FAILED: filter_results method missing")
            return False
            
        if hasattr(comparator, 'create_enhanced_performance_matrix'):
            print("SUCCESS: create_enhanced_performance_matrix method available")
        else:
            print("FAILED: create_enhanced_performance_matrix method missing")
            return False
            
        print("SUCCESS: All enhanced features available")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    """Main test function"""
    print("Running simple system tests...")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_enhanced_features
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Test results: {passed}/{total} passed")
    
    if passed == total:
        print("All tests passed! System enhancements are working.")
        return True
    else:
        print("Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)