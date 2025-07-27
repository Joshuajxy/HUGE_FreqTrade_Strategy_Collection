"""
Jupyter interface integration for the backtest system
"""
import subprocess
import webbrowser
import socket
from pathlib import Path
from typing import Optional, Dict, Any, List
import streamlit as st
import time
import threading

from utils.data_models import BacktestResult, NotebookTemplate
from utils.error_handling import ErrorHandler, error_handler
from .template_manager import NotebookTemplateManager
from .data_exporter import DataExporter
from .notebook_executor import NotebookExecutor

class JupyterInterface:
    """Jupyter interface integration"""
    
    def __init__(self):
        """Initialize Jupyter interface"""
        self.template_manager = NotebookTemplateManager()
        self.data_exporter = DataExporter()
        self.notebook_executor = NotebookExecutor()
        
        # Jupyter server tracking
        self.jupyter_process = None
        self.jupyter_port = None
        self.jupyter_url = None
        
        ErrorHandler.log_info("Jupyter interface initialized")
    
    def _find_free_port(self, start_port: int = 8888) -> int:
        """Find a free port for Jupyter server"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        
        raise RuntimeError("No free port found for Jupyter server")
    
    def _check_jupyter_availability(self) -> Dict[str, bool]:
        """Check Jupyter components availability"""
        availability = {
            'jupyter_lab': False,
            'jupyter_notebook': False,
            'papermill': False
        }
        
        # Check Jupyter Lab
        try:
            result = subprocess.run(
                ["python", "-c", "import jupyterlab; print('available')"],
                capture_output=True,
                text=True,
                timeout=5
            )
            availability['jupyter_lab'] = result.returncode == 0
        except:
            pass
        
        # Check Jupyter Notebook
        try:
            result = subprocess.run(
                ["python", "-c", "import notebook; print('available')"],
                capture_output=True,
                text=True,
                timeout=5
            )
            availability['jupyter_notebook'] = result.returncode == 0
        except:
            pass
        
        # Check Papermill
        try:
            result = subprocess.run(
                ["python", "-c", "import papermill; print('available')"],
                capture_output=True,
                text=True,
                timeout=5
            )
            availability['papermill'] = result.returncode == 0
        except:
            pass
        
        return availability
    
    @error_handler(Exception, show_error=True)
    def start_jupyter_lab(self, port: Optional[int] = None) -> bool:
        """
        Start Jupyter Lab server
        
        Args:
            port: port to use (optional)
            
        Returns:
            whether startup was successful
        """
        try:
            if self.jupyter_process and self.jupyter_process.poll() is None:
                st.warning("Jupyter server is already running")
                return True
            
            # Find free port
            if not port:
                port = self._find_free_port()
            
            # Start Jupyter Lab
            cmd = [
                "python", "-m", "jupyterlab",
                "--port", str(port),
                "--no-browser",
                "--allow-root",
                f"--notebook-dir={Path.cwd()}"
            ]
            
            self.jupyter_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.jupyter_port = port
            self.jupyter_url = f"http://localhost:{port}"
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if server started successfully
            if self.jupyter_process.poll() is None:
                ErrorHandler.log_info(f"Jupyter Lab started on port {port}")
                return True
            else:
                stdout, stderr = self.jupyter_process.communicate()
                ErrorHandler.log_error(f"Jupyter Lab failed to start: {stderr}")
                return False
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to start Jupyter Lab: {str(e)}")
            return False
    
    @error_handler(Exception, show_error=True)
    def stop_jupyter_lab(self) -> bool:
        """Stop Jupyter Lab server"""
        try:
            if self.jupyter_process and self.jupyter_process.poll() is None:
                self.jupyter_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.jupyter_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.jupyter_process.kill()
                    self.jupyter_process.wait()
                
                self.jupyter_process = None
                self.jupyter_port = None
                self.jupyter_url = None
                
                ErrorHandler.log_info("Jupyter Lab stopped")
                return True
            else:
                st.info("Jupyter server is not running")
                return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to stop Jupyter Lab: {str(e)}")
            return False
    
    def get_jupyter_status(self) -> Dict[str, Any]:
        """Get Jupyter server status"""
        if self.jupyter_process and self.jupyter_process.poll() is None:
            return {
                'running': True,
                'port': self.jupyter_port,
                'url': self.jupyter_url,
                'pid': self.jupyter_process.pid
            }
        else:
            return {
                'running': False,
                'port': None,
                'url': None,
                'pid': None
            }
    
    def open_jupyter_in_browser(self) -> bool:
        """Open Jupyter Lab in browser"""
        try:
            if self.jupyter_url:
                webbrowser.open(self.jupyter_url)
                return True
            else:
                st.error("Jupyter server is not running")
                return False
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to open Jupyter in browser: {str(e)}")
            return False
    
    def render_jupyter_panel(self, results: List[BacktestResult] = None):
        """Render main Jupyter analysis panel"""
        st.header("📊 Jupyter Analysis")
        
        # Check Jupyter availability
        availability = self._check_jupyter_availability()
        
        # Display availability status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ Available" if availability['jupyter_lab'] else "❌ Not Available"
            st.metric("Jupyter Lab", status)
        
        with col2:
            status = "✅ Available" if availability['jupyter_notebook'] else "❌ Not Available"
            st.metric("Jupyter Notebook", status)
        
        with col3:
            status = "✅ Available" if availability['papermill'] else "❌ Not Available"
            st.metric("Papermill", status)
        
        # Installation instructions if needed
        missing_components = [k for k, v in availability.items() if not v]
        if missing_components:
            st.warning("Some Jupyter components are missing. Install with:")
            install_commands = {
                'jupyter_lab': "pip install jupyterlab",
                'jupyter_notebook': "pip install notebook",
                'papermill': "pip install papermill"
            }
            
            for component in missing_components:
                if component in install_commands:
                    st.code(install_commands[component])
        
        # Jupyter server control
        st.subheader("🚀 Jupyter Server Control")
        
        jupyter_status = self.get_jupyter_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if jupyter_status['running']:
                st.success(f"🟢 Running on port {jupyter_status['port']}")
            else:
                st.info("🔴 Not running")
        
        with col2:
            if not jupyter_status['running'] and availability['jupyter_lab']:
                if st.button("🚀 Start Jupyter Lab", type="primary"):
                    with st.spinner("Starting Jupyter Lab..."):
                        if self.start_jupyter_lab():
                            st.success("Jupyter Lab started successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to start Jupyter Lab")
            
            elif jupyter_status['running']:
                if st.button("⏹️ Stop Jupyter Lab"):
                    with st.spinner("Stopping Jupyter Lab..."):
                        if self.stop_jupyter_lab():
                            st.success("Jupyter Lab stopped")
                            time.sleep(1)
                            st.rerun()
        
        with col3:
            if jupyter_status['running']:
                if st.button("🌐 Open in Browser"):
                    if self.open_jupyter_in_browser():
                        st.success("Opening Jupyter Lab in browser...")
                    else:
                        st.error("Failed to open browser")
        
        # Analysis tabs
        if results:
            st.subheader("📓 Analysis Options")
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "Template Manager", 
                "Execute Analysis", 
                "Data Export", 
                "Execution Monitor"
            ])
            
            with tab1:
                self.template_manager.render_template_manager()
            
            with tab2:
                templates = self.template_manager.get_available_templates()
                self.notebook_executor.render_notebook_interface(templates, results)
            
            with tab3:
                self.data_exporter.render_export_interface(results)
            
            with tab4:
                self.notebook_executor.render_execution_monitor()
        
        else:
            st.info("No backtest results available. Run some backtests first to enable Jupyter analysis.")
    
    def render_quick_analysis(self, results: List[BacktestResult]):
        """Render quick analysis options"""
        st.subheader("⚡ Quick Analysis")
        
        if not results:
            st.info("No results available for quick analysis")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Generate Summary Report", use_container_width=True):
                with st.spinner("Generating summary report..."):
                    execution_id = self.notebook_executor.generate_automated_report(
                        results, "comprehensive"
                    )
                    
                    if execution_id:
                        st.success(f"Report generation started: {execution_id[:8]}...")
                    else:
                        st.error("Failed to start report generation")
        
        with col2:
            if st.button("📈 Strategy Comparison", use_container_width=True):
                if len(results) >= 2:
                    with st.spinner("Generating comparison analysis..."):
                        execution_id = self.notebook_executor.generate_automated_report(
                            results, "comparison"
                        )
                        
                        if execution_id:
                            st.success(f"Comparison analysis started: {execution_id[:8]}...")
                        else:
                            st.error("Failed to start comparison analysis")
                else:
                    st.warning("Need at least 2 strategies for comparison")
        
        with col3:
            if st.button("⚠️ Risk Analysis", use_container_width=True):
                with st.spinner("Generating risk analysis..."):
                    execution_id = self.notebook_executor.generate_automated_report(
                        results, "risk"
                    )
                    
                    if execution_id:
                        st.success(f"Risk analysis started: {execution_id[:8]}...")
                    else:
                        st.error("Failed to start risk analysis")
    
    def render_output_management(self):
        """Render output file management"""
        st.subheader("📁 Output Management")
        
        # Generated notebooks
        self.notebook_executor.render_output_files()
        
        # Export history
        st.subheader("📤 Export History")
        export_history = self.data_exporter.get_export_history()
        
        if export_history:
            history_data = []
            for item in export_history:
                history_data.append({
                    'Filename': item['filename'],
                    'Format': item['format'].upper(),
                    'Size (MB)': f"{item['size_mb']:.2f}",
                    'Created': item['created'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            import pandas as pd
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No export history available")
        
        # Cleanup options
        st.subheader("🧹 Cleanup")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clean Old Notebooks (7+ days)"):
                deleted_count = self.notebook_executor.cleanup_old_outputs(7)
                if deleted_count > 0:
                    st.success(f"Deleted {deleted_count} old notebook files")
                else:
                    st.info("No old notebook files to delete")
        
        with col2:
            if st.button("Clean Old Exports (30+ days)"):
                deleted_count = self.data_exporter.cleanup_old_exports(30)
                if deleted_count > 0:
                    st.success(f"Deleted {deleted_count} old export files")
                else:
                    st.info("No old export files to delete")
    
    def create_analysis_workspace(self, results: List[BacktestResult]) -> bool:
        """Create a dedicated analysis workspace"""
        try:
            workspace_dir = Path("jupyter_workspace")
            workspace_dir.mkdir(exist_ok=True)
            
            # Export data to workspace
            data_file = self.data_exporter.export_backtest_results(
                results, 
                "pickle", 
                "workspace_data"
            )
            
            if data_file:
                # Copy to workspace
                import shutil
                workspace_data = workspace_dir / "backtest_results.pkl"
                shutil.copy2(data_file, workspace_data)
                
                # Create starter notebook
                starter_notebook = {
                    "cells": [
                        {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": [
                                "# Backtest Analysis Workspace\n",
                                "\n",
                                "This notebook provides a starting point for analyzing your backtest results.\n",
                                "\n",
                                "## Getting Started\n",
                                "\n",
                                "1. Load the backtest results\n",
                                "2. Explore the data structure\n",
                                "3. Create your custom analysis\n"
                            ]
                        },
                        {
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "source": [
                                "import pickle\n",
                                "import pandas as pd\n",
                                "import numpy as np\n",
                                "import plotly.graph_objects as go\n",
                                "import plotly.express as px\n",
                                "from datetime import datetime\n",
                                "\n",
                                "# Load backtest results\n",
                                "with open('backtest_results.pkl', 'rb') as f:\n",
                                "    results = pickle.load(f)\n",
                                "\n",
                                "print(f\"Loaded {len(results)} backtest results\")\n",
                                "print(\"\\nStrategies:\")\n",
                                "for result in results:\n",
                                "    print(f\"- {result.strategy_name}: {result.metrics.total_return_pct:.2f}% return\")"
                            ]
                        },
                        {
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "source": [
                                "# Example: Create a simple performance comparison\n",
                                "strategy_names = [r.strategy_name for r in results]\n",
                                "returns = [r.metrics.total_return_pct for r in results]\n",
                                "\n",
                                "fig = go.Figure(data=[\n",
                                "    go.Bar(x=strategy_names, y=returns)\n",
                                "])\n",
                                "\n",
                                "fig.update_layout(\n",
                                "    title=\"Strategy Performance Comparison\",\n",
                                "    xaxis_title=\"Strategy\",\n",
                                "    yaxis_title=\"Total Return (%)\"\n",
                                ")\n",
                                "\n",
                                "fig.show()"
                            ]
                        },
                        {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": [
                                "## Your Analysis\n",
                                "\n",
                                "Add your custom analysis code below:"
                            ]
                        },
                        {
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "source": [
                                "# Your analysis code here\n"
                            ]
                        }
                    ],
                    "metadata": {
                        "kernelspec": {
                            "display_name": "Python 3",
                            "language": "python",
                            "name": "python3"
                        },
                        "language_info": {
                            "name": "python",
                            "version": "3.8.0"
                        }
                    },
                    "nbformat": 4,
                    "nbformat_minor": 4
                }
                
                # Save starter notebook
                starter_path = workspace_dir / "analysis_starter.ipynb"
                with open(starter_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(starter_notebook, f, indent=2, ensure_ascii=False)
                
                ErrorHandler.log_info(f"Analysis workspace created: {workspace_dir}")
                return True
            
            return False
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create analysis workspace: {str(e)}")
            return False
    
    def __del__(self):
        """Cleanup on destruction"""
        if self.jupyter_process and self.jupyter_process.poll() is None:
            try:
                self.jupyter_process.terminate()
                self.jupyter_process.wait(timeout=5)
            except:
                pass