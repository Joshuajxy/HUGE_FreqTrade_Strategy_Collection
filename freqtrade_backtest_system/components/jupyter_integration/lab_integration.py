"""
Jupyter Lab integration system (simplified version)
"""
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from utils.data_models import BacktestResult
from utils.error_handling import ErrorHandler, error_handler, ExecutionError

class JupyterLabIntegration:
    """Jupyter Lab integration system"""
    
    def __init__(self, work_dir: str = "jupyter_workspace", port: int = 8888):
        """Initialize Jupyter Lab integration"""
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.port = port
        self.process = None
        self._browser_opened = False
        self._setup_workspace()
    
    def _setup_workspace(self):
        """Setup Jupyter workspace structure"""
        directories = ["data", "notebooks", "templates", "exports", "scripts"]
        for directory in directories:
            (self.work_dir / directory).mkdir(exist_ok=True)
    
    def start_jupyter_lab(self, auto_open: bool = True, token: str = None) -> bool:
        """Start Jupyter Lab server"""
        if self.is_running():
            ErrorHandler.log_info("Jupyter Lab is already running")
            if auto_open:
                self._open_browser()
            return True
        
        try:
            cmd = [
                sys.executable, "-m", "jupyter", "lab",
                "--port", str(self.port),
                "--notebook-dir", str(self.work_dir),
                "--no-browser" if not auto_open else "--browser"
            ]
            
            if token is None:
                cmd.extend(["--NotebookApp.token=''", "--NotebookApp.password=''"])
            else:
                cmd.extend([f"--NotebookApp.token={token}"])
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=self.work_dir
            )
            
            if self._wait_for_server():
                ErrorHandler.log_info(f"Jupyter Lab started on port {self.port}")
                if auto_open and not self._browser_opened:
                    time.sleep(2)
                    self._open_browser()
                return True
            else:
                ErrorHandler.log_error("Jupyter Lab failed to start")
                return False
                
        except Exception as e:
            ErrorHandler.log_error(f"Error starting Jupyter Lab: {str(e)}")
            return False
    
    def _wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for Jupyter server to start"""
        try:
            import requests
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"http://localhost:{self.port}", timeout=1)
                    if response.status_code in [200, 302]:
                        return True
                except:
                    pass
                time.sleep(1)
            return False
        except ImportError:
            time.sleep(5)
            return True
    
    def _open_browser(self):
        """Open browser to Jupyter Lab"""
        try:
            url = f"http://localhost:{self.port}"
            webbrowser.open(url)
            self._browser_opened = True
            ErrorHandler.log_info(f"Opened browser to {url}")
        except Exception as e:
            ErrorHandler.log_warning(f"Could not open browser: {str(e)}")
    
    def stop_jupyter_lab(self) -> bool:
        """Stop Jupyter Lab server"""
        if not self.is_running():
            ErrorHandler.log_info("Jupyter Lab is not running")
            return True
        
        try:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                self.process = None
            
            self._kill_jupyter_processes()
            ErrorHandler.log_info("Jupyter Lab stopped")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(f"Error stopping Jupyter Lab: {str(e)}")
            return False
    
    def _kill_jupyter_processes(self):
        """Kill any remaining Jupyter processes on the port"""
        if not HAS_PSUTIL:
            return
            
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'jupyter' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if f"--port {self.port}" in cmdline or f"--port={self.port}" in cmdline:
                            proc.kill()
                            ErrorHandler.log_info(f"Killed Jupyter process {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            ErrorHandler.log_warning(f"Error killing Jupyter processes: {str(e)}")
    
    def is_running(self) -> bool:
        """Check if Jupyter Lab is running"""
        if self.process and self.process.poll() is None:
            return True
        
        if not HAS_PSUTIL:
            return False
            
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'jupyter' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if f"--port {self.port}" in cmdline or f"--port={self.port}" in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except:
            pass
        return False
    
    def export_data_to_workspace(self, results: List[BacktestResult], export_format: str = 'json') -> Dict[str, Path]:
        """Export backtest data to Jupyter workspace"""
        data_dir = self.work_dir / "data"
        exported_files = {}
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        try:
            if export_format == 'json':
                results_data = []
                for result in results:
                    results_data.append({
                        'strategy_name': result.strategy_name,
                        'metrics': {
                            'total_return_pct': result.metrics.total_return_pct,
                            'win_rate': result.metrics.win_rate,
                            'max_drawdown_pct': result.metrics.max_drawdown_pct,
                            'sharpe_ratio': result.metrics.sharpe_ratio,
                            'total_trades': result.metrics.total_trades
                        },
                        'timestamp': result.timestamp.isoformat()
                    })
                
                results_file = data_dir / f"backtest_results_{timestamp}.json"
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results_data, f, indent=2, ensure_ascii=False)
                exported_files['results'] = results_file
                
            elif export_format == 'csv':
                try:
                    import pandas as pd
                    metrics_data = []
                    for result in results:
                        metrics_data.append({
                            'strategy_name': result.strategy_name,
                            'total_return_pct': result.metrics.total_return_pct,
                            'win_rate': result.metrics.win_rate,
                            'max_drawdown_pct': result.metrics.max_drawdown_pct,
                            'sharpe_ratio': result.metrics.sharpe_ratio,
                            'total_trades': result.metrics.total_trades,
                            'timestamp': result.timestamp.isoformat()
                        })
                    
                    metrics_df = pd.DataFrame(metrics_data)
                    metrics_file = data_dir / f"metrics_{timestamp}.csv"
                    metrics_df.to_csv(metrics_file, index=False)
                    exported_files['metrics'] = metrics_file
                    
                except ImportError:
                    ErrorHandler.log_error("pandas not available for CSV export")
                    raise ExecutionError("pandas required for CSV export")
            
            ErrorHandler.log_info(f"Exported data to workspace: {len(exported_files)} files")
            return exported_files
            
        except Exception as e:
            ErrorHandler.log_error(f"Error exporting data: {str(e)}")
            raise ExecutionError(f"Failed to export data: {str(e)}")