"""
Test runner script for the backtest system
"""
import subprocess
import sys
from pathlib import Path

def run_all_tests():
    """Run all tests"""
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    # Check if venv exists
    if not venv_python.exists():
        print("Virtual environment not found. Please create it first.")
        return False
    
    # Run pytest
    try:
        result = subprocess.run([
            str(venv_python),
            "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short"
        ], cwd=project_root, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def run_tests_by_component(component_name):
    """Run tests for a specific component"""
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    # Check if venv exists
    if not venv_python.exists():
        print("Virtual environment not found. Please create it first.")
        return False
    
    # Run pytest for specific component
    try:
        result = subprocess.run([
            str(venv_python),
            "-m", "pytest",
            f"tests/test_{component_name}.py",
            "-v",
            "--tb=short"
        ], cwd=project_root, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        component = sys.argv[1]
        print(f"Running tests for component: {component}")
        success = run_tests_by_component(component)
    else:
        print("Running all tests...")
        success = run_all_tests()
    
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed!")
        sys.exit(1)