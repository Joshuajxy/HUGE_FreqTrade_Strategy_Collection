"""
JupyterLab integration component
"""
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from utils.error_handling import ErrorHandler


class JupyterLabIntegration:
    """JupyterLab integration handler"""
    
    def __init__(self, work_dir: str = ".", port: int = 8888):
        """
        Initialize JupyterLab integration
        Args:
            work_dir: working directory for JupyterLab
            port: port to run JupyterLab on
        """
        self.work_dir = Path(work_dir)
        self.port = port
        self.process = None
        self.start_time = None
        
    def is_running(self) -> bool:
        """Check if JupyterLab is currently running"""
        if self.process is None:
            return False
            
        # Check if process is still alive
        try:
            return self.process.poll() is None
        except:
            return False
    
    def start_jupyter_lab(self, auto_open: bool = True) -> bool:
        """
        Start JupyterLab server
        Args:
            auto_open: whether to automatically open browser
        Returns:
            whether start was successful
        """
        try:
            if self.is_running():
                ErrorHandler.log_info("JupyterLab is already running")
                return True
                
            # Start JupyterLab process
            cmd = ["jupyter", "lab", "--port", str(self.port), "--no-browser"]
            
            self.process = subprocess.Popen(
                cmd,
                cwd=self.work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.start_time = datetime.now()
            ErrorHandler.log_info(f"JupyterLab started on port {self.port}")
            
            # Optionally open browser
            if auto_open:
                time.sleep(2)  # Give JupyterLab time to start
                webbrowser.open(f"http://localhost:{self.port}")
                
            return True
            
        except FileNotFoundError:
            ErrorHandler.log_error("JupyterLab not found. Please install with: pip install jupyterlab")
            return False
        except Exception as e:
            ErrorHandler.log_error(f"Error starting JupyterLab: {str(e)}")
            return False
    
    def stop_jupyter_lab(self) -> bool:
        """
        Stop JupyterLab server
        Returns:
            whether stop was successful
        """
        try:
            if not self.is_running():
                ErrorHandler.log_info("JupyterLab is not running")
                return True
                
            # Terminate process
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            self.start_time = None
            
            ErrorHandler.log_info("JupyterLab stopped")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(f"Error stopping JupyterLab: {str(e)}")
            return False
    
    def export_data_to_workspace(self, results: list, format_type: str = "json") -> Dict[str, Path]:
        """
        Export backtest results to Jupyter workspace
        Args:
            results: list of backtest results
            format_type: export format (json, csv, pickle)
        Returns:
            dictionary mapping file types to file paths
        """
        try:
            # Create exports directory
            exports_dir = self.work_dir / "jupyter_exports"
            exports_dir.mkdir(exist_ok=True)
            
            exported_files = {}
            
            # Convert results to exportable format
            export_data = []
            for result in results:
                if hasattr(result, 'to_dict'):
                    export_data.append(result.to_dict())
                else:
                    export_data.append(str(result))
            
            # Export based on format type
            if format_type == "json":
                import json
                file_path = exports_dir / f"backtest_results_{int(time.time())}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
                exported_files['results'] = file_path
                
            elif format_type == "csv":
                import pandas as pd
                file_path = exports_dir / f"backtest_results_{int(time.time())}.csv"
                df = pd.DataFrame(export_data)
                df.to_csv(file_path, index=False)
                exported_files['results'] = file_path
                
            elif format_type == "pickle":
                import pickle
                file_path = exports_dir / f"backtest_results_{int(time.time())}.pkl"
                with open(file_path, 'wb') as f:
                    pickle.dump(export_data, f)
                exported_files['results'] = file_path
            
            ErrorHandler.log_info(f"Data exported to {len(exported_files)} files")
            return exported_files
            
        except Exception as e:
            ErrorHandler.log_error(f"Error exporting data: {str(e)}")
            return {}