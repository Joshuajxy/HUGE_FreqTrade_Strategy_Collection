"""
Notebook execution system with papermill integration
"""
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import threading
import time
import streamlit as st

from utils.data_models import NotebookTemplate, BacktestResult, ExecutionStatus
from utils.error_handling import ErrorHandler, ExecutionError, error_handler

class NotebookExecutor:
    """Notebook execution system with papermill integration"""
    
    def __init__(self, output_dir: str = "notebook_outputs"):
        """
        Initialize notebook executor
        
        Args:
            output_dir: directory for notebook outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "executed").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "temp").mkdir(exist_ok=True)
        
        # Execution tracking
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Check papermill availability
        self._check_papermill()
        
        ErrorHandler.log_info(f"Notebook executor initialized: {self.output_dir}")
    
    def _check_papermill(self):
        """Check if papermill is available"""
        try:
            result = subprocess.run(
                ["python", "-c", "import papermill; print(papermill.__version__)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                ErrorHandler.log_info(f"Papermill available: v{version}")
                self.papermill_available = True
            else:
                ErrorHandler.log_warning("Papermill not available - some features may be limited")
                self.papermill_available = False
        
        except Exception as e:
            ErrorHandler.log_warning(f"Failed to check papermill: {str(e)}")
            self.papermill_available = False
    
    @error_handler(ExecutionError, show_error=True)
    def execute_notebook(self, 
                         template: NotebookTemplate,
                         parameters: Dict[str, Any],
                         output_name: Optional[str] = None,
                         progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        Execute notebook with parameters
        
        Args:
            template: notebook template to execute
            parameters: parameters to pass to notebook
            output_name: custom output name
            progress_callback: callback for progress updates
            
        Returns:
            execution ID
        """
        try:
            # Generate execution ID
            execution_id = f"exec_{int(time.time())}_{len(self.active_executions)}"
            
            # Generate output filename
            if not output_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"{template.name.replace(' ', '_')}_{timestamp}"
            
            output_path = self.output_dir / "executed" / f"{output_name}.ipynb"
            
            # Create execution record
            execution_record = {
                'execution_id': execution_id,
                'template': template.name,
                'template_path': str(template.file_path),
                'output_path': str(output_path),
                'parameters': parameters,
                'status': ExecutionStatus.RUNNING,
                'start_time': datetime.now(),
                'progress_callback': progress_callback,
                'error_message': None
            }
            
            self.active_executions[execution_id] = execution_record
            
            # Execute notebook in background thread
            execution_thread = threading.Thread(
                target=self._execute_notebook_thread,
                args=(execution_id, template, parameters, output_path)
            )
            execution_thread.daemon = True
            execution_thread.start()
            
            ErrorHandler.log_info(f"Started notebook execution: {execution_id}")
            return execution_id
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to start notebook execution: {str(e)}")
            raise ExecutionError(f"Failed to start notebook execution: {str(e)}")
    
    def _execute_notebook_thread(self, 
                                execution_id: str,
                                template: NotebookTemplate,
                                parameters: Dict[str, Any],
                                output_path: Path):
        """Execute notebook in background thread"""
        try:
            execution_record = self.active_executions[execution_id]
            
            if self.papermill_available:
                # Use papermill for execution
                self._execute_with_papermill(execution_id, template, parameters, output_path)
            else:
                # Fallback to manual parameter substitution
                self._execute_with_substitution(execution_id, template, parameters, output_path)
            
            # Mark as completed
            execution_record['status'] = ExecutionStatus.COMPLETED
            execution_record['end_time'] = datetime.now()
            execution_record['execution_time'] = (
                execution_record['end_time'] - execution_record['start_time']
            ).total_seconds()
            
            # Call progress callback
            if execution_record['progress_callback']:
                execution_record['progress_callback'](execution_id, ExecutionStatus.COMPLETED)
            
            ErrorHandler.log_info(f"Notebook execution completed: {execution_id}")
        
        except Exception as e:
            # Mark as failed
            execution_record = self.active_executions.get(execution_id, {})
            execution_record['status'] = ExecutionStatus.FAILED
            execution_record['error_message'] = str(e)
            execution_record['end_time'] = datetime.now()
            
            # Call progress callback
            if execution_record.get('progress_callback'):
                execution_record['progress_callback'](execution_id, ExecutionStatus.FAILED)
            
            ErrorHandler.log_error(f"Notebook execution failed: {execution_id} - {str(e)}")
        
        finally:
            # Move to history
            if execution_id in self.active_executions:
                self.execution_history.append(self.active_executions[execution_id])
                del self.active_executions[execution_id]
    
    def _execute_with_papermill(self, 
                               execution_id: str,
                               template: NotebookTemplate,
                               parameters: Dict[str, Any],
                               output_path: Path):
        """Execute notebook using papermill"""
        try:
            # Build papermill command
            cmd = [
                "python", "-m", "papermill",
                str(template.file_path),
                str(output_path),
                "-p", json.dumps(parameters)
            ]
            
            # Execute with papermill
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor execution
            while process.poll() is None:
                time.sleep(1)
                
                # Update progress callback if available
                execution_record = self.active_executions.get(execution_id, {})
                if execution_record.get('progress_callback'):
                    execution_record['progress_callback'](execution_id, ExecutionStatus.RUNNING)
            
            # Check result
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise ExecutionError(f"Papermill execution failed: {stderr}")
            
            ErrorHandler.log_info(f"Papermill execution successful: {execution_id}")
        
        except Exception as e:
            raise ExecutionError(f"Papermill execution error: {str(e)}")
    
    def _execute_with_substitution(self, 
                                  execution_id: str,
                                  template: NotebookTemplate,
                                  parameters: Dict[str, Any],
                                  output_path: Path):
        """Execute notebook with manual parameter substitution"""
        try:
            # Read template
            with open(template.file_path, 'r', encoding='utf-8') as f:
                notebook_content = json.load(f)
            
            # Substitute parameters in notebook cells
            for cell in notebook_content.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', [])
                    
                    if isinstance(source, list):
                        # Join source lines
                        source_text = ''.join(source)
                    else:
                        source_text = str(source)
                    
                    # Substitute parameters
                    for param_name, param_value in parameters.items():
                        placeholder = f"{{{{{param_name}}}}}"
                        if isinstance(param_value, str):
                            replacement = f'"{param_value}"'
                        else:
                            replacement = str(param_value)
                        
                        source_text = source_text.replace(placeholder, replacement)
                    
                    # Update cell source
                    cell['source'] = source_text.split('\n')
                
                elif cell.get('cell_type') == 'markdown':
                    source = cell.get('source', [])
                    
                    if isinstance(source, list):
                        source_text = ''.join(source)
                    else:
                        source_text = str(source)
                    
                    # Substitute parameters in markdown
                    for param_name, param_value in parameters.items():
                        placeholder = f"{{{{{param_name}}}}}"
                        source_text = source_text.replace(placeholder, str(param_value))
                    
                    cell['source'] = source_text.split('\n')
            
            # Add execution metadata
            if 'metadata' not in notebook_content:
                notebook_content['metadata'] = {}
            
            notebook_content['metadata'].update({
                'execution_id': execution_id,
                'executed_at': datetime.now().isoformat(),
                'parameters': parameters,
                'template_name': template.name
            })
            
            # Save executed notebook
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(notebook_content, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Manual substitution execution successful: {execution_id}")
        
        except Exception as e:
            raise ExecutionError(f"Manual substitution error: {str(e)}")
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].copy()
        
        # Check history
        for record in self.execution_history:
            if record['execution_id'] == execution_id:
                return record.copy()
        
        return None
    
    def get_active_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active executions"""
        return {k: v.copy() for k, v in self.active_executions.items()}
    
    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history[-limit:] if limit > 0 else self.execution_history
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel active execution"""
        try:
            if execution_id in self.active_executions:
                execution_record = self.active_executions[execution_id]
                execution_record['status'] = ExecutionStatus.STOPPED
                execution_record['end_time'] = datetime.now()
                execution_record['error_message'] = "Execution cancelled by user"
                
                # Move to history
                self.execution_history.append(execution_record)
                del self.active_executions[execution_id]
                
                ErrorHandler.log_info(f"Execution cancelled: {execution_id}")
                return True
            
            return False
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to cancel execution: {str(e)}")
            return False 
   
    @error_handler(Exception, show_error=True)
    def generate_automated_report(self, 
                                 results: List[BacktestResult],
                                 report_type: str = "comprehensive") -> Optional[str]:
        """
        Generate automated analysis report
        
        Args:
            results: backtest results
            report_type: type of report to generate
            
        Returns:
            execution ID
        """
        try:
            # Select appropriate template based on report type
            if report_type == "comprehensive":
                template_name = "Performance Report"
            elif report_type == "comparison":
                template_name = "Strategy Comparison"
            elif report_type == "risk":
                template_name = "Risk Analysis"
            else:
                template_name = "Performance Report"
            
            # Find template (simplified - in real implementation, get from template manager)
            template = NotebookTemplate(
                name=template_name,
                description=f"Automated {report_type} report",
                file_path=Path(f"notebook_templates/predefined/{template_name.lower().replace(' ', '_')}.ipynb"),
                parameters=["results", "report_config"],
                template_type="report"
            )
            
            # Prepare parameters
            parameters = {
                "results": results,
                "report_type": report_type,
                "timestamp": datetime.now().isoformat(),
                "strategy_count": len(results)
            }
            
            # Execute notebook
            execution_id = self.execute_notebook(
                template,
                parameters,
                f"automated_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            return execution_id
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to generate automated report: {str(e)}")
            return None
    
    def render_execution_monitor(self):
        """Render notebook execution monitoring interface"""
        st.subheader("📓 Notebook Execution Monitor")
        
        # Active executions
        active_executions = self.get_active_executions()
        
        if active_executions:
            st.write("**Active Executions:**")
            
            for execution_id, record in active_executions.items():
                with st.expander(f"🔄 {record['template']} ({execution_id[:8]}...)", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Status", record['status'].value.title())
                        runtime = datetime.now() - record['start_time']
                        st.metric("Runtime", str(runtime).split('.')[0])
                    
                    with col2:
                        st.write(f"**Template:** {record['template']}")
                        st.write(f"**Output:** {Path(record['output_path']).name}")
                    
                    with col3:
                        if st.button(f"Cancel", key=f"cancel_{execution_id}"):
                            if self.cancel_execution(execution_id):
                                st.success("Execution cancelled")
                                st.rerun()
                    
                    # Show parameters
                    if record['parameters']:
                        st.write("**Parameters:**")
                        for param, value in record['parameters'].items():
                            st.write(f"- {param}: {value}")
        else:
            st.info("No active notebook executions")
        
        # Execution history
        st.subheader("📜 Execution History")
        history = self.get_execution_history(10)
        
        if history:
            history_data = []
            for record in reversed(history):  # Show newest first
                status_emoji = {
                    ExecutionStatus.COMPLETED: "✅",
                    ExecutionStatus.FAILED: "❌",
                    ExecutionStatus.STOPPED: "⏹️"
                }.get(record['status'], "❓")
                
                execution_time = record.get('execution_time', 0)
                
                history_data.append({
                    'Template': record['template'],
                    'Status': f"{status_emoji} {record['status'].value.title()}",
                    'Start Time': record['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'Duration': f"{execution_time:.1f}s" if execution_time else "N/A",
                    'Output': Path(record['output_path']).name,
                    'ID': record['execution_id'][:8] + "..."
                })
            
            import pandas as pd
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No execution history available")
    
    def render_notebook_interface(self, templates: List[NotebookTemplate], results: List[BacktestResult] = None):
        """Render notebook execution interface"""
        st.subheader("📓 Jupyter Notebook Analysis")
        
        if not templates:
            st.info("No notebook templates available")
            return
        
        # Template selection
        selected_template = st.selectbox(
            "Select Analysis Template",
            templates,
            format_func=lambda x: x.name
        )
        
        if selected_template:
            st.write(f"**Description:** {selected_template.description}")
            
            if selected_template.parameters:
                st.write(f"**Required Parameters:** {', '.join(selected_template.parameters)}")
            
            # Parameter configuration
            st.subheader("📝 Configure Parameters")
            
            parameters = {}
            
            # Common parameters
            if "results" in selected_template.parameters or "backtest_results" in selected_template.parameters:
                if results:
                    parameters["results"] = results
                    parameters["backtest_results"] = results
                    st.success(f"✅ Using {len(results)} backtest results")
                else:
                    st.warning("⚠️ No backtest results available")
                    return
            
            if "strategy_name" in selected_template.parameters:
                if results:
                    strategy_names = [r.strategy_name for r in results]
                    selected_strategy = st.selectbox("Select Strategy", strategy_names)
                    parameters["strategy_name"] = selected_strategy
                    
                    # Find the specific result
                    selected_result = next(r for r in results if r.strategy_name == selected_strategy)
                    parameters["backtest_result"] = selected_result
            
            if "timestamp" in selected_template.parameters:
                parameters["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if "report_type" in selected_template.parameters:
                report_type = st.selectbox(
                    "Report Type",
                    ["comprehensive", "summary", "detailed"],
                    index=0
                )
                parameters["report_type"] = report_type
            
            # Custom parameters
            st.write("**Additional Parameters:**")
            custom_params = st.text_area(
                "Custom Parameters (JSON format)",
                placeholder='{"param1": "value1", "param2": 123}',
                help="Add custom parameters in JSON format"
            )
            
            if custom_params:
                try:
                    import json
                    custom_dict = json.loads(custom_params)
                    parameters.update(custom_dict)
                    st.success("✅ Custom parameters added")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format")
            
            # Output configuration
            st.subheader("📁 Output Configuration")
            
            custom_output_name = st.text_input(
                "Custom Output Name (optional)",
                placeholder="Leave empty for auto-generated name"
            )
            
            # Execute button
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Execute Notebook", type="primary"):
                    if parameters:
                        with st.spinner("Starting notebook execution..."):
                            execution_id = self.execute_notebook(
                                selected_template,
                                parameters,
                                custom_output_name if custom_output_name else None
                            )
                            
                            if execution_id:
                                st.success(f"✅ Notebook execution started: {execution_id[:8]}...")
                                st.info("Monitor progress in the Execution Monitor section")
                            else:
                                st.error("❌ Failed to start notebook execution")
                    else:
                        st.error("❌ Please configure required parameters")
            
            with col2:
                if results and st.button("📊 Generate Auto Report"):
                    with st.spinner("Generating automated report..."):
                        execution_id = self.generate_automated_report(results, "comprehensive")
                        
                        if execution_id:
                            st.success(f"✅ Report generation started: {execution_id[:8]}...")
                        else:
                            st.error("❌ Failed to start report generation")
    
    def get_output_files(self) -> List[Dict[str, Any]]:
        """Get list of output notebook files"""
        output_files = []
        
        try:
            executed_dir = self.output_dir / "executed"
            
            for file_path in executed_dir.glob("*.ipynb"):
                stat = file_path.stat()
                
                # Try to read metadata from notebook
                metadata = {}
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        notebook_content = json.load(f)
                        metadata = notebook_content.get('metadata', {})
                except:
                    pass
                
                output_files.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size_mb': stat.st_size / (1024 * 1024),
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'execution_id': metadata.get('execution_id', 'Unknown'),
                    'template_name': metadata.get('template_name', 'Unknown')
                })
            
            # Sort by creation time (newest first)
            output_files.sort(key=lambda x: x['created'], reverse=True)
            return output_files
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get output files: {str(e)}")
            return []
    
    def render_output_files(self):
        """Render output files interface"""
        st.subheader("📁 Generated Notebooks")
        
        output_files = self.get_output_files()
        
        if output_files:
            for file_info in output_files:
                with st.expander(f"📓 {file_info['filename']}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Template:** {file_info['template_name']}")
                        st.write(f"**Size:** {file_info['size_mb']:.2f} MB")
                    
                    with col2:
                        st.write(f"**Created:** {file_info['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Execution ID:** {file_info['execution_id']}")
                    
                    with col3:
                        # Download button
                        try:
                            with open(file_info['path'], 'rb') as f:
                                st.download_button(
                                    "📥 Download",
                                    data=f.read(),
                                    file_name=file_info['filename'],
                                    mime="application/json",
                                    key=f"download_{file_info['filename']}"
                                )
                        except Exception as e:
                            st.error(f"Download failed: {str(e)}")
        else:
            st.info("No generated notebooks available")
    
    def cleanup_old_outputs(self, days_old: int = 7) -> int:
        """Clean up old output files"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            executed_dir = self.output_dir / "executed"
            
            for file_path in executed_dir.glob("*.ipynb"):
                if file_path.stat().st_ctime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            ErrorHandler.log_info(f"Cleaned up {deleted_count} old notebook outputs")
            return deleted_count
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to cleanup old outputs: {str(e)}")
            return 0