"""
Results storage system using SQLite
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from contextlib import contextmanager

from utils.data_models import BacktestResult, BacktestConfig, PerformanceMetrics, TradeRecord, ComparisonResult
from utils.error_handling import ErrorHandler, DataError, error_handler

class ResultsStorage:
    """Results storage system using SQLite"""
    
    def __init__(self, db_path: str = "data/backtest_results.db"):
        """
        Initialize results storage
        
        Args:
            db_path: SQLite database file path
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        ErrorHandler.log_info(f"Results storage initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create backtest results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_name TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        execution_time REAL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        config_json TEXT NOT NULL,
                        metrics_json TEXT NOT NULL,
                        trades_json TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(strategy_name, timestamp)
                    )
                """)\n                
                # Create comparison results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS comparison_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        comparison_id TEXT NOT NULL UNIQUE,
                        strategies_json TEXT NOT NULL,
                        metrics_comparison_json TEXT NOT NULL,
                        rankings_json TEXT NOT NULL,
                        best_strategy TEXT NOT NULL,
                        comparison_timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_backtest_strategy_timestamp 
                    ON backtest_results(strategy_name, timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_backtest_status 
                    ON backtest_results(status)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_comparison_timestamp 
                    ON comparison_results(comparison_timestamp)
                """)
                
                conn.commit()
                
            ErrorHandler.log_info("Database schema initialized successfully")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to initialize database: {str(e)}")
            raise DataError(f"Failed to initialize database: {str(e)}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @error_handler(DataError, show_error=True)
    def save_backtest_result(self, result: BacktestResult) -> int:
        """
        Save backtest result to database
        
        Args:
            result: backtest result object
            
        Returns:
            result ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Serialize complex objects to JSON
                config_json = json.dumps(result.config.to_dict())
                metrics_json = json.dumps(result.metrics.__dict__)
                trades_json = json.dumps([trade.to_dict() for trade in result.trades])
                
                # Insert or replace result
                cursor.execute("""
                    INSERT OR REPLACE INTO backtest_results 
                    (strategy_name, timestamp, execution_time, status, error_message, 
                     config_json, metrics_json, trades_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.strategy_name,
                    result.timestamp,
                    result.execution_time,
                    result.status.value,
                    result.error_message,
                    config_json,
                    metrics_json,
                    trades_json
                ))
                
                result_id = cursor.lastrowid
                conn.commit()
                
                ErrorHandler.log_info(f"Backtest result saved: {result.strategy_name} (ID: {result_id})")
                return result_id
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to save backtest result: {str(e)}")
            raise DataError(f"Failed to save backtest result: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def load_backtest_result(self, result_id: int) -> Optional[BacktestResult]:
        """
        Load backtest result by ID
        
        Args:
            result_id: result ID
            
        Returns:
            backtest result object
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM backtest_results WHERE id = ?
                """, (result_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._row_to_backtest_result(row)
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to load backtest result {result_id}: {str(e)}")
            raise DataError(f"Failed to load backtest result: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def get_strategy_results(self, 
                           strategy_name: str, 
                           limit: int = 10) -> List[BacktestResult]:
        """
        Get backtest results for a specific strategy
        
        Args:
            strategy_name: strategy name
            limit: maximum number of results to return
            
        Returns:
            list of backtest results
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM backtest_results 
                    WHERE strategy_name = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (strategy_name, limit))
                
                rows = cursor.fetchall()
                return [self._row_to_backtest_result(row) for row in rows]
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get strategy results for {strategy_name}: {str(e)}")
            raise DataError(f"Failed to get strategy results: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def get_recent_results(self, 
                          limit: int = 20, 
                          status_filter: Optional[str] = None) -> List[BacktestResult]:
        """
        Get recent backtest results
        
        Args:
            limit: maximum number of results to return
            status_filter: filter by status (optional)
            
        Returns:
            list of backtest results
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if status_filter:
                    cursor.execute("""
                        SELECT * FROM backtest_results 
                        WHERE status = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (status_filter, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM backtest_results 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,))
                
                rows = cursor.fetchall()
                return [self._row_to_backtest_result(row) for row in rows]
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get recent results: {str(e)}")
            raise DataError(f"Failed to get recent results: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def search_results(self, 
                      strategy_pattern: Optional[str] = None,
                      start_date: Optional[date] = None,
                      end_date: Optional[date] = None,
                      min_return: Optional[float] = None,
                      max_drawdown: Optional[float] = None,
                      limit: int = 50) -> List[BacktestResult]:
        """
        Search backtest results with filters
        
        Args:
            strategy_pattern: strategy name pattern (SQL LIKE)
            start_date: start date filter
            end_date: end date filter
            min_return: minimum return percentage
            max_drawdown: maximum drawdown percentage
            limit: maximum number of results
            
        Returns:
            list of matching backtest results
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic query
                conditions = []
                params = []
                
                if strategy_pattern:
                    conditions.append("strategy_name LIKE ?")
                    params.append(f"%{strategy_pattern}%")
                
                if start_date:
                    conditions.append("DATE(timestamp) >= ?")
                    params.append(start_date.isoformat())
                
                if end_date:
                    conditions.append("DATE(timestamp) <= ?")
                    params.append(end_date.isoformat())
                
                # For performance filters, we need to parse JSON (less efficient)
                base_query = "SELECT * FROM backtest_results"
                
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)
                
                base_query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = self._row_to_backtest_result(row)
                    
                    # Apply performance filters
                    if min_return is not None and result.metrics.total_return_pct < min_return:
                        continue
                    
                    if max_drawdown is not None and abs(result.metrics.max_drawdown_pct) > max_drawdown:
                        continue
                    
                    results.append(result)
                
                return results
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to search results: {str(e)}")
            raise DataError(f"Failed to search results: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def save_comparison_result(self, comparison: ComparisonResult) -> int:
        """
        Save comparison result to database
        
        Args:
            comparison: comparison result object
            
        Returns:
            comparison ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Generate comparison ID
                comparison_id = f"comp_{int(comparison.comparison_timestamp.timestamp())}"
                
                # Serialize complex objects to JSON
                strategies_json = json.dumps(comparison.strategies)
                metrics_json = json.dumps(comparison.metrics_comparison)
                rankings_json = json.dumps(comparison.rankings)
                
                # Insert comparison result
                cursor.execute("""
                    INSERT OR REPLACE INTO comparison_results 
                    (comparison_id, strategies_json, metrics_comparison_json, 
                     rankings_json, best_strategy, comparison_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    comparison_id,
                    strategies_json,
                    metrics_json,
                    rankings_json,
                    comparison.best_strategy,
                    comparison.comparison_timestamp
                ))
                
                result_id = cursor.lastrowid
                conn.commit()
                
                ErrorHandler.log_info(f"Comparison result saved: {comparison_id} (ID: {result_id})")
                return result_id
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to save comparison result: {str(e)}")
            raise DataError(f"Failed to save comparison result: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def get_comparison_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get comparison history
        
        Args:
            limit: maximum number of comparisons to return
            
        Returns:
            list of comparison summaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT comparison_id, strategies_json, best_strategy, 
                           comparison_timestamp, created_at
                    FROM comparison_results 
                    ORDER BY comparison_timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                comparisons = []
                for row in rows:
                    strategies = json.loads(row['strategies_json'])
                    comparisons.append({
                        'comparison_id': row['comparison_id'],
                        'strategies': strategies,
                        'strategy_count': len(strategies),
                        'best_strategy': row['best_strategy'],
                        'comparison_timestamp': datetime.fromisoformat(row['comparison_timestamp']),
                        'created_at': datetime.fromisoformat(row['created_at'])
                    })
                
                return comparisons
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get comparison history: {str(e)}")
            raise DataError(f"Failed to get comparison history: {str(e)}")
    
    def _row_to_backtest_result(self, row: sqlite3.Row) -> BacktestResult:
        """Convert database row to BacktestResult object"""
        try:
            # Parse JSON data
            config_data = json.loads(row['config_json'])
            metrics_data = json.loads(row['metrics_json'])
            trades_data = json.loads(row['trades_json'])
            
            # Reconstruct objects
            config = BacktestConfig.from_dict(config_data)
            metrics = PerformanceMetrics(**metrics_data)
            trades = [TradeRecord.from_dict(trade) for trade in trades_data]
            
            return BacktestResult(
                strategy_name=row['strategy_name'],
                config=config,
                metrics=metrics,
                trades=trades,
                timestamp=datetime.fromisoformat(row['timestamp']),
                execution_time=row['execution_time'],
                error_message=row['error_message'],
                status=row['status']
            )
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to convert row to BacktestResult: {str(e)}")
            raise DataError(f"Failed to convert database row: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def delete_old_results(self, days_old: int = 30) -> int:
        """
        Delete old backtest results
        
        Args:
            days_old: delete results older than this many days
            
        Returns:
            number of deleted results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM backtest_results 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                ErrorHandler.log_info(f"Deleted {deleted_count} old backtest results")
                return deleted_count
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to delete old results: {str(e)}")
            raise DataError(f"Failed to delete old results: {str(e)}")
    
    @error_handler(DataError, show_error=True)
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            storage statistics dictionary
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get backtest results statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_results,
                        COUNT(DISTINCT strategy_name) as unique_strategies,
                        MIN(timestamp) as oldest_result,
                        MAX(timestamp) as newest_result,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_results,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_results
                    FROM backtest_results
                """)
                
                backtest_stats = cursor.fetchone()
                
                # Get comparison results statistics
                cursor.execute("""
                    SELECT COUNT(*) as total_comparisons
                    FROM comparison_results
                """)
                
                comparison_stats = cursor.fetchone()
                
                # Get database file size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    'total_results': backtest_stats['total_results'],
                    'unique_strategies': backtest_stats['unique_strategies'],
                    'successful_results': backtest_stats['successful_results'],
                    'failed_results': backtest_stats['failed_results'],
                    'total_comparisons': comparison_stats['total_comparisons'],
                    'oldest_result': backtest_stats['oldest_result'],
                    'newest_result': backtest_stats['newest_result'],
                    'database_size_mb': db_size / (1024 * 1024),
                    'database_path': str(self.db_path)
                }
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get storage statistics: {str(e)}")
            raise DataError(f"Failed to get storage statistics: {str(e)}")
    
    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create database backup
        
        Args:
            backup_path: backup file path (optional)
            
        Returns:
            backup file path
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.db_path.parent / f"backtest_results_backup_{timestamp}.db"
            
            # Simple file copy for SQLite
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            ErrorHandler.log_info(f"Database backup created: {backup_path}")
            return backup_path
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to backup database: {str(e)}")
            raise DataError(f"Failed to backup database: {str(e)}")
    
    def vacuum_database(self):
        """Vacuum database to reclaim space"""
        try:
            with self._get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
            
            ErrorHandler.log_info("Database vacuumed successfully")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to vacuum database: {str(e)}")
            raise DataError(f"Failed to vacuum database: {str(e)}")