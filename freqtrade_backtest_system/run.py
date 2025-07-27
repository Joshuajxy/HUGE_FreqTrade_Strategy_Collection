#!/usr/bin/env python3
"""
Freqtrade backtest system startup script
"""
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check dependencies"""
    try:
        import streamlit
        import plotly
        import pandas
        import numpy
        print("✅ Core dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_freqtrade():
    """Check if freqtrade is available"""
    try:
        result = subprocess.run(
            ["freqtrade", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Freqtrade check passed: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Freqtrade check failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Freqtrade command not found, please ensure freqtrade is properly installed")
        return False
    except Exception as e:
        print(f"❌ Freqtrade check error: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "configs",
        "configs/backtest",
        "data",
        "temp",
        "notebook_templates",
        "notebook_outputs",
        "jupyter_exports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directory structure check completed")

def main():
    """Main function"""
    print("🚀 Starting Freqtrade backtest system...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check freqtrade
    if not check_freqtrade():
        print("⚠️  Warning: Freqtrade is not available, some features may not work properly")
    
    # Create directories
    create_directories()
    
    print("=" * 50)
    print("🎉 System check completed, starting web interface...")
    print("📱 Please visit in browser: http://localhost:8501")
    print("=" * 50)
    
    # Start Streamlit application
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Thank you for using Freqtrade backtest system!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()