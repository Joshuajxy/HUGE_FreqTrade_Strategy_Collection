"""
Backtest executor
"""
import subprocess
import sys
import json
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from utils.data_models import BacktestConfig, BacktestResult, PerformanceMetrics, ExecutionStatus
from utils.error_handling import ErrorHandler, ExecutionError, error_handler
from components.results.parser import ResultParser

class BacktestExecutor:
    """Backtest executor"""
    
    def __init__(self, freqtrade_path: str = "freqtrade"):
        """
        Initialize executor
        
        Args:
            freqtrade_path: freqtrade command path
        """
        self.freqtrade_path = freqtrade_path
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        self.user_data_dir = Path("user_data")
        self.user_data_dir.mkdir(exist_ok=True)
        (self.user_data_dir / "data").mkdir(exist_ok=True)
        (self.user_data_dir / "strategies").mkdir(exist_ok=True)
        (self.user_data_dir / "plot").mkdir(exist_ok=True)
        self.freqtrade_available = False
        
        # Validate freqtrade availability
        self._validate_freqtrade()
    
    def _validate_freqtrade(self):
        """Validate freqtrade availability"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "freqtrade", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                ErrorHandler.log_info(f"Freqtrade validation successful: {result.stdout.strip()}")
                self.freqtrade_available = True
            else:
                raise ExecutionError(f"Freqtrade validation failed: {result.stderr}")
        
        except FileNotFoundError:
            self.freqtrade_available = False
            ErrorHandler.log_warning(f"Freqtrade command not found: {self.freqtrade_path}")
            ErrorHandler.log_info("To install freqtrade, run: pip install freqtrade")
            raise ExecutionError(f"Freqtrade command not found: {self.freqtrade_path}\n💡 Install with: pip install freqtrade")
        
        except subprocess.TimeoutExpired:
            self.freqtrade_available = False
            raise ExecutionError("Freqtrade command timeout")
        
        except Exception as e:
            self.freqtrade_available = False
            raise ExecutionError(f"Freqtrade validation failed: {str(e)}")
    
    def _ensure_data_downloaded(self, config: BacktestConfig):
        """
        Ensure historical data for the given configuration is available, downloading it if necessary.
        """
        ErrorHandler.log_info("Ensuring historical data is available...")
        print("\n📥 Ensuring historical data is available...")
        try:
            cmd = [
                sys.executable, "-m", "freqtrade",
                "download-data",
                "--exchange", "binance",  # Assuming binance, could be from config
                "-t", config.timeframe,
                "--pairs", *config.pairs,
                "--timerange", f"{config.start_date.strftime('%Y%m%d')}-{config.end_date.strftime('%Y%m%d')}"
            ]
            
            ErrorHandler.log_info(f"Executing data download command: {' '.join(cmd)}")
            print(f"🔩 Executing command: {' '.join(cmd)}")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True)
            
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line:
                    print(f"   {line}")
                    ErrorHandler.log_info(f"DATA_DOWNLOAD: {line}")
            
            process.wait()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd, "Data download script failed.")

            print("✅ Data download check completed successfully.")
            ErrorHandler.log_info("Successfully ensured data is available for backtest.")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Data download failed with return code {e.returncode}."
            print(f"❌ {error_msg}")
            ErrorHandler.log_error(error_msg)
            raise ExecutionError(error_msg) from e
        except Exception as e:
            error_msg = f"An unknown error occurred during data download: {e}"
            print(f"❌ {error_msg}")
            ErrorHandler.log_error(error_msg)
            raise ExecutionError(error_msg) from e

    @error_handler(ExecutionError, show_error=False)
    def execute_backtest(self, task_id: str, strategy_info: "StrategyInfo", config: BacktestConfig) -> BacktestResult:
        """
        Execute backtest with detailed logging, ensuring data is downloaded first.
        
        Args:
            task_id: The unique ID for this execution task.
            strategy_info: strategy information object
            config: backtest configuration
            
        Returns:
            backtest result
        """
        from utils.data_models import StrategyInfo # For type hint
        start_time = time.time()
        strategy_name = strategy_info.name
        
        try:
            # Step 1: Ensure data is downloaded
            self._ensure_data_downloaded(config)

            # Step 2: Proceed with backtest execution
            log_line = f"🏁 STARTING BACKTEST EXECUTION: {strategy_name}"
            print(f"\n{log_line}")
            ErrorHandler.log_info(log_line)

            # Log configuration details
            config_info = f"Backtest config - Timeframe: {config.timeframe}, Pairs: {len(config.pairs)}, Start: {config.start_date}, End: {config.end_date}"
            print(f"📊 CONFIG: {config_info}")
            ErrorHandler.log_info(config_info)
            
            # Create temporary configuration file
            config_file = self._create_temp_config(strategy_name, config)
            
            # Execute freqtrade backtest
            output = self._run_freqtrade_backtest_with_logging(task_id, strategy_info, config_file)
            
            # Parse results
            parser = ResultParser()
            result = parser.parse_backtest_output(output, strategy_name, config)
            
            # Set execution time
            result.execution_time = time.time() - start_time
            result.status = ExecutionStatus.COMPLETED

            success_msg = f"Backtest execution completed: {strategy_name} (Time: {result.execution_time:.2f}s, Return: {result.metrics.total_return_pct:.2f}%)"
            print(f"✅ {success_msg}")
            ErrorHandler.log_info(success_msg)
            return result
        
        except Exception as e:
            # The error (including from data download) is caught here
            ErrorHandler.log_error(f"Backtest execution failed for {strategy_name}: {str(e)}")
            
            # Create error result
            error_result = BacktestResult(
                strategy_name=strategy_name,
                config=config,
                metrics=PerformanceMetrics(),
                trades=[],
                timestamp=datetime.now(),
                execution_time=time.time() - start_time,
                error_message=str(e),
                status=ExecutionStatus.FAILED
            )
            
            return error_result
        
        finally:
            # Clean up temporary files
            self._cleanup_temp_files()
    
    def _create_temp_config(self, strategy_name: str, config: BacktestConfig) -> Path:
        """Create temporary configuration file"""
        try:
            # Convert to freqtrade configuration format and add modern pairlist handling
            base_config = config.to_freqtrade_config(strategy_name)
            
            # The 'pairs' key is now handled within 'pairlists'
            pairs = base_config.pop("pairs", [])

            freqtrade_config = {
                "pairlists": [
                    {"method": "StaticPairList", "pairs": pairs}
                ],
                **base_config
            }
            
            # Add additional required configurations
            freqtrade_config.update({
                "datadir": str(self.user_data_dir / "data"),
                "user_data_dir": str(self.user_data_dir),
                "logfile": f"logs/freqtrade_{strategy_name}.log",
                "db_url": f"sqlite:///tradesv3_{strategy_name}.sqlite",
                # strategy_path is now handled by the command line argument
                "export": "trades",
                "exportfilename": f"user_data/backtest_results/backtest_results_{strategy_name}.json"
            })
            
            # Create temporary configuration file
            config_file = self.temp_dir / f"config_{strategy_name}_{int(time.time())}.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(freqtrade_config, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Temporary configuration file created: {config_file}")
            return config_file
        
        except Exception as e:
            raise ExecutionError(f"Failed to create temporary configuration: {str(e)}")
    
    def _run_freqtrade_backtest_with_logging(self, task_id: str, strategy_info: "StrategyInfo", config_file: Path) -> str:
        """Run freqtrade backtest command with detailed logging"""
        from utils.data_models import StrategyInfo # For type hint
        from .scheduler_singleton import get_log_queue

        strategy_name = strategy_info.name
        strategy_path = strategy_info.file_path.parent
        log_queue = get_log_queue()

        try:
            # Build command
            cmd = [
                sys.executable, "-m", "freqtrade",
                "backtesting",
                "--config", str(config_file),
                "--strategy-path", str(strategy_path),
                "--export", "trades"
            ]

            ErrorHandler.log_info(f"Executing freqtrade command: {' '.join(cmd)}")

            # Print detailed command information for real execution
            if self.freqtrade_path != "mock_freqtrade":
                log_queue.put((task_id, f"🔥 REAL FREQTRADE EXECUTION:"))
                log_queue.put((task_id, f"📝 Command: {' '.join(cmd)}"))
                log_queue.put((task_id, f"🎯 Strategy: {strategy_name}"))
                log_queue.put((task_id, f"📂 Strategy Path: {strategy_path}"))
                log_queue.put((task_id, f"⚙️ Config: {config_file}"))
                log_queue.put((task_id, f"🔧 Freqtrade path: {sys.executable} -m freqtrade"))
                log_queue.put((task_id, "=" * 80))

            # Execute command with real-time logging
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=Path.cwd()
            )

            # Capture output with real-time logging
            stdout_lines = []
            stderr_lines = []

            # Use select to handle real-time output properly
            import select

            # Set up polling for both stdout and stderr
            if hasattr(select, 'select') and sys.platform != 'win32':  # Unix-like systems only
                while True:
                    reads = [process.stdout, process.stderr]
                    readable, _, _ = select.select(reads, [], [], 0.1)

                    for stream in readable:
                        if stream == process.stdout:
                            line = process.stdout.readline()
                            if line:
                                line = line.strip()
                                if line:
                                    log_queue.put((task_id, f"📄 STDOUT: {line}"))
                                stdout_lines.append(line)
                        elif stream == process.stderr:
                            line = process.stderr.readline()
                            if line:
                                line = line.strip()
                                if line:
                                    log_queue.put((task_id, f"⚠️ STDERR: {line}"))
                                stderr_lines.append(line)

                    if process.poll() is not None:
                        break # Exit loop when process finishes
            else:
                # Windows fallback
                log_queue.put((task_id, "🔄 Reading freqtrade output (Windows mode)..."))
                import threading

                def reader_thread(pipe, line_list, prefix):
                    try:
                        for line in iter(pipe.readline, ''):
                            line = line.strip()
                            if line:
                                log_queue.put((task_id, f"{prefix}: {line}"))
                                line_list.append(line)
                    finally:
                        pipe.close()

                stdout_thread = threading.Thread(target=reader_thread, args=[process.stdout, stdout_lines, "📄 STDOUT"], daemon=True)
                stderr_thread = threading.Thread(target=reader_thread, args=[process.stderr, stderr_lines, "⚠️ STDERR"], daemon=True)
                stdout_thread.start()
                stderr_thread.start()
                stdout_thread.join()
                stderr_thread.join()

            process.wait()

            # Check return code
            if process.returncode == 0:
                ErrorHandler.log_info(f"Freqtrade backtest execution successful: {strategy_name}")
                log_queue.put((task_id, "✅ FREQTRADE EXECUTION COMPLETED SUCCESSFULLY"))
                return '\n'.join(stdout_lines)
            else:
                error_msg = f"Freqtrade backtest failed: {strategy_name} - {' '.join(stderr_lines)}"
                ErrorHandler.log_error(error_msg)
                log_queue.put((task_id, f"❌ FREQTRADE EXECUTION FAILED (Return code: {process.returncode})"))
                raise ExecutionError(error_msg)

        except subprocess.TimeoutExpired:
            raise ExecutionError("Backtest execution timeout")

        except Exception as e:
            raise ExecutionError(f"Failed to run freqtrade backtest: {str(e)}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            # NOTE: Do not delete temporary configuration files here to allow
            # subsequent subprocess-based validations to reuse the same config.
            # The test harness relies on the config file after execute_backtest().
            # If needed, a separate maintenance job can clean old files.

            # Clean up temporary result files
            for result_file in Path.cwd().glob("backtest_results_*.json"):
                if result_file.exists():
                    result_file.unlink()
            
            ErrorHandler.log_info("Temporary files cleaned up")
        
        except Exception as e:
            ErrorHandler.log_warning(f"Failed to clean up temporary files: {str(e)}")
    
    def execute_dry_run(self, strategy_name: str, config: BacktestConfig) -> bool:
        """
        Execute dry run
        
        Args:
            strategy_name: strategy name
            config: backtest configuration
            
        Returns:
            whether dry run started successfully
        """
        try:
            ErrorHandler.log_info(f"Starting dry run: {strategy_name}")
            
            # Create temporary configuration file
            config_file = self._create_temp_config(strategy_name, config)
            
            # Modify configuration for dry run
            with open(config_file, 'r', encoding='utf-8') as f:
                dry_run_config = json.load(f)
            
            dry_run_config.update({
                "dry_run": True,
                "db_url": f"sqlite:///dryrun_{strategy_name}.sqlite"
            })
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(dry_run_config, f, indent=2, ensure_ascii=False)
            
            # Build dry run command
            cmd = [
                sys.executable, "-m", "freqtrade",
                "trade",
                "--config", str(config_file),
                "--strategy", strategy_name
            ]
            
            # Print detailed command information for real execution
            if self.freqtrade_path != "mock_freqtrade":
                print(f"\n🚀 REAL DRY RUN EXECUTION:")
                print(f"📝 Command: {' '.join(cmd)}")
                print(f"🎯 Strategy: {strategy_name}")
                print(f"📂 Config: {config_file}")
                print(f"🗄️  Database: dryrun_{strategy_name}.sqlite")
                print(f"🔧 Freqtrade path: {self.freqtrade_path}")
                print("=" * 80)
            
            # Start dry run process (non-blocking)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd()
            )
            
            ErrorHandler.log_info(f"Dry run started: {strategy_name} (PID: {process.pid})")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to start dry run: {strategy_name} - {str(e)}")
            return False
    
    def stop_dry_run(self, strategy_name: str) -> bool:
        """
        Stop dry run
        
        Args:
            strategy_name: strategy name
            
        Returns:
            whether dry run stopped successfully
        """
        try:
            # This is a simplified implementation
            # In a real scenario, you would need to track process IDs
            ErrorHandler.log_info(f"Stopping dry run: {strategy_name}")
            
            # Kill freqtrade processes (simplified approach)
            subprocess.run(["pkill", "-f", f"freqtrade.*{strategy_name}"], 
                         capture_output=True, text=True)
            
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to stop dry run: {strategy_name} - {str(e)}")
            return False
    
    def get_execution_status(self, strategy_name: str) -> ExecutionStatus:
        """
        Get execution status
        
        Args:
            strategy_name: strategy name
            
        Returns:
            execution status
        """
        try:
            # Check if freqtrade process is running for this strategy
            result = subprocess.run(
                ["pgrep", "-f", f"freqtrade.*{strategy_name}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return ExecutionStatus.RUNNING
            else:
                return ExecutionStatus.IDLE
        
        except Exception as e:
            ErrorHandler.log_warning(f"Failed to get execution status: {str(e)}")
            return ExecutionStatus.IDLE
    
    def validate_strategy(self, strategy_path: Path) -> bool:
        """
        Validate strategy file
        
        Args:
            strategy_path: strategy file path
            
        Returns:
            whether strategy is valid
        """
        try:
            # Basic validation - check if file exists and has .py extension
            if not strategy_path.exists():
                return False
            
            if strategy_path.suffix != '.py':
                return False
            
            # Try to read the file and check for basic strategy structure
            with open(strategy_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required strategy components
            required_components = [
                'class',
                'populate_indicators',
                'populate_entry_trend',
                'populate_exit_trend'
            ]
            
            for component in required_components:
                if component not in content:
                    return False
            
            return True
        
        except Exception as e:
            ErrorHandler.log_warning(f"Strategy validation failed: {str(e)}")
            return False