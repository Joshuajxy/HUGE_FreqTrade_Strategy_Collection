"""
Serializable execution scheduler for Streamlit session state
"""
import uuid
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from utils.data_models import BacktestConfig, ExecutionStatus
from utils.error_handling import ErrorHandler
from components.execution.task_runner import run_backtest_task
from components.execution.executor_singleton import get_executor

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    """Serializable task information"""
    task_id: str
    strategy_name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, TaskStatus):
                data[key] = value.value
        return data

class SerializableScheduler:
    """Serializable execution scheduler for session state"""
    
    def __init__(self, max_workers: int = 4):
        """Initialize serializable scheduler. This class only holds task data."""
        self.max_workers = max_workers
        self.tasks: Dict[str, TaskInfo] = {}
        self.created_at = datetime.now()
        ErrorHandler.log_info(f"Serializable scheduler data object initialized, max workers: {max_workers}")

    def submit_task(self, strategy_info: 'StrategyInfo', config: BacktestConfig) -> str:
        """Submit a task for execution"""
        from .scheduler_singleton import get_thread_pool_executor # Import here to avoid circular dependencies
        from utils.data_models import StrategyInfo # For type hint

        task_id = str(uuid.uuid4())
        
        # Get the actual thread pool and submit the task runner function
        thread_pool = get_thread_pool_executor()
        future = thread_pool.submit(run_backtest_task, strategy_info, config)
        
        # Add a callback that will update the task's status upon completion
        future.add_done_callback(self._task_done_callback(task_id))

        # Create and store the initial task info
        task_info = TaskInfo(
            task_id=task_id,
            strategy_name=strategy_info.name,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
        )
        
        self.tasks[task_id] = task_info
        self.update_task_status(task_id, TaskStatus.RUNNING)
        ErrorHandler.log_info(f"Task submitted to thread pool: {strategy_info.name} ({task_id})")
        
        return task_id

    def _task_done_callback(self, task_id: str):
        def callback(future):
            try:
                result = future.result()
                self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
            except Exception as e:
                self.update_task_status(task_id, TaskStatus.FAILED, error_message=str(e))
        return callback

    def submit_batch(self, strategies: List['StrategyInfo'], config: BacktestConfig) -> Dict[str, str]:
        """Submit batch of tasks"""
        from utils.data_models import StrategyInfo # For type hint
        task_ids = {}
        
        for strategy_info in strategies:
            task_id = self.submit_task(strategy_info, config)
            task_ids[strategy_info.name] = task_id
        
        ErrorHandler.log_info(f"Batch submitted: {len(strategies)} tasks")
        return task_ids
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          error_message: str = None, result: Any = None):
        """Update task status"""
        if task_id not in self.tasks:
            ErrorHandler.log_warning(f"Task not found: {task_id}")
            return
        
        task = self.tasks[task_id]
        old_status = task.status
        task.status = status
        
        if status == TaskStatus.RUNNING and old_status == TaskStatus.PENDING:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
            
        if error_message:
            task.error_message = error_message
            
        if result:
            task.result = result
        
        ErrorHandler.log_info(f"Task {task_id} status updated: {old_status.value} -> {status.value}")
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        """Get all tasks"""
        return self.tasks.copy()
    
    def get_execution_statistics(self) -> Dict[str, int]:
        """Get execution statistics"""
        stats = {
            'total_tasks': len(self.tasks),
            'pending_tasks': 0,
            'running_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'max_workers': self.max_workers
        }
        
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                stats['pending_tasks'] += 1
            elif task.status == TaskStatus.RUNNING:
                stats['running_tasks'] += 1
            elif task.status == TaskStatus.COMPLETED:
                stats['completed_tasks'] += 1
            elif task.status == TaskStatus.FAILED:
                stats['failed_tasks'] += 1
            elif task.status == TaskStatus.CANCELLED:
                stats['cancelled_tasks'] += 1
        
        return stats
    
    def get_execution_status(self) -> Dict[str, TaskStatus]:
        """Get execution status for all tasks"""
        return {task_id: task.status for task_id, task in self.tasks.items()}
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            self.update_task_status(task_id, TaskStatus.CANCELLED)
            return True
        
        return False
    
    def clear_completed_tasks(self):
        """Clear completed tasks"""
        completed_tasks = [
            task_id for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in completed_tasks:
            del self.tasks[task_id]
        
        ErrorHandler.log_info(f"Cleared {len(completed_tasks)} completed tasks")
    
    def get_task_result(self, task_id: str) -> Any:
        """Get task result"""
        if task_id in self.tasks:
            return self.tasks[task_id].result
        return None
    
    def is_task_completed(self, task_id: str) -> bool:
        """Check if task is completed"""
        if task_id in self.tasks:
            return self.tasks[task_id].status in [
                TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED
            ]
        return False
    
    def get_running_tasks(self) -> List[str]:
        """Get list of running task IDs"""
        return [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.RUNNING
        ]
    
    def get_pending_tasks(self) -> List[str]:
        """Get list of pending task IDs"""
        return [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.PENDING
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduler to dictionary for serialization"""
        return {
            'max_workers': self.max_workers,
            'created_at': self.created_at.isoformat(),
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SerializableScheduler':
        """Create scheduler from dictionary"""
        scheduler = cls(max_workers=data['max_workers'])
        scheduler.created_at = datetime.fromisoformat(data['created_at'])
        
        # Restore tasks
        for task_id, task_data in data['tasks'].items():
            task_info = TaskInfo(
                task_id=task_data['task_id'],
                strategy_name=task_data['strategy_name'],
                status=TaskStatus(task_data['status']),
                created_at=datetime.fromisoformat(task_data['created_at']),
                started_at=datetime.fromisoformat(task_data['started_at']) if task_data['started_at'] else None,
                completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data['completed_at'] else None,
                error_message=task_data['error_message'],
                result=task_data['result']
            )
            scheduler.tasks[task_id] = task_info
        
        return scheduler