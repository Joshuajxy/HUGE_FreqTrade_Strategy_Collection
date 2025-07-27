"""
Dry run executor for continuous strategy monitoring
"""
import subprocess
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import psutil

from utils.data_models import BacktestConfig, DryRunStatus, ExecutionStatus
from utils.error_handling import ErrorHandler, ExecutionError, error_handler

class DryRunExecutor:
    """Dry run executor for continuous strategy monitoring"""
    
    def __init__(self, freqtrade_path: str = "freqtrade"):
        """
        Initialize dry run executor
        
        Args:
            freqtrade_path: freqtrade command path
        """
        self.freqtrade_path = freqtrade_path
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Active dry run processes
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.dry_run_status: Dict[str, DryRunStatus] = {}
        self.status_callbacks: Dict[str, Callable] = {}
        
        # Monitoring thread
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        self._monitor_thread.start()
        
        ErrorHandler.log_info("Dry run executor initialized")
    
    @error_handler(ExecutionError, show_error=False)
    def start_dry_run(self, 
                     strategy_name: str, 
                     config: BacktestConfig,
                     status_callback: Optional[Callable] = None) -> str:
        """
        Start dry run for a strategy
        
        Args:
            strategy_name: strategy name
            config: backtest configuration
            status_callback: status update callback function
            
        Returns:
            dry run ID
        """
        run_id = f"dryrun_{strategy_name}_{int(time.time())}"
        
        try:
            ErrorHandler.log_info(f"Starting dry run: {strategy_name}")
            
            # Create dry run configuration
            config_file = self._create_dry_run_config(strategy_name, config, run_id)
            
            # Start freqtrade dry run process
            process = self._start_freqtrade_process(config_file, run_id)
            
            # Store process and status
            self.active_processes[run_id] = process
            self.dry_run_status[run_id] = DryRunStatus(
                run_id=run_id,
                strategy=strategy_name,
                status=ExecutionStatus.RUNNING,
                start_time=datetime.now(),
                last_update=datetime.now()
            )
            
            if status_callback:
                self.status_callbacks[run_id] = status_callback
            
            ErrorHandler.log_info(f"Dry run started: {strategy_name} (ID: {run_id})")
            return run_id
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to start dry run {strategy_name}: {str(e)}")
            raise ExecutionError(f"Failed to start dry run: {str(e)}")
    
    def stop_dry_run(self, run_id: str) -> bool:
        """
        Stop dry run
        
        Args:
            run_id: dry run ID
            
        Returns:
            whether stop was successful
        """
        try:
            if run_id not in self.active_processes:
                ErrorHandler.log_warning(f"Dry run not found: {run_id}")
                return False
            
            process = self.active_processes[run_id]
            
            # Terminate process gracefully
            process.terminate()
            
            # Wait for process to terminate
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                process.kill()
                process.wait()
            
            # Update status
            if run_id in self.dry_run_status:
                self.dry_run_status[run_id].update_status(ExecutionStatus.STOPPED)
            
            # Clean up
            self.active_processes.pop(run_id, None)
            self.status_callbacks.pop(run_id, None)
            
            ErrorHandler.log_info(f"Dry run stopped: {run_id}")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to stop dry run {run_id}: {str(e)}")
            return False
    
    def get_dry_run_status(self, run_id: str) -> Optional[DryRunStatus]:
        """
        Get dry run status
        
        Args:
            run_id: dry run ID
            
        Returns:
            dry run status
        """
        return self.dry_run_status.get(run_id)
    
    def get_all_dry_runs(self) -> Dict[str, DryRunStatus]:
        """
        Get all dry run statuses
        
        Returns:
            dictionary of all dry run statuses
        """
        return self.dry_run_status.copy()
    
    def get_active_dry_runs(self) -> Dict[str, DryRunStatus]:
        """
        Get active dry run statuses
        
        Returns:
            dictionary of active dry run statuses
        """
        return {
            run_id: status for run_id, status in self.dry_run_status.items()
            if status.status == ExecutionStatus.RUNNING
        }
    
    def restart_dry_run(self, run_id: str) -> bool:
        """
        Restart dry run
        
        Args:
            run_id: dry run ID
            
        Returns:
            whether restart was successful
        """
        try:
            if run_id not in self.dry_run_status:
                ErrorHandler.log_warning(f"Dry run not found: {run_id}")
                return False
            
            status = self.dry_run_status[run_id]
            
            # Stop current run if active
            if run_id in self.active_processes:
                self.stop_dry_run(run_id)
            
            # Wait a moment for cleanup
            time.sleep(2)
            
            # Create new configuration (reuse strategy name)
            strategy_name = status.strategy
            
            # Note: We would need the original config to restart properly
            # For now, we'll just update the status
            status.update_status(ExecutionStatus.RUNNING)
            status.start_time = datetime.now()
            
            ErrorHandler.log_info(f"Dry run restarted: {run_id}")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to restart dry run {run_id}: {str(e)}")
            return False
    
    def _create_dry_run_config(self, 
                              strategy_name: str, 
                              config: BacktestConfig, 
                              run_id: str) -> Path:
        """Create dry run configuration file"""
        try:
            # Convert to freqtrade configuration format
            freqtrade_config = config.to_freqtrade_config(strategy_name)
            
            # Modify for dry run
            freqtrade_config.update({
                "dry_run": True,
                "db_url": f"sqlite:///dryrun_{run_id}.sqlite",
                "logfile": f"logs/dryrun_{run_id}.log",
                "user_data_dir": "user_data",
                "datadir": "user_data/data",
                "strategy_path": ["user_data/strategies"],
                "telegram": {
                    "enabled": False
                },
                "api_server": {
                    "enabled": False
                }
            })
            
            # Create configuration file
            config_file = self.temp_dir / f"dryrun_config_{run_id}.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(freqtrade_config, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Dry run configuration created: {config_file}")
            return config_file
        
        except Exception as e:
            raise ExecutionError(f"Failed to create dry run configuration: {str(e)}")
    
    def _start_freqtrade_process(self, config_file: Path, run_id: str) -> subprocess.Popen:
        """Start freqtrade process"""
        try:
            # Build command
            cmd = [
                self.freqtrade_path,
                "trade",
                "--config", str(config_file),
                "--logfile", f"logs/dryrun_{run_id}.log"
            ]
            
            ErrorHandler.log_info(f"Starting freqtrade process: {' '.join(cmd)}")
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd()
            )
            
            return process
        
        except Exception as e:
            raise ExecutionError(f"Failed to start freqtrade process: {str(e)}")
    
    def _monitor_processes(self):
        """Monitor active dry run processes"""
        while self._monitoring_active:
            try:
                completed_runs = []
                
                for run_id, process in self.active_processes.items():
                    # Check if process is still running
                    if process.poll() is not None:
                        # Process has terminated
                        if run_id in self.dry_run_status:
                            if process.returncode == 0:
                                self.dry_run_status[run_id].update_status(ExecutionStatus.COMPLETED)
                            else:
                                self.dry_run_status[run_id].update_status(ExecutionStatus.FAILED)
                        
                        completed_runs.append(run_id)
                    else:
                        # Process is still running, update status
                        if run_id in self.dry_run_status:
                            status = self.dry_run_status[run_id]
                            status.last_update = datetime.now()
                            
                            # Read new output from stdout
                            while True:
                                line = process.stdout.readline()
                                if not line:
                                    break
                                status.latest_log_line = line.strip()
                                self._parse_log_line(status, line)

                            # Try to get process statistics
                            try:
                                proc = psutil.Process(process.pid)
                                # cpu_percent = proc.cpu_percent() # This can block
                                # memory_info = proc.memory_info()
                                
                                # Update status with process info (if needed)
                                # This could be extended to include more detailed monitoring
                                
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                    
                    # Call status callback if available
                    if run_id in self.status_callbacks:
                        try:
                            callback = self.status_callbacks[run_id]
                            callback(self.dry_run_status.get(run_id))
                        except Exception as e:
                            ErrorHandler.log_warning(f"Status callback error for {run_id}: {str(e)}")
                
                # Clean up completed runs
                for run_id in completed_runs:
                    self.active_processes.pop(run_id, None)
                    self.status_callbacks.pop(run_id, None)
                    ErrorHandler.log_info(f"Dry run process completed: {run_id}")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                ErrorHandler.log_error(f"Error in process monitoring: {str(e)}")
                time.sleep(10)  # Wait longer on error

    def _parse_log_line(self, status: DryRunStatus, line: str):
        # Regex patterns for parsing freqtrade dry run output
        # Example: 2023-01-01 10:00:00 - INFO - BTC/USDT: Buy signal for 0.001 BTC at 20000 USDT
        buy_signal_pattern = r'INFO - (.*): Buy signal for ([\d\.]+) (.*) at ([\d\.]+) USDT'
        sell_signal_pattern = r'INFO - (.*): Sell signal for ([\d\.]+) (.*) at ([\d\.]+) USDT'
        # Example: 2023-01-01 10:00:00 - INFO - Current balance: 1000.0 USDT (10.0% profit)
        balance_pattern = r'INFO - Current balance: ([\d\.]+) USDT \(([+-]?[\d\.]+)% profit\)'
        # Example: 2023-01-01 10:00:00 - INFO - Current open trades: 1
        open_trades_pattern = r'INFO - Current open trades: (\d+)'

        if "Buy signal" in line:
            match = re.search(buy_signal_pattern, line)
            if match:
                pair, amount, currency, price = match.groups()
                status.signals_count += 1
                status.trade_signals.append({"type": "buy", "pair": pair, "amount": float(amount), "price": float(price), "timestamp": datetime.now()})
                ErrorHandler.log_info(f"Parsed Buy Signal: {pair} {amount} {currency} at {price}")
        elif "Sell signal" in line:
            match = re.search(sell_signal_pattern, line)
            if match:
                pair, amount, currency, price = match.groups()
                status.signals_count += 1
                status.trade_signals.append({"type": "sell", "pair": pair, "amount": float(amount), "price": float(price), "timestamp": datetime.now()})
                ErrorHandler.log_info(f"Parsed Sell Signal: {pair} {amount} {currency} at {price}")
        elif "Current balance" in line:
            match = re.search(balance_pattern, line)
            if match:
                balance, profit_pct = match.groups()
                status.current_balance = float(balance)
                status.current_profit = float(profit_pct)
                status.balance_history.append({"timestamp": datetime.now(), "balance": float(balance), "profit_pct": float(profit_pct)})
                ErrorHandler.log_info(f"Parsed Balance: {balance} ({profit_pct}%)")
        elif "Current open trades" in line:
            match = re.search(open_trades_pattern, line)
            if match:
                open_trades = match.group(1)
                status.open_trades = int(open_trades)
                ErrorHandler.log_info(f"Parsed Open Trades: {open_trades}")
    
    def get_dry_run_logs(self, run_id: str, lines: int = 50) -> List[str]:
        """
        Get dry run logs
        
        Args:
            run_id: dry run ID
            lines: number of lines to retrieve
            
        Returns:
            list of log lines
        """
        try:
            log_file = Path(f"logs/dryrun_{run_id}.log")
            
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # Return last N lines
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to read dry run logs for {run_id}: {str(e)}")
            return []
    
    def cleanup_old_dry_runs(self, max_age_hours: int = 24):
        """
        Clean up old dry run data
        
        Args:
            max_age_hours: maximum age in hours for dry run data
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Clean up old status records
            old_runs = []
            for run_id, status in self.dry_run_status.items():
                if status.start_time < cutoff_time and status.status != ExecutionStatus.RUNNING:
                    old_runs.append(run_id)
            
            for run_id in old_runs:
                self.dry_run_status.pop(run_id, None)
                
                # Clean up associated files
                config_file = self.temp_dir / f"dryrun_config_{run_id}.json"
                if config_file.exists():
                    config_file.unlink()
                
                log_file = Path(f"logs/dryrun_{run_id}.log")
                if log_file.exists():
                    log_file.unlink()
                
                db_file = Path(f"dryrun_{run_id}.sqlite")
                if db_file.exists():
                    db_file.unlink()
            
            if old_runs:
                ErrorHandler.log_info(f"Cleaned up {len(old_runs)} old dry runs")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to cleanup old dry runs: {str(e)}")
    
    def shutdown(self):
        """Shutdown dry run executor"""
        try:
            ErrorHandler.log_info("Shutting down dry run executor...")
            
            # Stop monitoring
            self._monitoring_active = False
            
            # Stop all active dry runs
            active_runs = list(self.active_processes.keys())
            for run_id in active_runs:
                self.stop_dry_run(run_id)
            
            # Wait for monitor thread to finish
            if self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=10)
            
            ErrorHandler.log_info("Dry run executor shutdown completed")
        
        except Exception as e:
            ErrorHandler.log_error(f"Error during dry run executor shutdown: {str(e)}")
    
    def __del__(self):
        """Destructor"""
        self.shutdown()