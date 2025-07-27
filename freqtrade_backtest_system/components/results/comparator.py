"""
Result comparator
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from utils.data_models import BacktestResult, ComparisonResult, METRIC_WEIGHTS
from utils.error_handling import ErrorHandler, DataError, error_handler

class ResultComparator:
    """Result comparator"""
    
    def __init__(self, metric_weights: Optional[Dict[str, float]] = None):
        """
        Initialize comparator
        
        Args:
            metric_weights: metric weight configuration
        """
        self.metric_weights = metric_weights or METRIC_WEIGHTS
        self.comparison_metrics = [
            'total_return',
            'total_return_pct', 
            'win_rate',
            'max_drawdown',
            'max_drawdown_pct',
            'sharpe_ratio',
            'sortino_ratio',
            'total_trades',
            'winning_trades',
            'losing_trades',
            'avg_profit',
            'avg_profit_pct'
        ]
    
    @error_handler(DataError, show_error=True)
    def compare_strategies(self, results: List[BacktestResult]) -> ComparisonResult:
        """
        Compare multiple strategy results
        
        Args:
            results: backtest results list
            
        Returns:
            comparison result object
        """
        if len(results) < 2:
            raise DataError("At least 2 strategy results are required for comparison")
        
        ErrorHandler.log_info(f"Starting comparison of {len(results)} strategies")
        
        try:
            # Create comparison dataframe
            comparison_df = self._create_comparison_dataframe(results)
            
            # Calculate rankings
            rankings = self._calculate_rankings(comparison_df)
            
            # Find best strategy
            best_strategy = min(rankings.items(), key=lambda x: x[1])[0]
            
            # Create metrics comparison
            metrics_comparison = {}
            for metric in self.comparison_metrics:
                if metric in comparison_df.columns:
                    metrics_comparison[metric] = comparison_df[metric].tolist()
            
            # Create comparison result
            comparison = ComparisonResult(
                strategies=comparison_df.index.tolist(),
                metrics_comparison=metrics_comparison,
                rankings=rankings,
                best_strategy=best_strategy
            )
            
            ErrorHandler.log_info(f"Strategy comparison completed, best strategy: {best_strategy}")
            return comparison
        
        except Exception as e:
            ErrorHandler.log_error(f"Strategy comparison failed: {str(e)}")
            raise DataError(f"Strategy comparison failed: {str(e)}")
    
    def _create_comparison_dataframe(self, results: List[BacktestResult]) -> pd.DataFrame:
        """Create comparison dataframe"""
        data = []
        
        for result in results:
            row = {'strategy': result.strategy_name}
            
            # Extract metrics
            for metric in self.comparison_metrics:
                if hasattr(result.metrics, metric):
                    row[metric] = getattr(result.metrics, metric)
                else:
                    row[metric] = 0.0
            
            data.append(row)
        
        df = pd.DataFrame(data)
        df.set_index('strategy', inplace=True)
        
        return df
    
    def _calculate_rankings(self, df: pd.DataFrame) -> Dict[str, int]:
        """Calculate strategy rankings"""
        rankings = {}
        
        try:
            # Calculate weighted score for each strategy
            scores = {}
            
            for strategy in df.index:
                score = 0.0
                
                for metric, weight in self.metric_weights.items():
                    if metric in df.columns:
                        value = df.loc[strategy, metric]
                        
                        # Normalize value (higher is better for most metrics)
                        if metric in ['max_drawdown', 'max_drawdown_pct']:
                            # For drawdown, lower is better
                            normalized_value = 1.0 / (1.0 + abs(value))
                        else:
                            # For other metrics, higher is better
                            normalized_value = max(0, value)
                        
                        score += normalized_value * weight
                
                scores[strategy] = score
            
            # Sort by score (descending) and assign ranks
            sorted_strategies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            for rank, (strategy, score) in enumerate(sorted_strategies, 1):
                rankings[strategy] = rank
            
        except Exception as e:
            ErrorHandler.log_error(f"Failed to calculate rankings: {str(e)}")
            # Fallback: assign sequential rankings
            for i, strategy in enumerate(df.index, 1):
                rankings[strategy] = i
        
        return rankings
    
    def create_performance_matrix(self, results: List[BacktestResult]) -> pd.DataFrame:
        """
        Create performance comparison matrix
        
        Args:
            results: backtest results list
            
        Returns:
            performance matrix dataframe
        """
        try:
            data = []
            
            for result in results:
                row = {
                    'Strategy': result.strategy_name,
                    'Total Return (%)': f"{result.metrics.total_return_pct:.2f}%",
                    'Win Rate (%)': f"{result.metrics.win_rate:.2f}%",
                    'Max Drawdown (%)': f"{result.metrics.max_drawdown_pct:.2f}%",
                    'Sharpe Ratio': f"{result.metrics.sharpe_ratio:.3f}",
                    'Total Trades': result.metrics.total_trades,
                    'Avg Profit': f"{result.metrics.avg_profit:.2f}",
                    'Execution Time': f"{result.execution_time:.2f}s" if result.execution_time else "N/A"
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            return df
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create performance matrix: {str(e)}")
            return pd.DataFrame()
    
    def analyze_risk_return(self, results: List[BacktestResult]) -> Dict[str, List[str]]:
        """
        Analyze risk-return characteristics
        
        Args:
            results: backtest results list
            
        Returns:
            risk-return analysis dictionary
        """
        analysis = {
            'high_return_low_risk': [],
            'high_return_high_risk': [],
            'low_return_low_risk': [],
            'low_return_high_risk': []
        }
        
        try:
            if not results:
                return analysis
            
            # Calculate median values for comparison
            returns = [r.metrics.total_return_pct for r in results]
            drawdowns = [abs(r.metrics.max_drawdown_pct) for r in results]
            
            median_return = np.median(returns)
            median_drawdown = np.median(drawdowns)
            
            # Classify strategies
            for result in results:
                strategy_name = result.strategy_name
                return_pct = result.metrics.total_return_pct
                drawdown_pct = abs(result.metrics.max_drawdown_pct)
                
                if return_pct >= median_return and drawdown_pct <= median_drawdown:
                    analysis['high_return_low_risk'].append(strategy_name)
                elif return_pct >= median_return and drawdown_pct > median_drawdown:
                    analysis['high_return_high_risk'].append(strategy_name)
                elif return_pct < median_return and drawdown_pct <= median_drawdown:
                    analysis['low_return_low_risk'].append(strategy_name)
                else:
                    analysis['low_return_high_risk'].append(strategy_name)
            
        except Exception as e:
            ErrorHandler.log_error(f"Risk-return analysis failed: {str(e)}")
        
        return analysis
    
    def get_top_strategies(self, results: List[BacktestResult], top_n: int = 3) -> List[BacktestResult]:
        """
        Get top N strategies based on comprehensive scoring
        
        Args:
            results: backtest results list
            top_n: number of top strategies to return
            
        Returns:
            top strategies list
        """
        try:
            if len(results) <= top_n:
                return results
            
            comparison = self.compare_strategies(results)
            
            # Sort strategies by ranking
            sorted_strategies = sorted(comparison.rankings.items(), key=lambda x: x[1])
            top_strategy_names = [name for name, rank in sorted_strategies[:top_n]]
            
            # Return corresponding results
            top_results = []
            for result in results:
                if result.strategy_name in top_strategy_names:
                    top_results.append(result)
            
            return top_results
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get top strategies: {str(e)}")
            return results[:top_n]
    
    def generate_comparison_summary(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """
        Generate comparison summary statistics
        
        Args:
            results: backtest results list
            
        Returns:
            summary statistics dictionary
        """
        summary = {
            'total_strategies': len(results),
            'avg_return': 0.0,
            'avg_win_rate': 0.0,
            'avg_drawdown': 0.0,
            'best_return': 0.0,
            'worst_return': 0.0,
            'most_trades': 0,
            'least_trades': 0
        }
        
        try:
            if not results:
                return summary
            
            returns = [r.metrics.total_return_pct for r in results]
            win_rates = [r.metrics.win_rate for r in results]
            drawdowns = [r.metrics.max_drawdown_pct for r in results]
            trade_counts = [r.metrics.total_trades for r in results]
            
            summary.update({
                'avg_return': np.mean(returns),
                'avg_win_rate': np.mean(win_rates),
                'avg_drawdown': np.mean(drawdowns),
                'best_return': max(returns),
                'worst_return': min(returns),
                'most_trades': max(trade_counts),
                'least_trades': min(trade_counts)
            })
            
        except Exception as e:
            ErrorHandler.log_error(f"Failed to generate comparison summary: {str(e)}")
        
        return summary
    
    def export_comparison_report(self, results: List[BacktestResult], file_path: str) -> bool:
        """
        Export comparison report to file
        
        Args:
            results: backtest results list
            file_path: output file path
            
        Returns:
            whether export was successful
        """
        try:
            comparison = self.compare_strategies(results)
            matrix = self.create_performance_matrix(results)
            summary = self.generate_comparison_summary(results)
            
            # Create report content
            report_content = {
                'comparison_timestamp': datetime.now().isoformat(),
                'summary': summary,
                'rankings': comparison.rankings,
                'best_strategy': comparison.best_strategy,
                'performance_matrix': matrix.to_dict('records'),
                'detailed_metrics': comparison.metrics_comparison
            }
            
            # Save to file
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_content, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Comparison report exported to: {file_path}")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to export comparison report: {str(e)}")
            return False