"""
Error handling and exception management module
"""
import streamlit as st
import logging
import traceback
from typing import Optional, Any, Callable
from functools import wraps
from pathlib import Path
from datetime import datetime

# Configure logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'app.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BacktestSystemError(Exception):
    """Base exception class for backtest system"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now()

class StrategyError(BacktestSystemError):
    """Strategy related errors"""
    pass

class ConfigError(BacktestSystemError):
    """Configuration related errors"""
    pass

class ExecutionError(BacktestSystemError):
    """Execution related errors"""
    pass

class DataError(BacktestSystemError):
    """Data related errors"""
    pass

class ValidationError(BacktestSystemError):
    """Validation related errors"""
    pass

class ErrorHandler:
    """Error handler"""
    
    @staticmethod
    def setup_logging():
        """Setup logging system"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Ensure log file exists
        log_file = log_dir / "app.log"
        if not log_file.exists():
            log_file.touch()
    
    @staticmethod
    def handle_application_error(error: Exception):
        """Handle application level errors"""
        error_msg = f"Application error: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        st.error("🚨 Application encountered an error")
        
        with st.expander("Error Details", expanded=False):
            st.code(f"""
Error Type: {type(error).__name__}
Error Message: {str(error)}
Occurred At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Stack Trace:
{traceback.format_exc()}
            """)
        
        st.info("💡 Suggestion: Please check configuration and input parameters, or contact technical support")
    
    @staticmethod
    def handle_strategy_error(strategy_name: str, error: Exception) -> dict:
        """Handle strategy related errors"""
        error_msg = f"Strategy {strategy_name} processing failed: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        st.error(f"❌ Strategy **{strategy_name}** processing failed")
        st.warning(f"Error message: {str(error)}")
        
        return {
            'strategy_name': strategy_name,
            'error': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
    
    @staticmethod
    def handle_backtest_error(strategy_name: str, error: Exception) -> dict:
        """Handle backtest execution errors"""
        error_msg = f"Strategy {strategy_name} backtest failed: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        st.error(f"🔥 Strategy **{strategy_name}** backtest failed")
        
        # Provide different suggestions based on error type
        if "freqtrade" in str(error).lower():
            st.info("💡 Suggestion: Please check if freqtrade is correctly installed and configured")
        elif "config" in str(error).lower():
            st.info("💡 Suggestion: Please check backtest configuration parameters")
        elif "data" in str(error).lower():
            st.info("💡 Suggestion: Please check if historical data is available")
        else:
            st.info("💡 Suggestion: Please check strategy files and system environment")
        
        return {
            'strategy_name': strategy_name,
            'error': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'metrics': {},
            'trades': []
        }
    
    @staticmethod
    def handle_config_error(error: Exception):
        """Handle configuration errors"""
        error_msg = f"Configuration error: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        st.error("⚙️ Configuration parameter error")
        st.warning(f"Error message: {str(error)}")
        
        # Provide configuration suggestions
        if "date" in str(error).lower():
            st.info("💡 Suggestion: Please check date settings, ensure start date is earlier than end date")
        elif "balance" in str(error).lower():
            st.info("💡 Suggestion: Please check balance settings, ensure initial balance is greater than 0")
        elif "timeframe" in str(error).lower():
            st.info("💡 Suggestion: Please select a valid timeframe")
        else:
            st.info("💡 Suggestion: Please check all configuration parameters meet requirements")
    
    @staticmethod
    def handle_data_error(error: Exception):
        """Handle data related errors"""
        error_msg = f"Data error: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        st.error("📊 Data processing error")
        st.warning(f"Error message: {str(error)}")
        st.info("💡 Suggestion: Please check data file format and integrity")
    
    @staticmethod
    def handle_file_error(file_path: Path, error: Exception):
        """Handle file operation errors"""
        error_msg = f"File operation error {file_path}: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        st.error(f"📁 File operation failed: {file_path.name}")
        st.warning(f"Error message: {str(error)}")
        
        if "permission" in str(error).lower():
            st.info("💡 Suggestion: Please check file permissions")
        elif "not found" in str(error).lower():
            st.info("💡 Suggestion: Please check if file path is correct")
        else:
            st.info("💡 Suggestion: Please check if file exists and is accessible")
    
    @staticmethod
    def handle_validation_error(field_name: str, error: Exception):
        """Handle validation errors"""
        error_msg = f"Validation error {field_name}: {str(error)}"
        logger.warning(error_msg)
        
        st.warning(f"⚠️ Parameter validation failed: {field_name}")
        st.info(f"Error message: {str(error)}")
    
    @staticmethod
    def log_info(message: str):
        """Log info message"""
        logger.info(message)
    
    @staticmethod
    def log_warning(message: str):
        """Log warning message"""
        logger.warning(message)
    
    @staticmethod
    def log_error(message: str, exc_info: bool = False):
        """Log error message"""
        logger.error(message, exc_info=exc_info)

def error_handler(error_type: type = Exception, 
                 show_error: bool = True, 
                 return_default: Any = None):
    """Error handling decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                if show_error:
                    if isinstance(e, StrategyError):
                        ErrorHandler.handle_strategy_error("Unknown", e)
                    elif isinstance(e, ConfigError):
                        ErrorHandler.handle_config_error(e)
                    elif isinstance(e, DataError):
                        ErrorHandler.handle_data_error(e)
                    else:
                        ErrorHandler.handle_application_error(e)
                
                return return_default
            except Exception as e:
                ErrorHandler.handle_application_error(e)
                return return_default
        
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """Safe execution function, returns (success_flag, result)"""
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        ErrorHandler.log_error(f"Safe execution failed: {str(e)}", exc_info=True)
        return False, str(e)

def validate_config(config: dict, required_fields: list) -> bool:
    """Validate configuration parameters"""
    try:
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Missing required field: {field}")
            
            if config[field] is None:
                raise ValidationError(f"Field cannot be empty: {field}")
        
        return True
    
    except ValidationError as e:
        ErrorHandler.handle_validation_error("config", e)
        return False

def validate_file_path(file_path: Path, must_exist: bool = True) -> bool:
    """Validate file path"""
    try:
        if must_exist and not file_path.exists():
            raise ValidationError(f"File does not exist: {file_path}")
        
        if must_exist and not file_path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        
        return True
    
    except ValidationError as e:
        ErrorHandler.handle_validation_error(str(file_path), e)
        return False

class ErrorRecoveryManager:
    """Error recovery and retry mechanism"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize error recovery manager
        Args:
            max_retries: maximum number of retries
            retry_delay: delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_history = []
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """
        Execute function with retry mechanism
        Args:
            func: function to execute
            *args: function arguments
            **kwargs: function keyword arguments
        Returns:
            tuple of (success, result)
        """
        import time
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    ErrorHandler.log_info(f"Function succeeded on attempt {attempt + 1}")
                return True, result
                
            except Exception as e:
                last_error = e
                self.error_history.append({
                    'function': func.__name__,
                    'attempt': attempt + 1,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
                
                if attempt < self.max_retries:
                    ErrorHandler.log_warning(f"Attempt {attempt + 1} failed, retrying in {self.retry_delay}s: {str(e)}")
                    time.sleep(self.retry_delay)
                else:
                    ErrorHandler.log_error(f"All {self.max_retries + 1} attempts failed: {str(e)}")
        
        return False, str(last_error)
    
    def get_error_statistics(self) -> dict:
        """Get error statistics"""
        if not self.error_history:
            return {}
        
        error_counts = {}
        for error_record in self.error_history:
            func_name = error_record['function']
            if func_name not in error_counts:
                error_counts[func_name] = 0
            error_counts[func_name] += 1
        
        return {
            'total_errors': len(self.error_history),
            'error_by_function': error_counts,
            'recent_errors': self.error_history[-10:] if len(self.error_history) > 10 else self.error_history
        }

class SystemHealthChecker:
    """System health monitoring and diagnostics"""
    
    def __init__(self):
        """Initialize health checker"""
        self.health_checks = []
        self.last_check_time = None
        self.health_status = "unknown"
    
    def add_health_check(self, name: str, check_func: Callable) -> None:
        """Add a health check function"""
        self.health_checks.append({
            'name': name,
            'function': check_func
        })
    
    def run_health_checks(self) -> dict:
        """Run all health checks"""
        results = {
            'overall_status': 'healthy',
            'checks': [],
            'timestamp': datetime.now(),
            'issues': []
        }
        
        for check in self.health_checks:
            try:
                check_result = check['function']()
                status = 'healthy' if check_result else 'unhealthy'
                
                results['checks'].append({
                    'name': check['name'],
                    'status': status,
                    'result': check_result
                })
                
                if not check_result:
                    results['overall_status'] = 'unhealthy'
                    results['issues'].append(f"Health check failed: {check['name']}")
                    
            except Exception as e:
                results['checks'].append({
                    'name': check['name'],
                    'status': 'error',
                    'error': str(e)
                })
                results['overall_status'] = 'unhealthy'
                results['issues'].append(f"Health check error in {check['name']}: {str(e)}")
        
        self.last_check_time = results['timestamp']
        self.health_status = results['overall_status']
        
        return results
    
    def get_system_diagnostics(self) -> dict:
        """Get comprehensive system diagnostics"""
        import psutil
        import sys
        
        diagnostics = {
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_usage': psutil.disk_usage('.').percent
            },
            'process_info': {
                'pid': psutil.Process().pid,
                'memory_usage': psutil.Process().memory_info().rss,
                'cpu_percent': psutil.Process().cpu_percent(),
                'threads': psutil.Process().num_threads()
            },
            'health_status': self.health_status,
            'last_check': self.last_check_time
        }
        
        return diagnostics

class ErrorReportGenerator:
    """Generate comprehensive error reports"""
    
    def __init__(self):
        """Initialize error report generator"""
        self.report_dir = Path("error_reports")
        self.report_dir.mkdir(exist_ok=True)
    
    def generate_error_report(self, error: Exception, context: dict = None) -> Path:
        """
        Generate detailed error report
        Args:
            error: the exception that occurred
            context: additional context information
        Returns:
            path to generated report file
        """
        import json
        
        timestamp = datetime.now()
        report_filename = f"error_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.report_dir / report_filename
        
        # Collect system information
        health_checker = SystemHealthChecker()
        system_diagnostics = health_checker.get_system_diagnostics()
        
        # Build error report
        report_data = {
            'error_info': {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc(),
                'timestamp': timestamp.isoformat()
            },
            'context': context or {},
            'system_diagnostics': system_diagnostics,
            'environment': {
                'working_directory': str(Path.cwd()),
                'python_path': sys.path[:5],  # First 5 paths
                'environment_variables': {
                    k: v for k, v in os.environ.items() 
                    if k.startswith(('FREQTRADE_', 'STREAMLIT_', 'PYTHON'))
                }
            }
        }
        
        # Save report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        ErrorHandler.log_info(f"Error report generated: {report_path}")
        return report_path
    
    def get_recent_reports(self, limit: int = 10) -> list:
        """Get recent error reports"""
        reports = []
        
        for report_file in sorted(self.report_dir.glob("error_report_*.json"), reverse=True):
            if len(reports) >= limit:
                break
                
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                reports.append({
                    'filename': report_file.name,
                    'path': str(report_file),
                    'timestamp': report_data['error_info']['timestamp'],
                    'error_type': report_data['error_info']['type'],
                    'error_message': report_data['error_info']['message'][:100] + "..." if len(report_data['error_info']['message']) > 100 else report_data['error_info']['message']
                })
                
            except Exception as e:
                ErrorHandler.log_warning(f"Error reading report file {report_file}: {str(e)}")
        
        return reports

class EnhancedErrorHandler(ErrorHandler):
    """Enhanced error handler with recovery and reporting"""
    
    def __init__(self):
        """Initialize enhanced error handler"""
        self.recovery_manager = ErrorRecoveryManager()
        self.health_checker = SystemHealthChecker()
        self.report_generator = ErrorReportGenerator()
        
        # Add default health checks
        self._setup_default_health_checks()
    
    def _setup_default_health_checks(self):
        """Setup default system health checks"""
        
        def check_memory_usage():
            """Check if memory usage is within acceptable limits"""
            import psutil
            memory_percent = psutil.virtual_memory().percent
            return memory_percent < 90  # Less than 90% memory usage
        
        def check_disk_space():
            """Check if disk space is sufficient"""
            import psutil
            disk_usage = psutil.disk_usage('.').percent
            return disk_usage < 95  # Less than 95% disk usage
        
        def check_log_directory():
            """Check if log directory is accessible"""
            log_dir = Path("logs")
            return log_dir.exists() and log_dir.is_dir()
        
        def check_freqtrade_availability():
            """Check if freqtrade is available"""
            import subprocess
            try:
                result = subprocess.run(['freqtrade', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            except:
                return False
        
        self.health_checker.add_health_check("Memory Usage", check_memory_usage)
        self.health_checker.add_health_check("Disk Space", check_disk_space)
        self.health_checker.add_health_check("Log Directory", check_log_directory)
        self.health_checker.add_health_check("Freqtrade Availability", check_freqtrade_availability)
    
    def handle_critical_error(self, error: Exception, context: dict = None):
        """Handle critical system errors with full reporting"""
        # Generate error report
        report_path = self.report_generator.generate_error_report(error, context)
        
        # Run health checks
        health_results = self.health_checker.run_health_checks()
        
        # Log critical error
        ErrorHandler.log_error(f"Critical error occurred: {str(error)}", exc_info=True)
        
        # Display error in Streamlit
        st.error("🚨 Critical System Error")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Error Information:**")
            st.write(f"- Type: {type(error).__name__}")
            st.write(f"- Message: {str(error)}")
            st.write(f"- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"- Report: {report_path.name}")
        
        with col2:
            st.write("**System Health:**")
            if health_results['overall_status'] == 'healthy':
                st.success("✅ System health: Good")
            else:
                st.error("❌ System health: Issues detected")
                for issue in health_results['issues']:
                    st.warning(f"⚠️ {issue}")
        
        # Provide recovery suggestions
        st.write("**Recovery Suggestions:**")
        recovery_suggestions = self._get_recovery_suggestions(error, health_results)
        for suggestion in recovery_suggestions:
            st.info(f"💡 {suggestion}")
        
        # Offer to download error report
        if st.button("📥 Download Error Report"):
            with open(report_path, 'r', encoding='utf-8') as f:
                st.download_button(
                    label="Download Report",
                    data=f.read(),
                    file_name=report_path.name,
                    mime="application/json"
                )
    
    def _get_recovery_suggestions(self, error: Exception, health_results: dict) -> list:
        """Get recovery suggestions based on error and system health"""
        suggestions = []
        
        # Error-specific suggestions
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if "memory" in error_message or "ram" in error_message:
            suggestions.append("Close unnecessary applications to free up memory")
            suggestions.append("Reduce the number of concurrent backtest executions")
        
        if "disk" in error_message or "space" in error_message:
            suggestions.append("Free up disk space by cleaning temporary files")
            suggestions.append("Check if log files are taking up too much space")
        
        if "permission" in error_message:
            suggestions.append("Check file and directory permissions")
            suggestions.append("Try running the application with appropriate privileges")
        
        if "freqtrade" in error_message:
            suggestions.append("Verify freqtrade installation and configuration")
            suggestions.append("Check if freqtrade is in the system PATH")
        
        # Health-based suggestions
        if health_results['overall_status'] != 'healthy':
            for issue in health_results['issues']:
                if "memory" in issue.lower():
                    suggestions.append("System memory usage is high - consider restarting the application")
                elif "disk" in issue.lower():
                    suggestions.append("Disk space is low - clean up unnecessary files")
                elif "freqtrade" in issue.lower():
                    suggestions.append("Freqtrade is not available - check installation")
        
        # Generic suggestions
        if not suggestions:
            suggestions.extend([
                "Try restarting the application",
                "Check system resources and close unnecessary programs",
                "Verify all configuration settings",
                "Contact technical support if the problem persists"
            ])
        
        return suggestions
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        health_results = self.health_checker.run_health_checks()
        error_stats = self.recovery_manager.get_error_statistics()
        recent_reports = self.report_generator.get_recent_reports(5)
        
        return {
            'health': health_results,
            'errors': error_stats,
            'recent_reports': recent_reports,
            'timestamp': datetime.now()
        }

# Create global enhanced error handler instance
enhanced_error_handler = EnhancedErrorHandler()

# Enhanced error handling decorators
def critical_error_handler(func: Callable) -> Callable:
    """Decorator for critical error handling with full reporting"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'function': func.__name__,
                'args': str(args)[:200],  # Limit length
                'kwargs': str(kwargs)[:200]  # Limit length
            }
            enhanced_error_handler.handle_critical_error(e, context)
            return None
    return wrapper

def retry_on_failure(max_retries: int = 3, retry_delay: float = 1.0):
    """Decorator for automatic retry on failure"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            success, result = enhanced_error_handler.recovery_manager.execute_with_retry(
                func, *args, **kwargs
            )
            if not success:
                raise ExecutionError(f"Function {func.__name__} failed after {max_retries} retries: {result}")
            return result
        return wrapper
    return decorator

# Initialize logging system
ErrorHandler.setup_logging()