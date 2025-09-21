"""
Real-time monitoring panel for execution status and logs
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading

from utils.data_models import ExecutionStatus, DryRunStatus
from utils.error_handling import ErrorHandler, error_handler

class MonitoringPanel:
    """Real-time monitoring panel for execution status"""
    
    def __init__(self):
        """Initialize monitoring panel"""
        self.refresh_interval = 5  # seconds
        self.max_log_lines = 100
        self.status_colors = {
            ExecutionStatus.IDLE: '#6c757d',
            ExecutionStatus.RUNNING: '#ffc107',
            ExecutionStatus.COMPLETED: '#28a745',
            ExecutionStatus.FAILED: '#dc3545',
            ExecutionStatus.STOPPED: '#6f42c1'
        }
    
    @error_handler(Exception, show_error=True)
    def render_execution_monitor(self, 
                                scheduler=None, 
                                task_ids: Dict[str, str] = None):
        """
        Render execution monitoring interface
        
        Args:
            scheduler: execution scheduler instance
            task_ids: dictionary mapping strategy names to task IDs
        """
        st.subheader("🔄 Execution Monitor")
        
        if not scheduler or not task_ids:
            st.info("No active executions to monitor")
            return
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        
        if auto_refresh:
            # Create placeholder for dynamic content
            placeholder = st.empty()
            
            # Refresh loop
            for _ in range(60):  # Refresh for 5 minutes max
                with placeholder.container():
                    self._render_execution_status(scheduler, task_ids)
                
                if not auto_refresh:
                    break
                
                time.sleep(self.refresh_interval)
        else:
            # Static display
            self._render_execution_status(scheduler, task_ids)
    
    def _render_execution_status(self, scheduler, task_ids: Dict[str, str]):
        """Render current execution status"""
        try:
            # Get execution statistics
            stats = scheduler.get_execution_statistics()
            status_dict = scheduler.get_execution_status()
            
            # Display overall statistics
            self._render_statistics_cards(stats)
            
            # Display progress bar
            self._render_progress_bar(stats)
            
            # Display individual task status
            self._render_task_status_table(task_ids, status_dict, scheduler)
            
            # Display execution timeline
            self._render_execution_timeline(task_ids, scheduler)
            
        except Exception as e:
            st.error(f"Error updating execution status: {str(e)}")
    
    def _render_statistics_cards(self, stats: Dict[str, Any]):
        """Render statistics cards"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Tasks",
                stats.get('total_tasks', 0),
                help="Total number of tasks submitted"
            )
        
        with col2:
            st.metric(
                "Running",
                stats.get('running_tasks', 0),
                delta=f"/{stats.get('max_workers', 0)} workers",
                help="Currently running tasks"
            )
        
        with col3:
            st.metric(
                "Completed",
                stats.get('completed_tasks', 0),
                delta="✅" if stats.get('completed_tasks', 0) > 0 else None,
                help="Successfully completed tasks"
            )
        
        with col4:
            st.metric(
                "Failed",
                stats.get('failed_tasks', 0),
                delta="❌" if stats.get('failed_tasks', 0) > 0 else None,
                help="Failed tasks"
            )
        
        with col5:
            st.metric(
                "Stopped",
                stats.get('stopped_tasks', 0),
                delta="⏹️" if stats.get('stopped_tasks', 0) > 0 else None,
                help="Manually stopped tasks"
            )
    
    def _render_progress_bar(self, stats: Dict[str, Any]):
        """Render overall progress bar"""
        total_tasks = stats.get('total_tasks', 0)
        
        if total_tasks > 0:
            completed = stats.get('completed_tasks', 0)
            failed = stats.get('failed_tasks', 0)
            stopped = stats.get('stopped_tasks', 0)
            finished = completed + failed + stopped
            
            progress = finished / total_tasks
            
            st.progress(
                progress,
                text=f"Overall Progress: {finished}/{total_tasks} ({progress:.1%})"
            )
            
            # Detailed progress breakdown
            if finished > 0:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if completed > 0:
                        st.success(f"✅ {completed} completed")
                
                with col2:
                    if failed > 0:
                        st.error(f"❌ {failed} failed")
                
                with col3:
                    if stopped > 0:
                        st.warning(f"⏹️ {stopped} stopped")
    
    def _render_task_status_table(self, 
                                 task_ids: Dict[str, str], 
                                 status_dict: Dict[str, ExecutionStatus],
                                 scheduler):
        """Render task status table"""
        st.subheader("Task Status")
        
        # Create status data
        status_data = []
        
        for strategy, task_id in task_ids.items():
            status = status_dict.get(task_id, ExecutionStatus.IDLE)
            metadata = scheduler.get_task_metadata(task_id)
            
            # Calculate duration
            duration = "N/A"
            if metadata and 'start_time' in metadata:
                start_time = metadata['start_time']
                if isinstance(start_time, datetime):
                    if status == ExecutionStatus.RUNNING:
                        duration = str(datetime.now() - start_time).split('.')[0]
                    else:
                        # For completed tasks, we'd need end time
                        duration = "Completed"
            
            status_data.append({
                'Strategy': strategy,
                'Status': status.value.title(),
                'Duration': duration,
                'Task ID': task_id[:8] + "..."  # Shortened ID
            })
        
        # Display as DataFrame
        if status_data:
            df = pd.DataFrame(status_data)
            
            # Style the dataframe
            def style_status(val):
                if val.lower() == 'running':
                    return 'background-color: #fff3cd; color: #856404'
                elif val.lower() == 'completed':
                    return 'background-color: #d4edda; color: #155724'
                elif val.lower() == 'failed':
                    return 'background-color: #f8d7da; color: #721c24'
                elif val.lower() == 'stopped':
                    return 'background-color: #e2e3e5; color: #383d41'
                return ''
            
            styled_df = df.style.applymap(style_status, subset=['Status'])
            st.dataframe(styled_df, width='stretch')
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Refresh Status"):
                    st.rerun()
            
            with col2:
                if st.button("⏹️ Stop All"):
                    for task_id in task_ids.values():
                        scheduler.cancel_task(task_id)
                    st.success("Stop signal sent to all tasks")
                    time.sleep(1)
                    st.rerun()
            
            with col3:
                if st.button("🧹 Clear Completed"):
                    scheduler.clear_completed_tasks()
                    st.success("Completed tasks cleared")
                    time.sleep(1)
                    st.rerun()
    
    def _render_execution_timeline(self, task_ids: Dict[str, str], scheduler):
        """Render execution timeline chart"""
        try:
            st.subheader("Execution Timeline")
            
            # Get task metadata
            timeline_data = []
            
            for strategy, task_id in task_ids.items():
                metadata = scheduler.get_task_metadata(task_id)
                status = scheduler.get_task_status(task_id)
                
                if metadata and 'start_time' in metadata:
                    start_time = metadata['start_time']
                    
                    # Estimate end time based on status
                    if status == ExecutionStatus.RUNNING:
                        end_time = datetime.now()
                    else:
                        # For completed tasks, estimate based on typical duration
                        end_time = start_time + timedelta(minutes=5)  # Placeholder
                    
                    timeline_data.append({
                        'Strategy': strategy,
                        'Start': start_time,
                        'End': end_time,
                        'Status': status.value,
                        'Duration': (end_time - start_time).total_seconds()
                    })
            
            if timeline_data:
                # Create Gantt-like chart
                fig = go.Figure()
                
                for i, data in enumerate(timeline_data):
                    color = self.status_colors.get(
                        ExecutionStatus(data['Status']), 
                        '#6c757d'
                    )
                    
                    fig.add_trace(go.Scatter(
                        x=[data['Start'], data['End']],
                        y=[i, i],
                        mode='lines+markers',
                        name=data['Strategy'],
                        line=dict(color=color, width=8),
                        marker=dict(size=8, color=color),
                        hovertemplate=f"<b>{data['Strategy']}</b><br>" +
                                    f"Status: {data['Status']}<br>" +
                                    f"Start: {data['Start']}<br>" +
                                    f"Duration: {data['Duration']:.0f}s<extra></extra>"
                    ))
                
                fig.update_layout(
                    title="Task Execution Timeline",
                    xaxis_title="Time",
                    yaxis=dict(
                        tickmode='array',
                        tickvals=list(range(len(timeline_data))),
                        ticktext=[data['Strategy'] for data in timeline_data]
                    ),
                    height=max(300, len(timeline_data) * 50),
                    showlegend=False,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No timeline data available")
        
        except Exception as e:
            st.error(f"Error creating timeline: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def render_dry_run_monitor(self, dry_run_executor=None):
        """
        Render dry run monitoring interface
        
        Args:
            dry_run_executor: dry run executor instance
        """
        st.subheader("📊 Dry Run Monitor")
        
        if not dry_run_executor:
            st.info("No dry run executor available")
            return
        
        # Get active dry runs
        active_dry_runs = dry_run_executor.get_active_dry_runs()
        all_dry_runs = dry_run_executor.get_all_dry_runs()
        
        if not all_dry_runs:
            st.info("No dry runs currently active or in history")
            return
        
        # Display active dry runs
        if active_dry_runs:
            st.subheader("🔴 Active Dry Runs")
            
            for run_id, status in active_dry_runs.items():
                with st.expander(f"🔄 {status.strategy} (ID: {run_id[:8]}...)", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Status", status.status.value.title())
                        st.metric("Signals", status.signals_count)
                    
                    with col2:
                        st.metric("Current Balance", f"{status.current_balance:.2f}")
                        st.metric("Current Profit", f"{status.current_profit:.2f}")
                    
                    with col3:
                        st.metric("Open Trades", status.open_trades)
                        runtime = datetime.now() - status.start_time
                        st.metric("Runtime", str(runtime).split('.')[0])
                    
                    # Control buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"⏹️ Stop", key=f"stop_{run_id}"):
                            if dry_run_executor.stop_dry_run(run_id):
                                st.success("Dry run stopped")
                                st.rerun()
                    
                    with col2:
                        if st.button(f"🔄 Restart", key=f"restart_{run_id}"):
                            if dry_run_executor.restart_dry_run(run_id):
                                st.success("Dry run restarted")
                                st.rerun()
                    
                    with col3:
                        if st.button(f"📋 View Logs", key=f"logs_{run_id}"):
                            self._show_dry_run_logs(dry_run_executor, run_id)
        
        # Display dry run history
        st.subheader("📜 Dry Run History")
        
        history_data = []
        for run_id, status in all_dry_runs.items():
            history_data.append({
                'Run ID': run_id[:8] + "...",
                'Strategy': status.strategy,
                'Status': status.status.value.title(),
                'Start Time': status.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Last Update': status.last_update.strftime('%Y-%m-%d %H:%M:%S'),
                'Signals': status.signals_count,
                'Profit': f"{status.current_profit:.2f}"
            })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, width='stretch')
    
    def _show_dry_run_logs(self, dry_run_executor, run_id: str):
        """Show dry run logs"""
        try:
            logs = dry_run_executor.get_dry_run_logs(run_id, lines=50)
            
            if logs:
                st.subheader(f"📋 Logs for {run_id[:8]}...")
                
                # Display logs in a text area
                log_text = "".join(logs)
                st.text_area(
                    "Recent Logs",
                    value=log_text,
                    height=400,
                    disabled=True
                )
                
                # Download button for full logs
                st.download_button(
                    "📥 Download Full Logs",
                    data=log_text,
                    file_name=f"dryrun_logs_{run_id[:8]}.txt",
                    mime="text/plain"
                )
            else:
                st.info("No logs available for this dry run")
        
        except Exception as e:
            st.error(f"Error retrieving logs: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def render_system_monitor(self):
        """Render system resource monitoring"""
        st.subheader("🖥️ System Monitor")
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "CPU Usage",
                    f"{cpu_percent:.1f}%",
                    delta=f"{'🔴' if cpu_percent > 80 else '🟢'}"
                )
            
            with col2:
                st.metric(
                    "Memory Usage",
                    f"{memory_percent:.1f}%",
                    delta=f"{'🔴' if memory_percent > 80 else '🟢'}"
                )
            
            with col3:
                st.metric(
                    "Disk Usage",
                    f"{disk_percent:.1f}%",
                    delta=f"{'🔴' if disk_percent > 90 else '🟢'}"
                )
            
            # Create resource usage chart
            fig = go.Figure()
            
            categories = ['CPU', 'Memory', 'Disk']
            values = [cpu_percent, memory_percent, disk_percent]
            colors = ['red' if v > 80 else 'yellow' if v > 60 else 'green' for v in values]
            
            fig.add_trace(go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=[f"{v:.1f}%" for v in values],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="System Resource Usage",
                yaxis_title="Usage (%)",
                yaxis=dict(range=[0, 100]),
                height=400,
                template="plotly_white",
                showlegend=False
            )
            
            st.plotly_chart(fig, width='stretch')
            
        except ImportError:
            st.warning("psutil not available - install with: pip install psutil")
        except Exception as e:
            st.error(f"Error monitoring system resources: {str(e)}")
    
    def render_log_viewer(self, log_file_path: str = "logs/app.log"):
        """
        Render log file viewer
        
        Args:
            log_file_path: path to log file
        """
        st.subheader("📋 Log Viewer")
        
        try:
            from pathlib import Path
            
            log_file = Path(log_file_path)
            
            if not log_file.exists():
                st.info(f"Log file not found: {log_file_path}")
                return
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Display controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                num_lines = st.selectbox(
                    "Lines to show",
                    [50, 100, 200, 500, "All"],
                    index=1
                )
            
            with col2:
                log_level = st.selectbox(
                    "Filter by level",
                    ["All", "ERROR", "WARNING", "INFO", "DEBUG"]
                )
            
            with col3:
                if st.button("🔄 Refresh Logs"):
                    st.rerun()
            
            # Filter logs
            filtered_lines = lines
            
            if log_level != "All":
                filtered_lines = [line for line in lines if log_level in line]
            
            # Limit number of lines
            if num_lines != "All":
                filtered_lines = filtered_lines[-num_lines:]
            
            # Display logs
            if filtered_lines:
                log_text = "".join(filtered_lines)
                
                st.text_area(
                    "Log Content",
                    value=log_text,
                    height=500,
                    disabled=True
                )
                
                # Download button
                st.download_button(
                    "📥 Download Logs",
                    data=log_text,
                    file_name=f"app_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            else:
                st.info("No logs match the current filter")
        
        except Exception as e:
            st.error(f"Error reading log file: {str(e)}")