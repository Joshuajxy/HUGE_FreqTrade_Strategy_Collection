"""
Result parser
"""
import re
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from utils.data_models import BacktestResult, BacktestConfig, PerformanceMetrics, TradeRecord
from utils.error_handling import ErrorHandler, DataError

class ResultParser:
    """Result parser"""
    
    def __init__(self):
        """Initialize parser"""
        # Regular expression patterns for performance metrics
        
        self.metric_patterns = {
            'total_return': r'Total profit USDT\s+\|\s+([+-]?\d+\.?\d*)',
            'total_return_pct': r'Total profit %\s+\|\s+([+-]?\d+\.?\d*)',
            'win_rate': r'Win rate\s+\|\s+([+-]?\d+\.?\d*)%',
            'max_drawdown': r'Max drawdown\s+\|\s+([+-]?\d+\.?\d*)\s*USDT',
            'max_drawdown_pct': r'Max drawdown %\s+\|\s+([+-]?\d+\.?\d*)',
            'sharpe_ratio': r'Sharpe\s+\|\s+([+-]?\d+\.?\d*)',
            'sortino_ratio': r'Sortino\s+\|\s+([+-]?\d+\.?\d*)',
            'calmar_ratio': r'Calmar\s+\|\s+([+-]?\d+\.?\d*)',
            'total_trades': r'Total trades\s+\|\s+(\d+)',
            'winning_trades': r'Winning trades\s+\|\s+(\d+)',
            'losing_trades': r'Losing trades\s+\|\s+(\d+)',
            'avg_profit': r'Avg\. profit\s+\|\s+([+-]?\d+\.?\d*)\s*USDT',
            'avg_profit_pct': r'Avg\. profit %\s+\|\s+([+-]?\d+\.?\d*)',
            'avg_duration': r'Avg\. duration\s+\|\s+([+-]?\d+\.?\d*)',
            'total_profit': r'Total profit USDT\s+\|\s+([+-]?\d+\.?\d*)',
            'total_loss': r'Total loss USDT\s+\|\s+([+-]?\d+\.?\d*)'
        }
    
    def parse_backtest_output(self, 
                             output: str, 
                             strategy_name: str, 
                             config: BacktestConfig) -> BacktestResult:
        """
        Parse freqtrade backtest output
        
        Args:
            output: freqtrade output text
            strategy_name: strategy name
            config: backtest configuration
            
        Returns:
            backtest result object
        """
        try:
            ErrorHandler.log_info(f"Starting to parse backtest result: {strategy_name}")
            
            # Parse performance metrics
            metrics = self._parse_metrics(output)
            
            # Parse trade records
            trades = self._parse_trades(output)
            
            # Create result object
            result = BacktestResult(
                strategy_name=strategy_name,
                config=config,
                metrics=metrics,
                trades=trades,
                timestamp=datetime.now()
            )
            
            ErrorHandler.log_info(f"Backtest result parsing completed: {strategy_name}")
            return result
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to parse backtest result: {str(e)}")
            raise DataError(f"Failed to parse backtest result: {str(e)}")
    
    def parse_backtest_file(self, file_path: Path | str, strategy_name: str, config: BacktestConfig) -> BacktestResult:
        """Parse backtest result from a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataError(f"Backtest output file not found: {path}")

            content = path.read_text(encoding='utf-8')
            ErrorHandler.log_info(f"Parsing backtest output from file: {path}")
            return self.parse_backtest_output(content, strategy_name, config)
        except Exception as exc:
            ErrorHandler.log_error(f"Failed to parse backtest file {file_path}: {exc}")
            raise
    
    def _parse_metrics(self, output: str) -> PerformanceMetrics:
        """Parse performance metrics"""
        metrics = PerformanceMetrics()
        
        try:
            # Use regular expressions to extract metrics
            for metric_name, pattern in self.metric_patterns.items():
                match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        value = float(match.group(1))
                        setattr(metrics, metric_name, value)
                        ErrorHandler.log_info(f"Extracted metric {metric_name}: {value}")
                    except ValueError:
                        ErrorHandler.log_warning(f"Cannot convert metric value: {metric_name} = {match.group(1)}")
            
            # Calculate derived metrics
            if metrics.winning_trades and metrics.losing_trades:
                total_profit = metrics.avg_profit * metrics.winning_trades
                total_loss = abs(metrics.avg_profit * metrics.losing_trades) # Assuming avg_profit is the same for wins and losses which is not ideal
                if total_loss > 0:
                    metrics.profit_factor = total_profit / total_loss

            metrics.calculate_derived_metrics()
            
            # Validate metric reasonableness
            self._validate_metrics(metrics)
            
        except Exception as e:
            ErrorHandler.log_error(f"Failed to parse performance metrics: {str(e)}")
        
        return metrics
    
    def _validate_metrics(self, metrics: PerformanceMetrics):
        """Validate metric reasonableness"""
        # Check if win rate is within reasonable range
        if metrics.win_rate < 0 or metrics.win_rate > 100:
            ErrorHandler.log_warning(f"Win rate out of reasonable range: {metrics.win_rate}%")
        
        # Check trade count
        if metrics.total_trades < 0:
            ErrorHandler.log_warning(f"Abnormal trade count: {metrics.total_trades}")
        
        # Check if winning and losing trades match total trades
        if metrics.winning_trades + metrics.losing_trades != metrics.total_trades:
            ErrorHandler.log_warning("Winning and losing trade counts don't match total trades")
    
    def _parse_trades(self, output: str) -> List[TradeRecord]:
        """Parse trade records"""
        trades = []
        
        try:
            # Find trade table section
            trade_table_pattern = r'BACKTESTING REPORT.*?(?=\n\n|\Z)'
            trade_match = re.search(trade_table_pattern, output, re.DOTALL)
            
            if not trade_match:
                ErrorHandler.log_warning("Trade record table not found")
                return trades
            
            trade_section = trade_match.group(0)
            
            # Parse table rows
            lines = trade_section.split('\n')
            header_found = False
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and separators
                if not line or line.startswith('=') or line.startswith('-'):
                    continue
                
                # Find header
                if 'Pair' in line and 'Profit' in line:
                    header_found = True
                    continue
                
                # Parse trade rows
                if header_found and '|' in line:
                    trade = self._parse_trade_line(line)
                    if trade:
                        trades.append(trade)
            
            ErrorHandler.log_info(f"Parsed {len(trades)} trade records")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to parse trade records: {str(e)}")
        
        return trades
    
    def _parse_trade_line(self, line: str) -> Optional[TradeRecord]:
        """Parse single trade record line"""
        try:
            # Split table columns
            columns = [col.strip() for col in line.split('|') if col.strip()]
            
            if len(columns) < 6:
                return None
            
            # Parse according to freqtrade output format
            # This needs to be adjusted based on actual output format
            pair = columns[0] if len(columns) > 0 else ""
            profit_str = columns[-2] if len(columns) > 1 else "0"
            
            # Parse profit
            profit_match = re.search(r'([+-]?\d+\.?\d*)', profit_str)
            profit = float(profit_match.group(1)) if profit_match else 0.0
            
            # Create trade record (simplified version)
            trade = TradeRecord(
                pair=pair,
                side="buy",  # Simplified handling
                timestamp=datetime.now(),  # Should actually parse from output
                price=0.0,  # Should actually parse from output
                amount=0.0,  # Should actually parse from output
                profit=profit,
                reason="backtest"
            )
            
            return trade
        
        except Exception as e:
            ErrorHandler.log_warning(f"Failed to parse trade line: {line} - {str(e)}")
            return None
    
    def parse_json_result(self, json_file: Path) -> Optional[BacktestResult]:
        """
        Parse JSON format backtest result
        
        Args:
            json_file: JSON result file path
            
        Returns:
            backtest result object
        """
        try:
            if not json_file.exists():
                raise DataError(f"Result file does not exist: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse JSON data
            return self._parse_json_data(data)
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to parse JSON result: {str(e)}")
            return None
    
    def _parse_json_data(self, data: Dict[str, Any]) -> BacktestResult:
        """Parse JSON data"""
        try:
            # Extract basic information
            strategy_name = data.get('strategy', {}).get('strategy_name', 'Unknown')
            
            # Parse performance metrics
            metrics_data = data.get('results_metrics', {})
            metrics = PerformanceMetrics()
            
            # Map JSON fields to metric object
            metric_mapping = {
                'profit_total': 'total_return',
                'profit_total_pct': 'total_return_pct',
                'winrate': 'win_rate',
                'max_drawdown': 'max_drawdown',
                'max_drawdown_pct': 'max_drawdown_pct',
                'sharpe': 'sharpe_ratio',
                'sortino': 'sortino_ratio',
                'calmar': 'calmar_ratio',
                'trades': 'total_trades',
                'wins': 'winning_trades',
                'losses': 'losing_trades',
                'profit_mean': 'avg_profit',
                'profit_mean_pct': 'avg_profit_pct'
            }
            
            for json_key, metric_key in metric_mapping.items():
                if json_key in metrics_data:
                    setattr(metrics, metric_key, metrics_data[json_key])
            
            # Parse trade records
            trades_data = data.get('trades', [])
            trades = []
            
            for trade_data in trades_data:
                trade = TradeRecord(
                    pair=trade_data.get('pair', ''),
                    side=trade_data.get('side', 'buy'),
                    timestamp=datetime.fromisoformat(trade_data.get('open_date', datetime.now().isoformat())),
                    price=trade_data.get('open_rate', 0.0),
                    amount=trade_data.get('amount', 0.0),
                    profit=trade_data.get('profit_abs', 0.0),
                    profit_pct=trade_data.get('profit_ratio', 0.0),
                    reason=trade_data.get('exit_reason', '')
                )
                trades.append(trade)
            
            # Create configuration object (simplified)
            config = BacktestConfig(
                start_date=datetime.now().date(),
                end_date=datetime.now().date(),
                timeframe="1h",
                pairs=[],
                initial_balance=1000.0,
                max_open_trades=3
            )
            
            # Create result object
            result = BacktestResult(
                strategy_name=strategy_name,
                config=config,
                metrics=metrics,
                trades=trades,
                timestamp=datetime.now()
            )
            
            return result
        
        except Exception as e:
            raise DataError(f"Failed to parse JSON data: {str(e)}")
    
    def parse_csv_trades(self, csv_file: Path) -> List[TradeRecord]:
        """
        Parse CSV format trade records
        
        Args:
            csv_file: CSV file path
            
        Returns:
            trade record list
        """
        trades = []
        
        try:
            if not csv_file.exists():
                raise DataError(f"CSV file does not exist: {csv_file}")
            
            df = pd.read_csv(csv_file)
            
            for _, row in df.iterrows():
                trade = TradeRecord(
                    pair=row.get('pair', ''),
                    side=row.get('side', 'buy'),
                    timestamp=pd.to_datetime(row.get('open_date', datetime.now())),
                    price=float(row.get('open_rate', 0.0)),
                    amount=float(row.get('amount', 0.0)),
                    profit=float(row.get('profit_abs', 0.0)),
                    profit_pct=float(row.get('profit_ratio', 0.0)),
                    reason=row.get('exit_reason', '')
                )
                trades.append(trade)
            
            ErrorHandler.log_info(f"Parsed {len(trades)} trade records from CSV")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to parse CSV trade records: {str(e)}")
        
        return trades
    
    def extract_summary_stats(self, output: str) -> Dict[str, Any]:
        """
        Extract summary statistics
        
        Args:
            output: freqtrade output text
            
        Returns:
            statistics dictionary
        """
        stats = {}
        
        try:
            # Extract key statistics
            patterns = {
                'start_date': r'Backtesting from (\d{4}-\d{2}-\d{2})',
                'end_date': r'to (\d{4}-\d{2}-\d{2})',
                'total_days': r'(\d+) days',
                'pairs_tested': r'(\d+) pairs?',
                'timeframe': r'timeframe: (\w+)',
                'initial_balance': r'Starting balance: ([+-]?\d+\.?\d*)',
                'final_balance': r'Final balance: ([+-]?\d+\.?\d*)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    stats[key] = match.group(1)
            
        except Exception as e:
            ErrorHandler.log_error(f"Failed to extract summary statistics: {str(e)}")
        
        return stats
    
    def validate_result_completeness(self, result: BacktestResult) -> tuple[bool, List[str]]:
        """
        Validate result completeness
        
        Args:
            result: backtest result
            
        Returns:
            (is_complete, missing_items_list)
        """
        missing_items = []
        
        # Check basic information
        if not result.strategy_name:
            missing_items.append("strategy name")
        
        if not result.config:
            missing_items.append("backtest configuration")
        
        # Check performance metrics
        if result.metrics.total_trades == 0:
            missing_items.append("trade records")
        
        if result.metrics.total_return == 0 and result.metrics.total_return_pct == 0:
            missing_items.append("return metrics")
        
        # Check timestamp
        if not result.timestamp:
            missing_items.append("timestamp")
        
        is_complete = len(missing_items) == 0
        return is_complete, missing_items