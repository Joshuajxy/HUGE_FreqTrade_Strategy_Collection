"""
Debug test script for freqtrade backtest system
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all module imports"""
    print("Testing imports...")
    
    try:
        # Test basic imports
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        # Test data models
        from utils.data_models import StrategyInfo, BacktestConfig, BacktestResult
        print("✅ Data models imported successfully")
        
        # Test error handling
        from utils.error_handling import ErrorHandler, enhanced_error_handler
        print("✅ Error handling imported successfully")
        
        # Test UI components
        from components.ui.main_layout import MainLayout
        print("✅ Main layout imported successfully")
        
        # Test strategy components
        from components.strategy_manager.scanner import StrategyScanner
        from components.strategy_manager.selector import StrategySelector
        print("✅ Strategy components imported successfully")
        
        # Test backtest components
        from components.backtest_config.panel import BacktestConfigPanel
        from components.backtest_config.manager import ConfigManager
        print("✅ Backtest config components imported successfully")
        
        # Test execution components
        from components.execution.scheduler import ExecutionScheduler
        from components.execution.backtest_executor import BacktestExecutor
        print("✅ Execution components imported successfully")
        
        # Test results components
        from components.results.parser import ResultParser
        from components.results.comparator import ResultComparator
        print("✅ Results components imported successfully")
        
        # Test optimization components
        from components.optimization.performance_optimizer import MemoryOptimizer
        from components.optimization.performance_panel import PerformanceMonitoringPanel
        print("✅ Optimization components imported successfully")
        
        # Test integration components
        from components.integration.visualizer_bridge import VisualizerIntegrationPanel
        print("✅ Integration components imported successfully")
        
        # Test jupyter components
        try:
            from components.jupyter_integration.jupyter_panel import JupyterAnalysisPanel
            print("✅ Jupyter components imported successfully")
        except ImportError as e:
            print(f"⚠️ Jupyter components import warning: {e}")
            print("✅ Core system can still function without full Jupyter integration")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        # Test error handler
        from utils.error_handling import ErrorHandler
        ErrorHandler.log_info("Test log message")
        print("✅ Error handler logging works")
        
        # Test strategy scanner
        from components.strategy_manager.scanner import StrategyScanner
        scanner = StrategyScanner(["."])
        print("✅ Strategy scanner initialized")
        
        # Test config panel
        from components.backtest_config.panel import BacktestConfigPanel
        config_panel = BacktestConfigPanel()
        print("✅ Config panel initialized")
        
        # Test performance optimizer
        from components.optimization.performance_optimizer import MemoryOptimizer
        memory_optimizer = MemoryOptimizer()
        print("✅ Memory optimizer initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\nTesting dependencies...")
    
    # Core required packages
    core_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'psutil'
    ]
    
    # Optional packages for full functionality
    optional_packages = [
        'nbformat',
        'nbconvert'
    ]
    
    missing_core = []
    missing_optional = []
    
    for package in core_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} missing (required)")
            missing_core.append(package)
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"⚠️ {package} missing (optional - Jupyter features will be limited)")
            missing_optional.append(package)
    
    if missing_core:
        print(f"\n❌ Missing required packages: {', '.join(missing_core)}")
        print("Install with: pip install " + " ".join(missing_core))
        return False
    
    if missing_optional:
        print(f"\n⚠️ Missing optional packages: {', '.join(missing_optional)}")
        print("Install for full functionality: pip install " + " ".join(missing_optional))
    
    return True

def test_optional_dependencies():
    """Test optional dependencies"""
    print("\nTesting optional dependencies...")
    
    optional_packages = [
        'streamlit_option_menu',
        'papermill',
        'jupyter',
        'jupyterlab'
    ]
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"⚠️ {package} missing (optional)")

def create_requirements_file():
    """Create requirements.txt file"""
    print("\nCreating requirements.txt...")
    
    requirements = [
        "streamlit>=1.28.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "plotly>=5.15.0",
        "psutil>=5.9.0",
        "nbformat>=5.7.0",
        "nbconvert>=7.0.0",
        "streamlit-option-menu>=0.3.6",
        "papermill>=2.4.0",
        "jupyter>=1.0.0",
        "jupyterlab>=4.0.0"
    ]
    
    try:
        with open("requirements.txt", "w") as f:
            f.write("\n".join(requirements))
        print("✅ requirements.txt created")
        return True
    except Exception as e:
        print(f"❌ Error creating requirements.txt: {e}")
        return False

def main():
    """Main debug function"""
    print("🔍 Freqtrade Backtest System Debug Test")
    print("=" * 50)
    
    # Test dependencies first
    deps_ok = test_dependencies()
    test_optional_dependencies()
    
    if not deps_ok:
        print("\n❌ Missing required dependencies. Please install them first.")
        create_requirements_file()
        return False
    
    # Test imports
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ Import tests failed")
        return False
    
    # Test basic functionality
    func_ok = test_basic_functionality()
    
    if not func_ok:
        print("\n❌ Functionality tests failed")
        return False
    
    print("\n✅ All tests passed! System is ready to run.")
    print("\nTo start the application, run:")
    print("streamlit run app.py")
    
    return True

if __name__ == "__main__":
    main()