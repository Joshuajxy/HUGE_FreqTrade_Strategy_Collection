#!/usr/bin/env python3
"""
Script to run real freqtrade integration tests
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run real freqtrade tests"""
    print("🔥 REAL FREQTRADE INTEGRATION TESTS")
    print("=" * 50)

    # Check if freqtrade is available
    try:
        result = subprocess.run(["freqtrade", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Freqtrade detected: {result.stdout.strip()}")
        else:
            print("❌ Freqtrade command failed")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Freqtrade not found. Please install freqtrade:")
        print("   pip install freqtrade")
        sys.exit(1)

    # Run the tests
    print("\n🚀 Running real freqtrade integration tests...")
    print("This will test actual freqtrade commands without mocks")

    test_file = Path(__file__).parent / "test_backtest_executor.py"
    cmd = [sys.executable, "-m", "pytest", str(test_file), "::TestRealFreqtradeIntegration", "-v", "-s", "--tb=short"]

    print(f"📝 Command: {' '.join(cmd)}")
    print("=" * 50)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()
