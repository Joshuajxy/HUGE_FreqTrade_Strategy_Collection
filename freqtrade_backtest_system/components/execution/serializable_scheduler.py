"""
Serializable execution scheduler for Streamlit session state
"""
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import json

from utils.error_handling import ErrorHandler, error_handler
from utils.data_models import BacktestConfig

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
    result_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, TaskStatus):
                data[key] = value.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskInfo':
        """Create from dictionary"""
        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'started_at', 'completed_at']:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        
        if 'status' in data:
            data['status'] = TaskStatus(data['status'])
        
        return cls(**data)

class SerializableExecutionScheduler:
    """Serializable execution scheduler for Streamlit"""
    
    def __init__(self, max_workers: int = 4):
        """Initialize scheduler"""
        self.max_workers = max_workers
        self.tasks: Dict[str, TaskInfo] = {}
        self.active_tasks: List[str] = []
        self._task_counter = 0
        
        ErrorHandler.log_info(f"Serializable scheduler initialized, max parallel: {max_workers}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduler state to dictionary for serialization"""
        return {
            'max_workers': self.max_workers,
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            'active_tasks': self.active_tasks,
            'task_counter': self._task_counter
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SerializableExecutionScheduler':
        """Create scheduler from dictionary"""
        scheduler = cls(data.get('max_workers', 4))
        scheduler._task_counter = data.get('task_counter', 0)
        scheduler.active_tasks = data.get('active_tasks', [])
        
        # Restore tasks
        for task_id, task_data in data.get('tasks', {}).items():
            scheduler.tasks[task_id] = TaskInfo.from_dict(task_data)
        
        return scheduler
    
    def submit_task(self, strategy_name: str, config: BacktestConfig, 
                   executor_func: Callable = None) -> str:
        """Submit a task for execution"""
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{int(time.time())}"
        
        task = TaskInfo(
            task_id=task_id,
            strategy_name=strategy_name,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        
        # Start task if we have available workers
        if len(self.active_tasks) < self.max_workers:
            self._start_task(task_id, config, executor_func)
        
        ErrorHandler.log_info(f"Task submitted: {task_id} for strategy {strategy_name}")
        return task_id
    
    def _start_task(self, task_id: str, config: BacktestConfig, executor_func: Callable):
        """Start executing a task"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.active_tasks.append(task_id)
        
        # In a real implementation, this would run in a separate thread
        # For now, we'll simulate the execution
        def simulate_execution():
            try:
                time.sleep(2)  # Simulate work
                
                # Simulate successful completion
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result_data = {
                    'strategy_name': task.strategy_name,
                    'success': True,
                    'metrics': {
                        'total_return_pct': 15.5,
                        'win_rate': 65.0,
                        'max_drawdown_pct': -8.2,
                        'sharpe_ratio': 1.25,
                        'total_trades': 150
                    }
                }
                
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)
                
                ErrorHandler.log_info(f"Task completed: {task_id}")
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error_message = str(e)
                
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)
                
                ErrorHandler.log_error(f"Task failed: {task_id} - {str(e)}")
        
        # Start simulation in background thread
        thread = threading.Thread(target=simulate_execution, daemon=True)
        thread.start()
    
    def execute_backtest_batch(self, strategies: List[str], config: BacktestConfig, 
                              executor_func: Callable = None) -> Dict[str, str]:
        """Execute multiple backtest tasks"""
        task_ids = {}
        
        for strategy in strategies:
            task_id = self.submit_task(strategy, config, executor_func)
            task_ids[strategy] = task_id
        
        ErrorHandler.log_info(f"Batch execution started: {len(strategies)} strategies")
        return task_ids
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None
    
    def get_execution_status(self) -> Dict[str, TaskStatus]:
        """Get status of all tasks"""
        return {task_id: task.status for task_id, task in self.tasks.items()}
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                return task.result_data
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)
                
                ErrorHandler.log_info(f"Task cancelled: {task_id}")
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
    
    def get_execution_statistics(self) -> Dict[str, int]:
        """Get execution statistics"""
        stats = {
            'total_tasks': len(self.tasks),
            'pending_tasks': 0,
            'running_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0
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
    
    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed task information"""
        if task_id in self.tasks:
            return self.tasks[task_id].to_dict()
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all task details"""
        return [task.to_dict() for task in self.tasks.values()]