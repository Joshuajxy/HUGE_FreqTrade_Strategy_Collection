"""
Parallel execution scheduler
"""
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from queue import Queue

from utils.data_models import BacktestConfig, BacktestResult, ExecutionStatus
from utils.error_handling import ErrorHandler, ExecutionError

class ExecutionScheduler:
    """Parallel execution scheduler"""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize scheduler
        
        Args:
            max_workers: maximum number of parallel worker threads
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, Future] = {}
        self.task_status: Dict[str, ExecutionStatus] = {}
        self.task_results: Dict[str, Any] = {}
        self.task_metadata: Dict[str, Dict[str, Any]] = {}
        self.status_callbacks: List[Callable] = []
        
        # Start status monitoring thread
        self._start_status_monitor()
        
        ErrorHandler.log_info(f"Execution scheduler initialized, max parallel: {max_workers}")
    
    def _start_status_monitor(self):
        """Start status monitoring thread"""
        def monitor():
            while not self._shutdown_event.is_set():
                self._update_task_status()
                time.sleep(1)  # Check every second
        
        self._shutdown_event = threading.Event()
        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()
    
    def _update_task_status(self):
        """Update task status"""
        completed_tasks = []
        
        for task_id, future in self.tasks.items():
            if future.done():
                if future.cancelled():
                    self.task_status[task_id] = ExecutionStatus.STOPPED
                elif future.exception():
                    self.task_status[task_id] = ExecutionStatus.FAILED
                    ErrorHandler.log_error(f"Task {task_id} failed: {future.exception()}")
                else:
                    self.task_status[task_id] = ExecutionStatus.COMPLETED
                    self.task_results[task_id] = future.result()
                
                completed_tasks.append(task_id)
            elif future.running():
                self.task_status[task_id] = ExecutionStatus.RUNNING
        
        # Notify status callbacks
        for callback in self.status_callbacks:
            try:
                callback(self.get_execution_statistics())
            except Exception as e:
                ErrorHandler.log_warning(f"Status callback error: {str(e)}")
    
    def execute_task(self, 
                    task_func: Callable, 
                    *args, 
                    task_name: str = None,
                    **kwargs) -> str:
        """
        Execute a single task
        
        Args:
            task_func: function to execute
            *args: function arguments
            task_name: task name (optional)
            **kwargs: function keyword arguments
            
        Returns:
            task ID
        """
        task_id = str(uuid.uuid4())
        task_name = task_name or f"task_{task_id[:8]}"
        
        try:
            # Submit task to executor
            future = self.executor.submit(task_func, *args, **kwargs)
            
            # Store task information
            self.tasks[task_id] = future
            self.task_status[task_id] = ExecutionStatus.RUNNING
            self.task_metadata[task_id] = {
                'name': task_name,
                'start_time': datetime.now(),
                'args': args,
                'kwargs': kwargs
            }
            
            ErrorHandler.log_info(f"Task submitted: {task_name} (ID: {task_id})")
            return task_id
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to submit task {task_name}: {str(e)}")
            raise ExecutionError(f"Failed to submit task: {str(e)}")
    
    def execute_backtest_batch(self, 
                              strategies: List[str], 
                              config: BacktestConfig,
                              executor_func: Callable) -> Dict[str, str]:
        """
        Execute batch backtest for multiple strategies
        
        Args:
            strategies: list of strategy names
            config: backtest configuration
            executor_func: backtest execution function
            
        Returns:
            dictionary mapping strategy names to task IDs
        """
        task_ids = {}
        
        try:
            ErrorHandler.log_info(f"Starting batch backtest for {len(strategies)} strategies")
            
            for strategy in strategies:
                task_id = self.execute_task(
                    executor_func,
                    strategy,
                    config,
                    task_name=f"backtest_{strategy}"
                )
                task_ids[strategy] = task_id
            
            ErrorHandler.log_info(f"Batch backtest submitted, {len(task_ids)} tasks created")
            return task_ids
        
        except Exception as e:
            ErrorHandler.log_error(f"Batch backtest submission failed: {str(e)}")
            raise ExecutionError(f"Batch backtest submission failed: {str(e)}")
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task
        
        Args:
            task_id: task ID
            
        Returns:
            whether cancellation was successful
        """
        try:
            if task_id in self.tasks:
                future = self.tasks[task_id]
                if future.cancel():
                    self.task_status[task_id] = ExecutionStatus.STOPPED
                    ErrorHandler.log_info(f"Task cancelled: {task_id}")
                    return True
                else:
                    ErrorHandler.log_warning(f"Task cannot be cancelled: {task_id}")
                    return False
            else:
                ErrorHandler.log_warning(f"Task not found: {task_id}")
                return False
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to cancel task {task_id}: {str(e)}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[ExecutionStatus]:
        """
        Get task status
        
        Args:
            task_id: task ID
            
        Returns:
            task status
        """
        return self.task_status.get(task_id)
    
    def get_task_result(self, task_id: str) -> Any:
        """
        Get task result
        
        Args:
            task_id: task ID
            
        Returns:
            task result
        """
        return self.task_results.get(task_id)
    
    def get_execution_status(self) -> Dict[str, ExecutionStatus]:
        """
        Get all task execution status
        
        Returns:
            dictionary mapping task IDs to status
        """
        return self.task_status.copy()
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics
        
        Returns:
            execution statistics dictionary
        """
        total_tasks = len(self.tasks)
        running_tasks = sum(1 for status in self.task_status.values() 
                           if status == ExecutionStatus.RUNNING)
        completed_tasks = sum(1 for status in self.task_status.values() 
                             if status == ExecutionStatus.COMPLETED)
        failed_tasks = sum(1 for status in self.task_status.values() 
                          if status == ExecutionStatus.FAILED)
        stopped_tasks = sum(1 for status in self.task_status.values() 
                           if status == ExecutionStatus.STOPPED)
        
        return {
            'total_tasks': total_tasks,
            'running_tasks': running_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'stopped_tasks': stopped_tasks,
            'max_workers': self.max_workers,
            'active_workers': len([f for f in self.tasks.values() if f.running()])
        }
    
    def wait_for_completion(self, task_ids: List[str] = None, timeout: float = None) -> bool:
        """
        Wait for task completion
        
        Args:
            task_ids: list of task IDs to wait for (all tasks if None)
            timeout: timeout in seconds
            
        Returns:
            whether all tasks completed successfully
        """
        try:
            if task_ids is None:
                futures = list(self.tasks.values())
            else:
                futures = [self.tasks[task_id] for task_id in task_ids if task_id in self.tasks]
            
            if not futures:
                return True
            
            # Wait for completion
            completed = as_completed(futures, timeout=timeout)
            
            success_count = 0
            for future in completed:
                if not future.exception():
                    success_count += 1
            
            return success_count == len(futures)
        
        except Exception as e:
            ErrorHandler.log_error(f"Error waiting for task completion: {str(e)}")
            return False
    
    def clear_completed_tasks(self):
        """Clear completed tasks"""
        completed_task_ids = []
        
        for task_id, status in self.task_status.items():
            if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.STOPPED]:
                completed_task_ids.append(task_id)
        
        for task_id in completed_task_ids:
            self.tasks.pop(task_id, None)
            self.task_status.pop(task_id, None)
            self.task_results.pop(task_id, None)
            self.task_metadata.pop(task_id, None)
        
        ErrorHandler.log_info(f"Cleared {len(completed_task_ids)} completed tasks")
    
    def get_task_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task metadata
        
        Args:
            task_id: task ID
            
        Returns:
            task metadata
        """
        return self.task_metadata.get(task_id)
    
    def add_status_callback(self, callback: Callable):
        """
        Add status change callback
        
        Args:
            callback: callback function
        """
        self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable):
        """
        Remove status change callback
        
        Args:
            callback: callback function
        """
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def get_running_tasks(self) -> List[str]:
        """
        Get list of running task IDs
        
        Returns:
            list of running task IDs
        """
        return [task_id for task_id, status in self.task_status.items() 
                if status == ExecutionStatus.RUNNING]
    
    def get_completed_results(self) -> Dict[str, Any]:
        """
        Get all completed task results
        
        Returns:
            dictionary mapping task IDs to results
        """
        completed_results = {}
        
        for task_id, status in self.task_status.items():
            if status == ExecutionStatus.COMPLETED and task_id in self.task_results:
                completed_results[task_id] = self.task_results[task_id]
        
        return completed_results
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown scheduler
        
        Args:
            wait: whether to wait for running tasks to complete
        """
        try:
            ErrorHandler.log_info("Shutting down execution scheduler...")
            
            # Stop status monitoring
            self._shutdown_event.set()
            
            # Shutdown executor
            self.executor.shutdown(wait=wait)
            
            # Wait for monitor thread
            if hasattr(self, '_monitor_thread'):
                self._monitor_thread.join(timeout=5)
            
            ErrorHandler.log_info("Execution scheduler shutdown completed")
        
        except Exception as e:
            ErrorHandler.log_error(f"Error during scheduler shutdown: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown(wait=True)