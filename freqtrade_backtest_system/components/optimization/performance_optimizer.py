"""
System performance optimization components
"""
import gc
import psutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import pickle
import gzip
import json
from pathlib import Path

from utils.error_handling import ErrorHandler, error_handler
from utils.data_models import BacktestResult

@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_usage: float
    active_threads: int
    cache_hit_rate: float
    execution_time: float
    timestamp: datetime

class MemoryOptimizer:
    """Memory usage optimization"""
    
    def __init__(self, max_memory_usage: float = 0.8):
        """
        Initialize memory optimizer
        Args:
            max_memory_usage: maximum memory usage threshold (0.0-1.0)
        """
        self.max_memory_usage = max_memory_usage
        self.memory_monitor = MemoryMonitor()
    
    @error_handler(Exception, show_error=True)
    def optimize_memory_usage(self):
        """Optimize memory usage"""
        current_usage = self.memory_monitor.get_memory_usage()
        
        if current_usage > self.max_memory_usage:
            ErrorHandler.log_warning(f"High memory usage detected: {current_usage:.1%}")
            
            # Force garbage collection
            collected = gc.collect()
            ErrorHandler.log_info(f"Garbage collection freed {collected} objects")
            
            # Clear caches if available
            self._clear_caches()
            
            # Check memory usage after optimization
            new_usage = self.memory_monitor.get_memory_usage()
            improvement = current_usage - new_usage
            
            if improvement > 0.05:  # 5% improvement
                ErrorHandler.log_info(f"Memory optimization successful: {improvement:.1%} freed")
            else:
                ErrorHandler.log_warning("Memory optimization had minimal effect")
    
    def _clear_caches(self):
        """Clear internal caches"""
        try:
            # Clear any cached data
            if hasattr(self, '_cache'):
                self._cache.clear()
            
            # Force garbage collection again
            gc.collect()
            
        except Exception as e:
            ErrorHandler.log_warning(f"Error clearing caches: {str(e)}")
    
    def get_memory_recommendations(self) -> List[str]:
        """Get memory optimization recommendations"""
        recommendations = []
        
        usage = self.memory_monitor.get_memory_usage()
        available = self.memory_monitor.get_available_memory()
        
        if usage > 0.8:
            recommendations.append("High memory usage - consider reducing concurrent executions")
        
        if available < 1024:  # Less than 1GB available
            recommendations.append("Low available memory - close unnecessary applications")
        
        if usage > 0.9:
            recommendations.append("Critical memory usage - system may become unstable")
        
        return recommendations

class ConcurrencyOptimizer:
    """Concurrency and parallel execution optimization"""
    
    def __init__(self):
        """Initialize concurrency optimizer"""
        self.cpu_count = psutil.cpu_count()
        self.optimal_workers = self._calculate_optimal_workers()
        self.performance_history = []
    
    def _calculate_optimal_workers(self) -> int:
        """Calculate optimal number of worker threads"""
        # Base on CPU count and system resources
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative approach: use 75% of CPU cores
        cpu_workers = max(1, int(self.cpu_count * 0.75))
        
        # Memory-based limit: assume each worker needs ~500MB
        memory_workers = max(1, int(memory_gb / 0.5))
        
        # Use the minimum to avoid resource exhaustion
        optimal = min(cpu_workers, memory_workers, 8)  # Cap at 8 workers
        
        ErrorHandler.log_info(f"Calculated optimal workers: {optimal} (CPU: {cpu_workers}, Memory: {memory_workers})")
        return optimal
    
    @error_handler(Exception, show_error=True)
    def optimize_execution_batch(self, 
                                tasks: List[Callable],
                                max_workers: int = None) -> List[Any]:
        """
        Optimize batch execution of tasks
        Args:
            tasks: list of callable tasks
            max_workers: maximum number of workers (None for auto)
        Returns:
            list of task results
        """
        if not tasks:
            return []
        
        workers = max_workers or self.optimal_workers
        workers = min(workers, len(tasks))  # Don't use more workers than tasks
        
        ErrorHandler.log_info(f"Executing {len(tasks)} tasks with {workers} workers")
        
        start_time = time.time()
        results = []
        
        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all tasks
                future_to_task = {executor.submit(task): i for i, task in enumerate(tasks)}
                
                # Collect results as they complete
                for future in as_completed(future_to_task):
                    task_index = future_to_task[future]
                    try:
                        result = future.result()
                        results.append((task_index, result))
                    except Exception as e:
                        ErrorHandler.log_error(f"Task {task_index} failed: {str(e)}")
                        results.append((task_index, None))
            
            # Sort results by original task order
            results.sort(key=lambda x: x[0])
            execution_time = time.time() - start_time
            
            # Record performance metrics
            self._record_performance(len(tasks), workers, execution_time)
            
            ErrorHandler.log_info(f"Batch execution completed in {execution_time:.2f}s")
            return [result[1] for result in results]
            
        except Exception as e:
            ErrorHandler.log_error(f"Batch execution failed: {str(e)}")
            raise
    
    def _record_performance(self, task_count: int, workers: int, execution_time: float):
        """Record performance metrics for future optimization"""
        metric = {
            'task_count': task_count,
            'workers': workers,
            'execution_time': execution_time,
            'throughput': task_count / execution_time,
            'timestamp': datetime.now()
        }
        
        self.performance_history.append(metric)
        
        # Keep only recent history (last 100 executions)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    def get_performance_recommendations(self) -> Dict[str, Any]:
        """Get performance optimization recommendations"""
        if not self.performance_history:
            return {"message": "No performance history available"}
        
        # Analyze recent performance
        recent_metrics = self.performance_history[-10:]
        avg_throughput = sum(m['throughput'] for m in recent_metrics) / len(recent_metrics)
        
        recommendations = {
            'current_optimal_workers': self.optimal_workers,
            'average_throughput': avg_throughput,
            'recommendations': []
        }
        
        # Analyze worker efficiency
        worker_performance = {}
        for metric in recent_metrics:
            workers = metric['workers']
            if workers not in worker_performance:
                worker_performance[workers] = []
            worker_performance[workers].append(metric['throughput'])
        
        # Find best performing worker count
        best_workers = None
        best_throughput = 0
        
        for workers, throughputs in worker_performance.items():
            avg_throughput = sum(throughputs) / len(throughputs)
            if avg_throughput > best_throughput:
                best_throughput = avg_throughput
                best_workers = workers
        
        if best_workers and best_workers != self.optimal_workers:
            recommendations['recommendations'].append(
                f"Consider using {best_workers} workers instead of {self.optimal_workers} for better throughput"
            )
        
        return recommendations

class CacheManager:
    """Intelligent caching system"""
    
    def __init__(self, cache_dir: str = "cache", max_cache_size_mb: int = 500):
        """
        Initialize cache manager
        Args:
            cache_dir: directory for cache files
            max_cache_size_mb: maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convert to bytes
        self.cache_stats = {'hits': 0, 'misses': 0}
        self._memory_cache = {}
    
    @error_handler(Exception, show_error=True)
    def get(self, key: str, default=None) -> Any:
        """
        Get item from cache
        Args:
            key: cache key
            default: default value if not found
        Returns:
            cached value or default
        """
        # Try memory cache first
        if key in self._memory_cache:
            self.cache_stats['hits'] += 1
            return self._memory_cache[key]
        
        # Try disk cache
        cache_file = self.cache_dir / f"{key}.cache"
        if cache_file.exists():
            try:
                with gzip.open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                # Add to memory cache for faster access
                self._memory_cache[key] = data
                self.cache_stats['hits'] += 1
                return data
                
            except Exception as e:
                ErrorHandler.log_warning(f"Error reading cache file {key}: {str(e)}")
                # Remove corrupted cache file
                cache_file.unlink(missing_ok=True)
        
        self.cache_stats['misses'] += 1
        return default
    
    @error_handler(Exception, show_error=True)
    def set(self, key: str, value: Any, ttl_hours: int = 24):
        """
        Set item in cache
        Args:
            key: cache key
            value: value to cache
            ttl_hours: time to live in hours
        """
        # Add to memory cache
        self._memory_cache[key] = value
        
        # Save to disk cache
        cache_file = self.cache_dir / f"{key}.cache"
        try:
            cache_data = {
                'value': value,
                'created': datetime.now(),
                'ttl_hours': ttl_hours
            }
            
            with gzip.open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            # Clean up old cache files if needed
            self._cleanup_cache()
            
        except Exception as e:
            ErrorHandler.log_warning(f"Error writing cache file {key}: {str(e)}")
    
    def _cleanup_cache(self):
        """Clean up old and oversized cache files"""
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            
            # Remove expired files
            now = datetime.now()
            for cache_file in cache_files[:]:
                try:
                    with gzip.open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    created = data.get('created', now)
                    ttl_hours = data.get('ttl_hours', 24)
                    
                    if now - created > timedelta(hours=ttl_hours):
                        cache_file.unlink()
                        cache_files.remove(cache_file)
                        
                except Exception:
                    # Remove corrupted files
                    cache_file.unlink(missing_ok=True)
                    if cache_file in cache_files:
                        cache_files.remove(cache_file)
            
            # Check total cache size
            total_size = sum(f.stat().st_size for f in cache_files)
            
            if total_size > self.max_cache_size:
                # Remove oldest files first
                cache_files.sort(key=lambda f: f.stat().st_mtime)
                
                while total_size > self.max_cache_size and cache_files:
                    oldest_file = cache_files.pop(0)
                    file_size = oldest_file.stat().st_size
                    oldest_file.unlink()
                    total_size -= file_size
                    
                    ErrorHandler.log_info(f"Removed old cache file: {oldest_file.name}")
            
        except Exception as e:
            ErrorHandler.log_warning(f"Error during cache cleanup: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        # Calculate cache size
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'cache_files': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'memory_cache_items': len(self._memory_cache)
        }
    
    def clear_cache(self):
        """Clear all cache"""
        # Clear memory cache
        self._memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
        
        # Reset stats
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        ErrorHandler.log_info("Cache cleared")

class MemoryMonitor:
    """System memory monitoring"""
    
    def __init__(self):
        """Initialize memory monitor"""
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage as percentage"""
        return psutil.virtual_memory().percent / 100.0
    
    def get_available_memory(self) -> float:
        """Get available memory in MB"""
        return psutil.virtual_memory().available / (1024 * 1024)
    
    def get_process_memory(self) -> float:
        """Get current process memory usage in MB"""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get comprehensive memory information"""
        vm = psutil.virtual_memory()
        process_memory = self.get_process_memory()
        
        return {
            'total_mb': vm.total / (1024 * 1024),
            'available_mb': vm.available / (1024 * 1024),
            'used_mb': vm.used / (1024 * 1024),
            'usage_percent': vm.percent,
            'process_memory_mb': process_memory,
            'process_memory_percent': (process_memory / (vm.total / (1024 * 1024))) * 100
        }

class DataCompressor:
    """Data compression utilities"""
    
    @staticmethod
    def compress_backtest_results(results: List[BacktestResult]) -> bytes:
        """Compress backtest results for storage"""
        try:
            # Convert to serializable format
            data = [result.to_dict() for result in results]
            
            # Serialize and compress
            json_data = json.dumps(data, default=str)
            compressed = gzip.compress(json_data.encode('utf-8'))
            
            compression_ratio = len(compressed) / len(json_data.encode('utf-8'))
            ErrorHandler.log_info(f"Data compressed to {compression_ratio:.1%} of original size")
            
            return compressed
            
        except Exception as e:
            ErrorHandler.log_error(f"Error compressing data: {str(e)}")
            raise
    
    @staticmethod
    def decompress_backtest_results(compressed_data: bytes) -> List[Dict[str, Any]]:
        """Decompress backtest results"""
        try:
            # Decompress and deserialize
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            data = json.loads(json_data)
            
            return data
            
        except Exception as e:
            ErrorHandler.log_error(f"Error decompressing data: {str(e)}")
            raise

class PerformanceProfiler:
    """Performance profiling and monitoring"""
    
    def __init__(self):
        """Initialize performance profiler"""
        self.metrics_history = []
        self.monitoring_active = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval_seconds: int = 5):
        """Start performance monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        
        ErrorHandler.log_info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        ErrorHandler.log_info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval_seconds: int):
        """Performance monitoring loop"""
        memory_monitor = MemoryMonitor()
        
        while self.monitoring_active:
            try:
                # Collect metrics
                cpu_usage = psutil.cpu_percent()
                memory_info = memory_monitor.get_memory_info()
                disk_usage = psutil.disk_usage('.').percent
                active_threads = threading.active_count()
                
                metrics = PerformanceMetrics(
                    cpu_usage=cpu_usage,
                    memory_usage=memory_info['usage_percent'],
                    memory_available=memory_info['available_mb'],
                    disk_usage=disk_usage,
                    active_threads=active_threads,
                    cache_hit_rate=0.0,  # Will be updated by cache manager
                    execution_time=0.0,  # Will be updated by specific operations
                    timestamp=datetime.now()
                )
                
                self.metrics_history.append(metrics)
                
                # Keep only recent history (last 1000 measurements)
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                ErrorHandler.log_warning(f"Error in performance monitoring: {str(e)}")
                time.sleep(interval_seconds)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, float]:
        """Get performance metrics summary"""
        if not self.metrics_history:
            return {}
        
        # Filter recent metrics
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        return {
            'avg_cpu_usage': sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            'max_cpu_usage': max(m.cpu_usage for m in recent_metrics),
            'avg_memory_usage': sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            'max_memory_usage': max(m.memory_usage for m in recent_metrics),
            'min_memory_available': min(m.memory_available for m in recent_metrics),
            'avg_active_threads': sum(m.active_threads for m in recent_metrics) / len(recent_metrics),
            'max_active_threads': max(m.active_threads for m in recent_metrics)
        }