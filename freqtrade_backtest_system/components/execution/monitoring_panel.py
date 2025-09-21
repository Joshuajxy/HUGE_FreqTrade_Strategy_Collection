"""
Execution monitoring panel with real-time log display
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add plotly import
import plotly.graph_objects as go

from utils.data_models import ExecutionStatus, BacktestResult
from utils.error_handling import ErrorHandler


class ExecutionMonitoringPanel:
    """Execution monitoring panel with real-time log display"""
    
    def __init__(self):
        """Initialize monitoring panel"""
        # Initialize session state for logs
        if 'task_logs' not in st.session_state:
            st.session_state.task_logs = {}
        if 'task_start_times' not in st.session_state:
            st.session_state.task_start_times = {}
        
        # Define status colors
        self.status_colors = {
            ExecutionStatus.RUNNING: '#ffc107',    # Yellow
            ExecutionStatus.COMPLETED: '#28a745',  # Green
            ExecutionStatus.FAILED: '#dc3545',     # Red
            ExecutionStatus.STOPPED: '#6c757d',    # Gray
            ExecutionStatus.IDLE: '#6c757d'        # Gray
        }
    
    def render_execution_monitor(self, scheduler, task_ids: Dict[str, str]):
        """
        Render execution monitoring interface
        
        Args:
            scheduler: execution scheduler instance
            task_ids: dictionary mapping strategy names to task IDs
        """
        st.header("🔄 Execution Monitor")
        
        if not scheduler or not task_ids:
            st.info("No active executions to monitor")
            return
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        
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

        # Task logs storage
        if 'task_logs' not in st.session_state:
            st.session_state.task_logs = {}
        
        self._render_execution_status(scheduler, task_ids)

        if auto_refresh:
            time.sleep(5)
            st.rerun()
    
    def _render_execution_status(self, scheduler, task_ids: Dict[str, str]):
        """Render current execution status with logs"""
        try:
            # Get execution statistics
            stats = scheduler.get_execution_statistics()
            status_dict = scheduler.get_execution_status()
            
            # Display overall statistics
            self._render_statistics_cards(stats)
            
            # Display progress bar
            self._render_progress_bar(stats)
            
            # Display individual task status with logs
            self._render_task_status_table_with_logs(task_ids, status_dict, scheduler)
            
            # Display execution timeline
            self._render_execution_timeline(task_ids, scheduler)
            
        except Exception as e:
            st.error(f"Error updating execution status: {str(e)}")
            ErrorHandler.log_error(f"Execution status update error: {str(e)}")
    
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
    
    def _update_logs_from_queue(self, task_id_to_strategy_map: Dict[str, str]):
        """Drain the log queue and update the session state for logs."""
        from .scheduler_singleton import get_log_queue
        import queue

        log_queue = get_log_queue()
        while not log_queue.empty():
            try:
                task_id, log_line = log_queue.get_nowait()
                strategy_name = task_id_to_strategy_map.get(task_id)
                if strategy_name:
                    if strategy_name not in st.session_state.task_logs:
                        st.session_state.task_logs[strategy_name] = []
                    st.session_state.task_logs[strategy_name].append(log_line)
            except queue.Empty:
                break

    def _render_task_status_table_with_logs(self, 
                                           task_ids: Dict[str, str], 
                                           status_dict: Dict[str, ExecutionStatus],
                                           scheduler):
        """Render task status table with real-time logs"""
        st.subheader("📋 Task Status and Logs")
        
        # Create a reverse map from task_id to strategy name for the log updater
        task_id_to_strategy_map = {v: k for k, v in task_ids.items()}
        self._update_logs_from_queue(task_id_to_strategy_map)

        # Create status data
        status_data = []
        
        for strategy, task_id in task_ids.items():
            status = status_dict.get(task_id, ExecutionStatus.IDLE)
            metadata = None
            if hasattr(scheduler, 'get_task_info'):
                task_info = scheduler.get_task_info(task_id)
                if task_info:
                    metadata = {
                        'start_time': task_info.started_at,
                        'end_time': task_info.completed_at
                    }
            
            # Calculate duration
            duration = "N/A"
            if metadata and metadata.get('start_time'):
                start_time = metadata['start_time']
                if status.value == 'running':
                    duration = str(datetime.now() - start_time).split('.')[0]
                elif metadata.get('end_time'):
                    duration = str(metadata['end_time'] - start_time).split('.')[0]
            
            status_data.append({
                'Strategy': strategy,
                'Status': status.value.title(),
                'Duration': duration,
                'Task ID': task_id[:8] + "..."  # Shortened ID
            })
        
        # Display as DataFrame
        if status_data:
            df = pd.DataFrame(status_data)
            
            def style_status(val):
                val_lower = val.lower()
                if val_lower == 'running':
                    return 'background-color: #fff3cd; color: #856404'
                elif val_lower == 'completed':
                    return 'background-color: #d4edda; color: #155724'
                elif val_lower == 'failed':
                    return 'background-color: #f8d7da; color: #721c24'
                elif val_lower == 'stopped' or val_lower == 'cancelled':
                    return 'background-color: #e2e3e5; color: #383d41'
                return ''
            
            styled_df = df.style.map(style_status, subset=['Status'])
            st.dataframe(styled_df, width='stretch')
            
            # Display logs for running tasks
            st.subheader("📝 Real-time Task Logs")
            
            if task_ids:
                tab_names = list(task_ids.keys())
                tabs = st.tabs(tab_names)
                
                for i, (strategy, task_id) in enumerate(task_ids.items()):
                    with tabs[i]:
                        self._render_strategy_logs(strategy, task_id, status_dict.get(task_id, ExecutionStatus.IDLE))
    
    def _render_strategy_logs(self, strategy: str, task_id: str, status: ExecutionStatus):
        """Render logs for a specific strategy from session state."""
        if strategy not in st.session_state.task_logs:
            st.session_state.task_logs[strategy] = []

        if st.session_state.task_logs[strategy]:
            log_text = "\n".join(st.session_state.task_logs[strategy][-200:])  # Last 200 lines
            st.text_area(
                "Recent Logs",
                value=log_text,
                height=300,
                disabled=True,
                key=f"log_area_{strategy}"
            )
        else:
            st.info("No logs available yet. Waiting for task to start...")
    
    def _render_execution_timeline(self, task_ids: Dict[str, str], scheduler):
        """Render execution timeline chart"""
        try:
            st.subheader("📈 Execution Timeline")
            
            # Get task metadata
            timeline_data = []
            
            for strategy, task_id in task_ids.items():
                # Use hasattr to check if scheduler has get_task_metadata method
                metadata = None
                if hasattr(scheduler, 'get_task_metadata'):
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
            ErrorHandler.log_error(f"Timeline creation error: {str(e)}")
    
    def add_task_log(self, strategy: str, log_message: str):
        """
        Add a log message for a specific task
        
        Args:
            strategy: strategy name
            log_message: log message to add
        """
        if strategy not in st.session_state.task_logs:
            st.session_state.task_logs[strategy] = []
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {log_message}"
        st.session_state.task_logs[strategy].append(formatted_message)
        
        # Keep only last 1000 log entries to prevent memory issues
        if len(st.session_state.task_logs[strategy]) > 1000:
            st.session_state.task_logs[strategy] = st.session_state.task_logs[strategy][-1000:]
    
    def clear_task_logs(self, strategy: str = None):
        """
        Clear logs for a specific task or all tasks
        
        Args:
            strategy: strategy name (optional, if None clears all logs)
        """
        if strategy:
            if strategy in st.session_state.task_logs:
                st.session_state.task_logs[strategy] = []
        else:
            st.session_state.task_logs = {}
