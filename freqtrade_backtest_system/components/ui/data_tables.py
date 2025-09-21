"""
Advanced data table components with sorting, filtering, and pagination
"""
import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import plotly.express as px

from utils.data_models import BacktestResult, StrategyInfo, TradeRecord
from utils.error_handling import ErrorHandler, error_handler

class DataTableComponents:
    """Advanced data table components"""
    
    def __init__(self):
        """Initialize data table components"""
        self.default_page_size = 20
        self.max_page_size = 100
    
    @error_handler(Exception, show_error=True)
    def render_results_table(self, 
                           results: List[BacktestResult],
                           show_filters: bool = True,
                           show_pagination: bool = True,
                           selectable: bool = False) -> Optional[List[BacktestResult]]:
        """
        Render backtest results table with advanced features
        
        Args:
            results: list of backtest results
            show_filters: whether to show filter controls
            show_pagination: whether to show pagination
            selectable: whether rows are selectable
            
        Returns:
            selected results if selectable=True
        """
        if not results:
            st.info("No results to display")
            return None
        
        # Convert to DataFrame
        df = self._results_to_dataframe(results)
        
        # Apply filters if enabled
        if show_filters:
            df = self._apply_filters(df, "results")
        
        # Apply pagination if enabled
        if show_pagination:
            df, page_info = self._apply_pagination(df, "results")
            
            if page_info:
                st.caption(f"Showing {page_info['start']}-{page_info['end']} of {page_info['total']} results")
        
        # Display table
        if selectable:
            # Use st.data_editor for selection
            edited_df = st.data_editor(
                df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select strategies for comparison",
                        default=False,
                    )
                },
                disabled=[col for col in df.columns if col != "Select"]
            )
            
            # Return selected results
            if "Select" in edited_df.columns:
                selected_indices = edited_df[edited_df["Select"]].index.tolist()
                return [results[i] for i in selected_indices if i < len(results)]
            st.dataframe(
                df,
                width='stretch',
                hide_index=True
            )
        
        return None
    
    @error_handler(Exception, show_error=True)
    def render_strategies_table(self, 
                              strategies: List[StrategyInfo],
                              show_filters: bool = True,
                              selectable: bool = True) -> Optional[List[str]]:
        """
        Render strategies table
        
        Args:
            strategies: list of strategy info
            show_filters: whether to show filter controls
            selectable: whether strategies are selectable
            
        Returns:
            selected strategy names if selectable=True
        """
        if not strategies:
            st.info("No strategies to display")
            return None
        
        # Convert to DataFrame
        df = self._strategies_to_dataframe(strategies)
        
        # Apply filters if enabled
        if show_filters:
            df = self._apply_filters(df, "strategies")
        
        # Display table
        if selectable:
            # Add selection column
            df.insert(0, "Select", False)
            
            edited_df = st.data_editor(
                df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select strategies for backtesting",
                        default=False,
                    )
                },
                disabled=[col for col in df.columns if col != "Select"]
            )
            
            # Return selected strategy names
            if "Select" in edited_df.columns:
                selected_rows = edited_df[edited_df["Select"]]
                return selected_rows["Name"].tolist()
        else:
            st.dataframe(
                df,
                width='stretch',
                hide_index=True
            )
        
        return None
    
    @error_handler(Exception, show_error=True)
    def render_trades_table(self, 
                          trades: List[TradeRecord],
                          show_filters: bool = True,
                          show_pagination: bool = True):
        """
        Render trades table
        
        Args:
            trades: list of trade records
            show_filters: whether to show filter controls
            show_pagination: whether to show pagination
        """
        if not trades:
            st.info("No trades to display")
            return
        
        # Convert to DataFrame
        df = self._trades_to_dataframe(trades)
        
        # Apply filters if enabled
        if show_filters:
            df = self._apply_filters(df, "trades")
        
        # Apply pagination if enabled
        if show_pagination:
            df, page_info = self._apply_pagination(df, "trades")
            
            if page_info:
                st.caption(f"Showing {page_info['start']}-{page_info['end']} of {page_info['total']} trades")
        
        # Color-code profitable/unprofitable trades
        def style_profit(val):
            try:
                if pd.isna(val):
                    return ''
                num_val = float(str(val).replace('%', '').replace('$', ''))
                if num_val > 0:
                    return 'background-color: #d4edda; color: #155724'
                elif num_val < 0:
                    return 'background-color: #f8d7da; color: #721c24'
                return ''
            except:
                return ''
        
        # Apply styling
        styled_df = df.style.applymap(
            style_profit, 
            subset=['Profit', 'Profit %'] if 'Profit' in df.columns else []
        st.dataframe(
            styled_df,
            width='stretch',
            hide_index=True
        )
    
    def _results_to_dataframe(self, results: List[BacktestResult]) -> pd.DataFrame:
        """Convert backtest results to DataFrame"""
        data = []
        
        for result in results:
            metrics = result.metrics
            data.append({
                'Strategy': result.strategy_name,
                'Total Return': f"{metrics.total_return_pct:.2f}%",
                'Win Rate': f"{metrics.win_rate:.2f}%",
                'Max Drawdown': f"{metrics.max_drawdown_pct:.2f}%",
                'Sharpe Ratio': f"{metrics.sharpe_ratio:.3f}",
                'Sortino Ratio': f"{metrics.sortino_ratio:.3f}",
                'Total Trades': metrics.total_trades,
                'Winning Trades': metrics.winning_trades,
                'Losing Trades': metrics.losing_trades,
                'Avg Profit': f"{metrics.avg_profit:.2f}",
                'Execution Time': f"{result.execution_time:.2f}s" if result.execution_time else "N/A",
                'Status': result.status.value.title(),
                'Timestamp': result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return pd.DataFrame(data)
    
    def _strategies_to_dataframe(self, strategies: List[StrategyInfo]) -> pd.DataFrame:
        """Convert strategy info to DataFrame"""
        data = []
        
        for strategy in strategies:
            data.append({
                'Name': strategy.name,
                'Description': strategy.description[:100] + "..." if len(strategy.description) > 100 else strategy.description,
                'Author': strategy.author or "Unknown",
                'Version': strategy.version or "N/A",
                'File Path': str(strategy.file_path),
                'Last Modified': strategy.last_modified.strftime('%Y-%m-%d %H:%M:%S') if strategy.last_modified else "N/A"
            })
        
        return pd.DataFrame(data)
    
    def _trades_to_dataframe(self, trades: List[TradeRecord]) -> pd.DataFrame:
        """Convert trade records to DataFrame"""
        data = []
        
        for trade in trades:
            data.append({
                'Pair': trade.pair,
                'Side': trade.side.upper(),
                'Timestamp': trade.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Price': f"{trade.price:.6f}" if trade.price else "N/A",
                'Amount': f"{trade.amount:.6f}" if trade.amount else "N/A",
                'Profit': f"{trade.profit:.2f}" if trade.profit is not None else "N/A",
                'Profit %': f"{trade.profit_pct:.2f}%" if trade.profit_pct is not None else "N/A",
                'Reason': trade.reason or "N/A"
            })
        
        return pd.DataFrame(data)
    
    def _apply_filters(self, df: pd.DataFrame, table_type: str) -> pd.DataFrame:
        """Apply filters to DataFrame"""
        st.subheader("🔍 Filters")
        
        with st.expander("Filter Options", expanded=False):
            if table_type == "results":
                return self._apply_results_filters(df)
            elif table_type == "strategies":
                return self._apply_strategies_filters(df)
            elif table_type == "trades":
                return self._apply_trades_filters(df)
        
        return df
    
    def _apply_results_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply filters specific to results table"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Strategy name filter
            strategy_filter = st.text_input(
                "Strategy Name Contains",
                key="results_strategy_filter"
            )
            
            # Status filter
            status_options = ["All"] + df['Status'].unique().tolist()
            status_filter = st.selectbox(
                "Status",
                status_options,
                key="results_status_filter"
            )
        
        with col2:
            # Return range filter
            return_min = st.number_input(
                "Min Return (%)",
                value=None,
                key="results_return_min"
            )
            
            return_max = st.number_input(
                "Max Return (%)",
                value=None,
                key="results_return_max"
            )
        
        with col3:
            # Win rate filter
            win_rate_min = st.number_input(
                "Min Win Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=None,
                key="results_win_rate_min"
            )
            
            # Max drawdown filter
            max_drawdown_filter = st.number_input(
                "Max Drawdown Limit (%)",
                value=None,
                key="results_max_drawdown"
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if strategy_filter:
            filtered_df = filtered_df[
                filtered_df['Strategy'].str.contains(strategy_filter, case=False, na=False)
            ]
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['Status'] == status_filter]
        
        if return_min is not None:
            filtered_df = filtered_df[
                filtered_df['Total Return'].str.replace('%', '').astype(float) >= return_min
            ]
        
        if return_max is not None:
            filtered_df = filtered_df[
                filtered_df['Total Return'].str.replace('%', '').astype(float) <= return_max
            ]
        
        if win_rate_min is not None:
            filtered_df = filtered_df[
                filtered_df['Win Rate'].str.replace('%', '').astype(float) >= win_rate_min
            ]
        
        if max_drawdown_filter is not None:
            filtered_df = filtered_df[
                filtered_df['Max Drawdown'].str.replace('%', '').astype(float).abs() <= max_drawdown_filter
            ]
        
        return filtered_df
    
    def _apply_strategies_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply filters specific to strategies table"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Name filter
            name_filter = st.text_input(
                "Strategy Name Contains",
                key="strategies_name_filter"
            )
            
            # Author filter
            author_options = ["All"] + [author for author in df['Author'].unique() if author != "Unknown"]
            author_filter = st.selectbox(
                "Author",
                author_options,
                key="strategies_author_filter"
            )
        
        with col2:
            # Description filter
            desc_filter = st.text_input(
                "Description Contains",
                key="strategies_desc_filter"
            )
            
            # File path filter
            path_filter = st.text_input(
                "File Path Contains",
                key="strategies_path_filter"
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if name_filter:
            filtered_df = filtered_df[
                filtered_df['Name'].str.contains(name_filter, case=False, na=False)
            ]
        
        if author_filter != "All":
            filtered_df = filtered_df[filtered_df['Author'] == author_filter]
        
        if desc_filter:
            filtered_df = filtered_df[
                filtered_df['Description'].str.contains(desc_filter, case=False, na=False)
            ]
        
        if path_filter:
            filtered_df = filtered_df[
                filtered_df['File Path'].str.contains(path_filter, case=False, na=False)
            ]
        
        return filtered_df
    
    def _apply_trades_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply filters specific to trades table"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Pair filter
            pair_options = ["All"] + df['Pair'].unique().tolist()
            pair_filter = st.selectbox(
                "Trading Pair",
                pair_options,
                key="trades_pair_filter"
            )
            
            # Side filter
            side_options = ["All", "BUY", "SELL"]
            side_filter = st.selectbox(
                "Side",
                side_options,
                key="trades_side_filter"
            )
        
        with col2:
            # Profit filter
            profit_filter = st.selectbox(
                "Profit Type",
                ["All", "Profitable", "Unprofitable"],
                key="trades_profit_filter"
            )
            
            # Date range
            date_filter = st.date_input(
                "Date Range",
                value=None,
                key="trades_date_filter"
            )
        
        with col3:
            # Reason filter
            reason_filter = st.text_input(
                "Reason Contains",
                key="trades_reason_filter"
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if pair_filter != "All":
            filtered_df = filtered_df[filtered_df['Pair'] == pair_filter]
        
        if side_filter != "All":
            filtered_df = filtered_df[filtered_df['Side'] == side_filter]
        
        if profit_filter == "Profitable":
            filtered_df = filtered_df[
                filtered_df['Profit'].str.replace('N/A', '0').astype(float) > 0
            ]
        elif profit_filter == "Unprofitable":
            filtered_df = filtered_df[
                filtered_df['Profit'].str.replace('N/A', '0').astype(float) < 0
            ]
        
        if reason_filter:
            filtered_df = filtered_df[
                filtered_df['Reason'].str.contains(reason_filter, case=False, na=False)
            ]
        
        return filtered_df
    
    def _apply_pagination(self, df: pd.DataFrame, table_type: str) -> tuple[pd.DataFrame, Dict[str, int]]:
        """Apply pagination to DataFrame"""
        total_rows = len(df)
        
        if total_rows <= self.default_page_size:
            return df, None
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            page_size = st.selectbox(
                "Rows per page",
                [10, 20, 50, 100],
                index=1,
                key=f"{table_type}_page_size"
            )
        
        with col2:
            total_pages = (total_rows - 1) // page_size + 1
            current_page = st.number_input(
                f"Page (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=1,
                key=f"{table_type}_current_page"
            )
        
        with col3:
            st.write(f"Total: {total_rows} rows")
        
        # Calculate pagination
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        paginated_df = df.iloc[start_idx:end_idx]
        
        page_info = {
            'start': start_idx + 1,
            'end': end_idx,
            'total': total_rows,
            'page': current_page,
            'total_pages': total_pages
        }
        
        return paginated_df, page_info
    
    @error_handler(Exception, show_error=True)
    def render_comparison_table(self, results: List[BacktestResult]):
        """
        Render side-by-side comparison table
        
        Args:
            results: list of backtest results to compare
        """
        if len(results) < 2:
            st.warning("At least 2 results are needed for comparison")
            return
        
        st.subheader("📊 Strategy Comparison")
        
        # Create comparison data
        comparison_data = {}
        metrics_list = [
            ('Total Return (%)', 'total_return_pct'),
            ('Win Rate (%)', 'win_rate'),
            ('Max Drawdown (%)', 'max_drawdown_pct'),
            ('Sharpe Ratio', 'sharpe_ratio'),
            ('Sortino Ratio', 'sortino_ratio'),
            ('Calmar Ratio', 'calmar_ratio'),
            ('Total Trades', 'total_trades'),
            ('Winning Trades', 'winning_trades'),
            ('Losing Trades', 'losing_trades'),
            ('Average Profit', 'avg_profit'),
            ('Average Profit (%)', 'avg_profit_pct'),
            ('Average Duration', 'avg_duration')
        ]
        
        comparison_data['Metric'] = [metric[0] for metric in metrics_list]
        
        for result in results:
            strategy_values = []
            for metric_name, metric_attr in metrics_list:
                value = getattr(result.metrics, metric_attr)
                
                # Format values appropriately
                if 'pct' in metric_attr or '%' in metric_name:
                    formatted_value = f"{value:.2f}%"
                elif 'ratio' in metric_attr.lower():
                    formatted_value = f"{value:.3f}"
                elif isinstance(value, int):
                    formatted_value = str(value)
                else:
                    formatted_value = f"{value:.2f}"
                
                strategy_values.append(formatted_value)
            
            comparison_data[result.strategy_name] = strategy_values
        
        # Create DataFrame
        comparison_df = pd.DataFrame(comparison_data)
        
        # Style the comparison table
        def highlight_best(row):
            """Highlight best values in each row"""
            if row.name == 0:  # Skip header row
                return [''] * len(row)
            
            # Get numeric values for comparison (excluding the Metric column)
            numeric_values = []
            for i, val in enumerate(row[1:], 1):  # Skip first column (Metric)
                try:
                    # Remove % and convert to float
                    clean_val = float(str(val).replace('%', '').replace(',', ''))
                    numeric_values.append((i, clean_val))
                except:
                    numeric_values.append((i, float('-inf')))
            
            # Determine if higher or lower is better based on metric
            metric_name = row.iloc[0].lower()
            higher_is_better = not ('drawdown' in metric_name or 'duration' in metric_name)
            
            if numeric_values:
                if higher_is_better:
                    best_idx = max(numeric_values, key=lambda x: x[1])[0]
                else:
                    best_idx = min(numeric_values, key=lambda x: x[1])[0]
                
                styles = [''] * len(row)
                styles[best_idx] = 'background-color: #d4edda; font-weight: bold'
                return styles
            
            return [''] * len(row)
        
        # Apply styling
        styled_df = comparison_df.style.apply(highlight_best, axis=1)
        
        # Display table
        st.dataframe(
            styled_df,
            width='stretch',
            hide_index=True
        )
        
        # Add download button
        csv = comparison_df.to_csv(index=False)
        st.download_button(
            "📥 Download Comparison",
            data=csv,
            file_name=f"strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def render_summary_statistics(self, results: List[BacktestResult]):
        """
        Render summary statistics table
        
        Args:
            results: list of backtest results
        """
        if not results:
            return
        
        st.subheader("📈 Summary Statistics")
        
        # Calculate summary statistics
        returns = [r.metrics.total_return_pct for r in results]
        win_rates = [r.metrics.win_rate for r in results]
        drawdowns = [r.metrics.max_drawdown_pct for r in results]
        sharpe_ratios = [r.metrics.sharpe_ratio for r in results]
        trade_counts = [r.metrics.total_trades for r in results]
        
        summary_data = {
            'Metric': [
                'Number of Strategies',
                'Average Return (%)',
                'Best Return (%)',
                'Worst Return (%)',
                'Average Win Rate (%)',
                'Average Max Drawdown (%)',
                'Average Sharpe Ratio',
                'Total Trades (All Strategies)',
                'Average Trades per Strategy'
            ],
            'Value': [
                len(results),
                f"{np.mean(returns):.2f}%",
                f"{max(returns):.2f}%",
                f"{min(returns):.2f}%",
                f"{np.mean(win_rates):.2f}%",
                f"{np.mean(drawdowns):.2f}%",
                f"{np.mean(sharpe_ratios):.3f}",
                sum(trade_counts),
                f"{np.mean(trade_counts):.0f}"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        st.dataframe(
            summary_df,
            width='stretch',
            hide_index=True
        )