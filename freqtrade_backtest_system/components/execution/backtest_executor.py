"""
Backtest executor
"""
import subprocess
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
        
        # Validate freqtrade availability
        self._validate_freqtrade()
    
    def _validate_freqtrade(self):
        """Validate freqtrade availability"""
        try:
            result = subprocess.run(
                [self.freqtrade_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                ErrorHandler.log_info(f"Freqtrade validation successful: {result.stdout.strip()}")
            else:
                raise ExecutionError(f"Freqtrade validation failed: {result.stderr}")
        
        except FileNotFoundError:
            raise ExecutionError(f"Freqtrade command not found: {self.freqtrade_path}")
        
        except subprocess.TimeoutExpired:
            raise ExecutionError("Freqtrade command timeout")
        
        except Exception as e:
            raise ExecutionError(f"Freqtrade validation failed: {str(e)}")
    
    @error_handler(ExecutionError, show_error=False)
    def execute_backtest(self, strategy_name: str, config: BacktestConfig) -> BacktestResult:
        """
        Execute backtest
        
        Args:
            strategy_name: strategy name
            config: backtest configuration
            
        Returns:
            backtest result
        """
        start_time = time.time()
        
        try:
            ErrorHandler.log_info(f"Starting backtest execution: {strategy_name}")
            
            # Create temporary configuration file
            config_file = self._create_temp_config(strategy_name, config)
            
            # Execute freqtrade backtest
            output = self._run_freqtrade_backtest(config_file)
            
            # Parse results
            parser = ResultParser()
            result = parser.parse_backtest_output(output, strategy_name, config)
            
            # Set execution time
            result.execution_time = time.time() - start_time
            result.status = ExecutionStatus.COMPLETED
            
            ErrorHandler.log_info(f"Backtest execution completed: {strategy_name}")
            return result
        
        except Exception as e:
            ErrorHandler.log_error(f"Backtest execution failed: {strategy_name} - {str(e)}")
            
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
            # Convert to freqtrade configuration format
            freqtrade_config = config.to_freqtrade_config(strategy_name)
            
            # Add additional required configurations
            freqtrade_config.update({
                "datadir": "user_data/data",
                "user_data_dir": "user_data",
                "logfile": f"logs/freqtrade_{strategy_name}.log",
                "db_url": f"sqlite:///tradesv3_{strategy_name}.sqlite",
                "strategy_path": ["user_data/strategies"],
                "export": "trades",
                "exportfilename": f"backtest_results_{strategy_name}.json"
            })
            
            # Create temporary configuration file
            config_file = self.temp_dir / f"config_{strategy_name}_{int(time.time())}.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(freqtrade_config, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Temporary configuration file created: {config_file}")
            return config_file
        
        except Exception as e:
            raise ExecutionError(f"Failed to create temporary configuration: {str(e)}")
    
    def _run_freqtrade_backtest(self, config_file: Path) -> str:
        """Run freqtrade backtest command"""
        try:
            # Build command
            cmd = [
                self.freqtrade_path,
                "backtesting",
                "--config", str(config_file),
                "--strategy-list", "all",
                "--timerange", "20230101-20231231",  # This will be overridden by config
                "--export", "trades",
                "--export-filename", f"backtest_results_{int(time.time())}.json"
            ]
            
            ErrorHandler.log_info(f"Executing command: {' '.join(cmd)}")
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                ErrorHandler.log_info("Freqtrade backtest execution successful")
                return result.stdout
            else:
                error_msg = f"Freqtrade backtest failed: {result.stderr}"
                ErrorHandler.log_error(error_msg)
                raise ExecutionError(error_msg)
        
        except subprocess.TimeoutExpired:
            raise ExecutionError("Backtest execution timeout")
        
        except Exception as e:
            raise ExecutionError(f"Failed to run freqtrade backtest: {str(e)}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            # Clean up temporary configuration files
            for temp_file in self.temp_dir.glob("config_*.json"):
                if temp_file.exists():
                    temp_file.unlink()
            
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
                self.freqtrade_path,
                "trade",
                "--config", str(config_file),
                "--strategy", strategy_name
            ]
            
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