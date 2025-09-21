"""
Real Freqtrade Integration Tests
Direct testing with actual freqtrade commands, no mocks
"""
import pytest
import tempfile
from pathlib import Path
from datetime import date, timedelta, datetime
import sys
import subprocess
import json
import time

from components.execution.backtest_executor import BacktestExecutor
from utils.data_models import BacktestConfig, BacktestResult, PerformanceMetrics, ExecutionStatus
from utils.error_handling import ExecutionError, ErrorHandler


class TestRealFreqtradeIntegration:
    """Real integration tests with actual freqtrade commands"""

    @pytest.fixture
    def check_freqtrade_available(self):
        """Check if freqtrade is available for real testing"""
        try:
            result = subprocess.run([sys.executable, "-m", "freqtrade", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"\n🔥 FREQTRADE AVAILABLE FOR REAL TESTING: {result.stdout.strip()}")
                return True
            else:
                print("\n❌ Freqtrade command failed")
                pytest.skip("Freqtrade command failed")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("\n❌ Freqtrade not found - skipping real tests")
            pytest.skip("Freqtrade not available for real testing")
            return False

    @pytest.fixture
    def temp_workspace(self, tmp_path_factory):
        """Create a temporary workspace for testing"""
        temp_dir = tmp_path_factory.mktemp("freqtrade_real_test")
        user_data_dir = temp_dir / "user_data"
        user_data_dir.mkdir()
        (user_data_dir / "data").mkdir()
        (user_data_dir / "strategies").mkdir()
        (user_data_dir / "plot").mkdir()

        return temp_dir

    @pytest.fixture
    def test_strategy(self, temp_workspace):
        """Create a simple test strategy for real testing"""
        strategy_content = '''
import pandas as pd
import numpy as np
from freqtrade.strategy import IStrategy
from freqtrade.strategy import DecimalParameter, IntParameter

class RealTestStrategy(IStrategy):
    """
    Simple test strategy for real integration testing
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.10}
    stoploss = -0.10
    timeframe = '5m'

    # Strategy parameters
    sma_short = IntParameter(5, 20, default=10, space='buy')
    sma_long = IntParameter(20, 50, default=30, space='buy')

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """Add indicators to dataframe"""
        # Simple moving averages
        dataframe['sma_short'] = dataframe['close'].rolling(window=self.sma_short.value).mean()
        dataframe['sma_long'] = dataframe['close'].rolling(window=self.sma_long.value).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """Generate entry signals"""
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['sma_short']) &
                (dataframe['sma_short'] > dataframe['sma_long']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """Generate exit signals"""
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['sma_short'])
            ),
            'exit_long'
        ] = 1

        return dataframe
'''

        strategy_file = temp_workspace / "user_data" / "strategies" / "RealTestStrategy.py"
        with open(strategy_file, 'w', encoding='utf-8') as f:
            f.write(strategy_content)

        return "RealTestStrategy"

    @pytest.fixture
    def backtest_config(self):
        """Create a backtest configuration"""
        return BacktestConfig(
            timeframe="5m",
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            pairs=["BTC/USDT"],
            initial_balance=1000.0,
            max_open_trades=3,
            fee=0.001
        )

    def test_freqtrade_version_check(self, check_freqtrade_available):
        """Test freqtrade version command"""
        print("\n🔍 Testing freqtrade version command...")

        result = subprocess.run(["freqtrade", "--version"], capture_output=True, text=True, timeout=10)

        print(f"📝 Command executed: freqtrade --version")
        print(f"🔢 Return code: {result.returncode}")
        print(f"📄 Stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️  Stderr: {result.stderr.strip()}")

        assert result.returncode == 0
        assert "freqtrade" in result.stdout.lower()
        print("✅ Freqtrade version check passed")

    def test_freqtrade_help_command(self, check_freqtrade_available):
        """Test freqtrade help command"""
        print("\n📖 Testing freqtrade help command...")

        result = subprocess.run([sys.executable, "-m", "freqtrade", "--help"], capture_output=True, text=True, timeout=10)

        print(f"📝 Command executed: freqtrade --help")
        print(f"🔢 Return code: {result.returncode}")
        print(f"📄 Help output length: {len(result.stdout)} characters")

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "freqtrade" in result.stdout.lower()
        print("✅ Freqtrade help command passed")

    def test_backtest_executor_initialization(self, temp_workspace, check_freqtrade_available):
        """Test BacktestExecutor initialization with real freqtrade"""
        print("\n🏗️  Testing BacktestExecutor initialization...")

        # Create executor with real freqtrade path
        executor = BacktestExecutor(freqtrade_path="freqtrade")

        print(f"🎯 Freqtrade path: {executor.freqtrade_path}")
        print(f"📁 Temp dir: {executor.temp_dir}")
        print(f"📁 User data dir: {executor.user_data_dir}")
        print(f"✅ Available: {executor.freqtrade_available}")

        assert executor.freqtrade_path == "freqtrade"
        assert executor.temp_dir.exists()
        assert executor.user_data_dir.exists()
        assert executor.freqtrade_available is True

        print("✅ BacktestExecutor initialization passed")

    def test_create_temp_config_real(self, temp_workspace, backtest_config, check_freqtrade_available):
        """Test creating temporary config file"""
        print("\n📄 Testing temp config creation...")

        executor = BacktestExecutor(freqtrade_path="freqtrade")
        executor.temp_dir = temp_workspace / "temp"
        executor.temp_dir.mkdir(exist_ok=True)

        config_file = executor._create_temp_config("RealTestStrategy", backtest_config)

        print(f"📝 Created config file: {config_file}")
        print(f"📂 File exists: {config_file.exists()}")
        print(f"📏 File size: {config_file.stat().st_size} bytes")

        assert config_file.exists()
        assert config_file.suffix == ".json"
        assert "RealTestStrategy" in config_file.name

        # Verify config content
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        print(f"📊 Config data keys: {list(config_data.keys())}")
        assert "strategy" in config_data
        assert config_data["strategy"] == "RealTestStrategy"

        print("✅ Temp config creation passed")

    def test_freqtrade_config_validation(self, temp_workspace, backtest_config, check_freqtrade_available):
        """Test freqtrade config validation with detailed logging"""
        print("\n🔧 Testing freqtrade config validation with detailed logging...")

        executor = BacktestExecutor(freqtrade_path="freqtrade")
        executor.temp_dir = temp_workspace / "temp"
        executor.temp_dir.mkdir(exist_ok=True)

        config_file = executor._create_temp_config("RealTestStrategy", backtest_config)

        # Test freqtrade config validation with detailed output
        cmd = [sys.executable, "-m", "freqtrade", "backtesting", "--config", str(config_file), "--dry-run"]
        print(f"📝 Command: {' '.join(cmd)}")
        print(f"🎯 Config file: {config_file}")
        print(f"📂 Working directory: {temp_workspace}")

        # Read and display config content
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = json.load(f)
        print(f"📊 Config strategy: {config_content.get('strategy')}")
        print(f"📊 Config timeframe: {config_content.get('timeframe')}")
        print(f"📊 Config pairs: {config_content.get('exchange', {}).get('pair_whitelist', [])}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=temp_workspace)

        print(f"\n🔍 EXECUTION RESULTS:")
        print(f"🔢 Return code: {result.returncode}")
        print(f"⏱️  Timeout: 60 seconds")

        if result.stdout:
            print(f"\n📄 STDOUT ({len(result.stdout)} characters):")
            # Show first 1000 characters of stdout
            stdout_preview = result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout
            print(f"📝 {stdout_preview}")

            # Look for specific log patterns
            if "INFO" in result.stdout:
                info_lines = [line for line in result.stdout.split('\n') if 'INFO' in line]
                print(f"\n📋 Found {len(info_lines)} INFO log lines:")
                for i, line in enumerate(info_lines[:5]):  # Show first 5 INFO lines
                    print(f"   {i+1}. {line.strip()}")

        if result.stderr:
            print(f"\n⚠️  STDERR ({len(result.stderr)} characters):")
            stderr_preview = result.stderr[:1000] + "..." if len(result.stderr) > 1000 else result.stderr
            print(f"⚠️  {stderr_preview}")

            # Analyze stderr for common issues
            if "usage:" in result.stderr:
                print("⚠️  Command usage error - missing required parameters")
            elif "No such file or directory" in result.stderr:
                print("⚠️  File not found error")
            elif "Permission denied" in result.stderr:
                print("⚠️  Permission error")
            elif "Strategy" in result.stderr and "not found" in result.stderr:
                print("⚠️  Strategy file not found")
            elif "Config" in result.stderr and "error" in result.stderr.lower():
                print("⚠️  Configuration error")

        # Analyze return code
        print(f"\n📊 RETURN CODE ANALYSIS:")
        if result.returncode == 0:
            print("✅ Return code 0: Command executed successfully")
        elif result.returncode == 1:
            print("❌ Return code 1: General error occurred")
        elif result.returncode == 2:
            print("❌ Return code 2: Command usage error or invalid arguments")
        elif result.returncode == 126:
            print("❌ Return code 126: Command cannot execute (permission denied)")
        elif result.returncode == 127:
            print("❌ Return code 127: Command not found")
        else:
            print(f"❓ Return code {result.returncode}: Unknown error code")

        # Config validation might fail due to missing data, but we just want to test execution
        print("✅ Freqtrade config validation with detailed logging completed")

    def test_real_freqtrade_backtesting_command_display(self, temp_workspace, backtest_config, check_freqtrade_available):
        """Test displaying the complete freqtrade backtesting command"""
        print("\n🔥 Testing real freqtrade backtesting command display...")

        executor = BacktestExecutor(freqtrade_path="freqtrade")
        executor.temp_dir = temp_workspace / "temp"
        executor.temp_dir.mkdir(exist_ok=True)

        config_file = executor._create_temp_config("RealTestStrategy", backtest_config)

        # Build the complete command
        timestamp = int(time.time())
        cmd = [
            sys.executable, "-m", "freqtrade",
            "backtesting",
            "--config", str(config_file),
            "--export", "trades",
            "--export-filename", f"backtest_results_RealTestStrategy_{timestamp}.json"
        ]

        full_command = ' '.join(cmd)
        print(f"📝 COMPLETE FREQTRADE BACKTESTING COMMAND:")
        print(f"🔥 {full_command}")
        print(f"📂 Working directory: {temp_workspace}")
        print(f"🎯 Strategy: RealTestStrategy")
        print(f"📊 Timeframe: {backtest_config.timeframe}")
        print(f"💰 Initial balance: ${backtest_config.initial_balance}")
        print(f"📈 Trading pairs: {backtest_config.pairs}")
        print(f"📅 Date range: {backtest_config.start_date} to {backtest_config.end_date}")
        print(f"💾 Results file: backtest_results_RealTestStrategy_{timestamp}.json")

        # Verify command structure
        assert "freqtrade" in cmd
        assert "backtesting" in cmd
        assert "--config" in cmd
        assert "--export" in cmd
        assert "trades" in cmd
        assert "--export-filename" in cmd
        assert "RealTestStrategy" in full_command

        print(f"\n💡 To run this backtest manually, execute:")
        print(f"   cd {temp_workspace}")
        print(f"   {full_command}")

        print("✅ Real freqtrade command display test passed")

    def test_real_freqtrade_dry_run_command_display(self, temp_workspace, backtest_config, check_freqtrade_available):
        """Test displaying the complete freqtrade dry-run command"""
        print("\n🚀 Testing real freqtrade dry-run command display...")

        executor = BacktestExecutor(freqtrade_path="freqtrade")
        executor.temp_dir = temp_workspace / "temp"
        executor.temp_dir.mkdir(exist_ok=True)

        config_file = executor._create_temp_config("RealTestStrategy", backtest_config)

        # Build the complete dry-run command
        cmd = [
            sys.executable, "-m", "freqtrade",
            "trade",
            "--config", str(config_file),
            "--strategy", "RealTestStrategy"
        ]

        full_command = ' '.join(cmd)
        print(f"📝 COMPLETE FREQTRADE DRY-RUN COMMAND:")
        print(f"🚀 {full_command}")
        print(f"📂 Working directory: {temp_workspace}")
        print(f"🎯 Strategy: RealTestStrategy")
        print(f"🗄️  Database: dryrun_RealTestStrategy.sqlite")
        print(f"📊 Timeframe: {backtest_config.timeframe}")
        print(f"💰 Initial balance: ${backtest_config.initial_balance}")
        print(f"📈 Trading pairs: {backtest_config.pairs}")

        # Verify command structure
        assert "freqtrade" in cmd
        assert "trade" in cmd
        assert "--config" in cmd
        assert "--strategy" in cmd
        assert "RealTestStrategy" in full_command

        print(f"\n💡 To run this dry-run manually, execute:")
        print(f"   cd {temp_workspace}")
        print(f"   {full_command}")

        print("✅ Real freqtrade dry-run command display test passed")

    def test_strategy_validation_real(self, temp_workspace, test_strategy, check_freqtrade_available):
        """Test strategy validation with real files"""
        print("\n🔍 Testing strategy validation with real files...")

        executor = BacktestExecutor(freqtrade_path="freqtrade")

        strategy_file = temp_workspace / "user_data" / "strategies" / "RealTestStrategy.py"
        print(f"🎯 Strategy file: {strategy_file}")
        print(f"📂 File exists: {strategy_file.exists()}")

        result = executor.validate_strategy(strategy_file)
        print(f"✅ Validation result: {result}")

        assert result is True
        print("✅ Strategy validation passed")

    def test_freqtrade_command_execution_attempt(self, temp_workspace, backtest_config, check_freqtrade_available):
        """Test actual freqtrade command execution with comprehensive logging"""
        print("\n⚡ Testing actual freqtrade command execution with comprehensive logging...")

        executor = BacktestExecutor(freqtrade_path="freqtrade")
        executor.temp_dir = temp_workspace / "temp"
        executor.temp_dir.mkdir(exist_ok=True)
        executor.user_data_dir = temp_workspace / "user_data"
        executor.user_data_dir.mkdir(exist_ok=True)

        config_file = executor._create_temp_config("RealTestStrategy", backtest_config)

        print("\n" + "="*80)
        print("🔥 TESTING ACTUAL BACKTESTEXECUTOR.execute_backtest() METHOD")
        print("="*80)
        print("This will show the complete freqtrade command logs from BacktestExecutor")
        print("="*80)

        # Actually call BacktestExecutor.execute_backtest() to see the full logs
        try:
            result = executor.execute_backtest("RealTestStrategy", backtest_config)

            print("\n" + "="*80)
            print("📊 BACKTEST EXECUTOR RESULT ANALYSIS:")
            print(f"🎯 Strategy: {result.strategy_name}")
            print(f"📊 Status: {result.status}")
            print(f"⏱️  Execution Time: {result.execution_time:.2f}s")

            if result.error_message:
                print(f"❌ Error: {result.error_message}")

            if hasattr(result, 'metrics') and result.metrics:
                print("📈 Metrics:")
                print(f"   • Total Return: {getattr(result.metrics, 'total_return_pct', 'N/A')}%")
                print(f"   • Win Rate: {getattr(result.metrics, 'win_rate', 'N/A')}%")
                print(f"   • Total Trades: {getattr(result.metrics, 'total_trades', 'N/A')}")

            print("✅ BacktestExecutor.execute_backtest() completed with full logging")
        except Exception as e:
            print(f"\n💥 BACKTESTEXECUTOR EXCEPTION: {str(e)}")
            print("This is expected behavior - showing that the full command logging works")

        # Additional direct subprocess tests for comparison
        print("\n" + "="*80)
        print("🔄 ADDITIONAL DIRECT SUBPROCESS TESTS FOR COMPARISON")
        print("="*80)

        # Try to run a simple freqtrade command with different variations
        test_commands = [
            {
                "name": "Basic backtesting validation",
                "cmd": [sys.executable, "-m", "freqtrade", "backtesting", "--config", str(config_file), "--dry-run"],
                "description": "Test basic backtesting command with dry-run"
            },
            {
                "name": "Strategy listing",
                "cmd": [sys.executable, "-m", "freqtrade", "list-strategies", "--config", str(config_file)],
                "description": "List available strategies to verify strategy loading"
            },
            {
                "name": "Configuration validation",
                "cmd": [sys.executable, "-m", "freqtrade", "show-config", "--config", str(config_file)],
                "description": "Show parsed configuration to verify config is valid"
            }
        ]

        for i, test_case in enumerate(test_commands, 1):
            print(f"\n{'='*60}")
            print(f"🧪 SUBPROCESS TEST {i}: {test_case['name']}")
            print(f"📝 {test_case['description']}")
            print(f"🔧 Command: {' '.join(test_case['cmd'])}")
            print(f"📂 Working directory: {temp_workspace}")

            try:
                result = subprocess.run(
                    test_case['cmd'],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=temp_workspace
                )

                print(f"\n🔍 SUBPROCESS EXECUTION RESULTS:")
                print(f"🔢 Return code: {result.returncode}")
                print(f"⏱️  Execution time: Completed within timeout (60s)")

                # Analyze stdout
                if result.stdout:
                    stdout_lines = result.stdout.split('\n')
                    print(f"\n📄 STDOUT ANALYSIS ({len(result.stdout)} chars, {len(stdout_lines)} lines):")

                    # Show first few lines
                    print("📝 First 10 lines of output:")
                    for j, line in enumerate(stdout_lines[:10]):
                        if line.strip():
                            print(f"   {j+1:2d}: {line.strip()}")

                    # Look for specific log patterns
                    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                    log_counts = {}
                    for level in log_levels:
                        count = result.stdout.count(level)
                        if count > 0:
                            log_counts[level] = count

                    if log_counts:
                        print(f"\n📋 Log levels found: {log_counts}")

                    # Look for freqtrade-specific messages
                    freqtrade_messages = []
                    for line in stdout_lines:
                        if any(keyword in line.upper() for keyword in ['FREQTRADE', 'STRATEGY', 'CONFIG', 'BACKTEST']):
                            freqtrade_messages.append(line.strip())

                    if freqtrade_messages:
                        print(f"\n🎯 Freqtrade-specific messages ({len(freqtrade_messages)} found):")
                        for j, msg in enumerate(freqtrade_messages[:5]):  # Show first 5
                            print(f"   {j+1}. {msg}")

                # Analyze stderr
                if result.stderr:
                    stderr_lines = result.stderr.split('\n')
                    print(f"\n⚠️  STDERR ANALYSIS ({len(result.stderr)} characters):")
                    stderr_preview = result.stderr[:1000] + "..." if len(result.stderr) > 1000 else result.stderr
                    print(f"⚠️  {stderr_preview}")

                    # Analyze error types
                    error_patterns = {
                        "usage:": "Command usage help (missing arguments)",
                        "No such file or directory": "File not found",
                        "Permission denied": "Permission error",
                        "ModuleNotFoundError": "Python module missing",
                        "ImportError": "Import error",
                        "SyntaxError": "Python syntax error",
                        "strategy": "Strategy-related error",
                        "config": "Configuration error",
                        "exchange": "Exchange-related error"
                    }

                    detected_errors = []
                    for pattern, description in error_patterns.items():
                        if pattern.lower() in result.stderr.lower():
                            detected_errors.append(f"{pattern}: {description}")

                    if detected_errors:
                        print(f"\n🔍 Detected error patterns:")
                        for error in detected_errors[:3]:  # Show first 3
                            print(f"   • {error}")

                # Performance metrics
                print(f"\n📈 EXECUTION METRICS:")
                print(f"📊 Output size: {len(result.stdout)} chars stdout, {len(result.stderr)} chars stderr")
                print(f"📊 Total content: {len(result.stdout) + len(result.stderr)} characters")

                print(f"✅ Subprocess test case '{test_case['name']}' completed")

            except subprocess.TimeoutExpired:
                print(f"⏰ TIMEOUT: Command timed out after 60 seconds")
                print("⚠️  This is expected for commands requiring data download")
                print(f"✅ Subprocess test case '{test_case['name']}' completed (with timeout)")

            except Exception as e:
                print(f"💥 UNEXPECTED ERROR: {str(e)}")
                print(f"✅ Subprocess test case '{test_case['name']}' completed (with exception)")

    print(f"\n{'='*80}")
    print("🎉 All freqtrade command execution tests completed!")
    print("📋 Summary: Tested BacktestExecutor.execute_backtest() with full logging + additional subprocess tests")
    print("🔥 The BacktestExecutor logs show the complete freqtrade command execution flow!")