"""
Basic chart components for backtest results visualization
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import streamlit as st

from utils.data_models import BacktestResult, PerformanceMetrics
from utils.error_handling import ErrorHandler, error_handler

class ChartComponents:
    """Basic chart components for visualization"""
    
    def __init__(self):
        """Initialize chart components"""
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        self.chart_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
        }
    
    @error_handler(Exception, show_error=True)
    def create_return_comparison_chart(self, results: List[BacktestResult]) -> go.Figure:
        """
        Create return comparison bar chart
        
        Args:
            results: list of backtest results
            
        Returns:
            plotly figure
        """
        if not results:
            return self._create_empty_chart("No data available")
        
        try:
            # Prepare data
            strategies = [result.strategy_name for result in results]
            returns = [result.metrics.total_return_pct for result in results]
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=strategies,
                    y=returns,
                    marker_color=self.default_colors[:len(strategies)],
                    text=[f"{ret:.2f}%" for ret in returns],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>Return: %{y:.2f}%<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title="Strategy Return Comparison",
                xaxis_title="Strategy",
                yaxis_title="Total Return (%)",
                showlegend=False,
                height=500,
                template="plotly_white"
            )
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            return fig
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create return comparison chart: {str(e)}")
            return self._create_error_chart(f"Error creating chart: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def create_performance_radar_chart(self, results: List[BacktestResult]) -> go.Figure:
        """
        Create performance metrics radar chart
        
        Args:
            results: list of backtest results
            
        Returns:
            plotly figure
        """
        if not results:
            return self._create_empty_chart("No data available")
        
        try:
            # Define metrics for radar chart
            metrics = [
                ('Total Return %', 'total_return_pct'),
                ('Win Rate %', 'win_rate'),
                ('Sharpe Ratio', 'sharpe_ratio'),
                ('Max Drawdown %', 'max_drawdown_pct'),
                ('Total Trades', 'total_trades')
            ]
            
            fig = go.Figure()
            
            for i, result in enumerate(results[:5]):  # Limit to 5 strategies for readability
                # Normalize values for radar chart
                values = []
                for metric_name, metric_attr in metrics:
                    value = getattr(result.metrics, metric_attr)
                    
                    # Normalize different metrics to 0-100 scale
                    if metric_attr == 'total_return_pct':
                        normalized = max(0, min(100, value + 50))  # Shift to positive range
                    elif metric_attr == 'win_rate':
                        normalized = value
                    elif metric_attr == 'sharpe_ratio':
                        normalized = max(0, min(100, (value + 2) * 25))  # Scale -2 to 2 -> 0 to 100
                    elif metric_attr == 'max_drawdown_pct':
                        normalized = max(0, 100 + value)  # Convert negative drawdown to positive scale
                    elif metric_attr == 'total_trades':
                        normalized = min(100, value / 10)  # Scale trades
                    else:
                        normalized = value
                    
                    values.append(normalized)
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=[metric[0] for metric in metrics],
                    fill='toself',
                    name=result.strategy_name,
                    line_color=self.default_colors[i % len(self.default_colors)]
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Performance Metrics Comparison",
                height=600,
                template="plotly_white"
            )
            
            return fig
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create radar chart: {str(e)}")
            return self._create_error_chart(f"Error creating chart: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def create_metrics_comparison_table(self, results: List[BacktestResult]) -> pd.DataFrame:
        """
        Create metrics comparison table
        
        Args:
            results: list of backtest results
            
        Returns:
            pandas DataFrame
        """
        if not results:
            return pd.DataFrame()
        
        try:
            data = []
            
            for result in results:
                metrics = result.metrics
                data.append({
                    'Strategy': result.strategy_name,
                    'Total Return (%)': f"{metrics.total_return_pct:.2f}%",
                    'Win Rate (%)': f"{metrics.win_rate:.2f}%",
                    'Max Drawdown (%)': f"{metrics.max_drawdown_pct:.2f}%",
                    'Sharpe Ratio': f"{metrics.sharpe_ratio:.3f}",
                    'Sortino Ratio': f"{metrics.sortino_ratio:.3f}",
                    'Total Trades': metrics.total_trades,
                    'Avg Profit': f"{metrics.avg_profit:.2f}",
                    'Execution Time': f"{result.execution_time:.2f}s" if result.execution_time else "N/A"
                })
            
            return pd.DataFrame(data)
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create metrics table: {str(e)}")
            return pd.DataFrame()
    
    @error_handler(Exception, show_error=True)
    def create_drawdown_comparison_chart(self, results: List[BacktestResult]) -> go.Figure:
        """
        Create drawdown comparison chart
        
        Args:
            results: list of backtest results
            
        Returns:
            plotly figure
        """
        if not results:
            return self._create_empty_chart("No data available")
        
        try:
            strategies = [result.strategy_name for result in results]
            drawdowns = [abs(result.metrics.max_drawdown_pct) for result in results]
            
            # Create horizontal bar chart for drawdowns
            fig = go.Figure(data=[
                go.Bar(
                    y=strategies,
                    x=drawdowns,
                    orientation='h',
                    marker_color='red',
                    opacity=0.7,
                    text=[f"{dd:.2f}%" for dd in drawdowns],
                    textposition='auto',
                    hovertemplate='<b>%{y}</b><br>Max Drawdown: %{x:.2f}%<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title="Maximum Drawdown Comparison",
                xaxis_title="Max Drawdown (%)",
                yaxis_title="Strategy",
                showlegend=False,
                height=max(400, len(strategies) * 50),
                template="plotly_white"
            )
            
            return fig
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create drawdown chart: {str(e)}")
            return self._create_error_chart(f"Error creating chart: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def create_risk_return_scatter(self, results: List[BacktestResult]) -> go.Figure:
        """
        Create risk-return scatter plot
        
        Args:
            results: list of backtest results
            
        Returns:
            plotly figure
        """
        if not results:
            return self._create_empty_chart("No data available")
        
        try:
            strategies = [result.strategy_name for result in results]
            returns = [result.metrics.total_return_pct for result in results]
            risks = [abs(result.metrics.max_drawdown_pct) for result in results]
            sharpe_ratios = [result.metrics.sharpe_ratio for result in results]
            
            # Create scatter plot
            fig = go.Figure(data=[
                go.Scatter(
                    x=risks,
                    y=returns,
                    mode='markers+text',
                    text=strategies,
                    textposition='top center',
                    marker=dict(
                        size=[max(5, min(20, abs(sr) * 10)) for sr in sharpe_ratios],
                        color=sharpe_ratios,
                        colorscale='RdYlGn',
                        showscale=True,
                        colorbar=dict(title="Sharpe Ratio"),
                        line=dict(width=1, color='black')
                    ),
                    hovertemplate='<b>%{text}</b><br>' +
                                'Return: %{y:.2f}%<br>' +
                                'Risk (Max DD): %{x:.2f}%<br>' +
                                'Sharpe: %{marker.color:.3f}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title="Risk-Return Analysis",
                xaxis_title="Risk (Max Drawdown %)",
                yaxis_title="Return (%)",
                showlegend=False,
                height=600,
                template="plotly_white"
            )
            
            # Add quadrant lines
            if returns and risks:
                median_return = np.median(returns)
                median_risk = np.median(risks)
                
                fig.add_hline(y=median_return, line_dash="dash", line_color="gray", opacity=0.5)
                fig.add_vline(x=median_risk, line_dash="dash", line_color="gray", opacity=0.5)
                
                # Add quadrant labels
                fig.add_annotation(
                    x=max(risks) * 0.8, y=max(returns) * 0.8,
                    text="High Risk<br>High Return", showarrow=False,
                    bgcolor="rgba(255,255,0,0.3)", bordercolor="orange"
                )
                
                fig.add_annotation(
                    x=min(risks) * 1.2, y=max(returns) * 0.8,
                    text="Low Risk<br>High Return", showarrow=False,
                    bgcolor="rgba(0,255,0,0.3)", bordercolor="green"
                )
            
            return fig
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create risk-return scatter: {str(e)}")
            return self._create_error_chart(f"Error creating chart: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def create_trade_distribution_chart(self, result: BacktestResult) -> go.Figure:
        """
        Create trade distribution chart for a single strategy
        
        Args:
            result: backtest result
            
        Returns:
            plotly figure
        """
        if not result.trades:
            return self._create_empty_chart("No trade data available")
        
        try:
            profits = [trade.profit for trade in result.trades if trade.profit is not None]
            
            if not profits:
                return self._create_empty_chart("No profit data available")
            
            # Create histogram
            fig = go.Figure(data=[
                go.Histogram(
                    x=profits,
                    nbinsx=30,
                    marker_color='blue',
                    opacity=0.7,
                    name='Trade Distribution'
                )
            ])
            
            fig.update_layout(
                title=f"Trade Profit Distribution - {result.strategy_name}",
                xaxis_title="Profit",
                yaxis_title="Number of Trades",
                showlegend=False,
                height=400,
                template="plotly_white"
            )
            
            # Add vertical line at zero
            fig.add_vline(x=0, line_dash="dash", line_color="red", opacity=0.7)
            
            # Add statistics annotations
            mean_profit = np.mean(profits)
            median_profit = np.median(profits)
            
            fig.add_annotation(
                x=0.7, y=0.9, xref="paper", yref="paper",
                text=f"Mean: {mean_profit:.2f}<br>Median: {median_profit:.2f}",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black"
            )
            
            return fig
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create trade distribution chart: {str(e)}")
            return self._create_error_chart(f"Error creating chart: {str(e)}")
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            text=message,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            template="plotly_white",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        return fig
    
    def _create_error_chart(self, error_message: str) -> go.Figure:
        """Create error chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            text=f"Error: {error_message}",
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            template="plotly_white",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        return fig
    
    def render_interactive_charts(self, results: List[BacktestResult]):
        """
        Render interactive charts in Streamlit
        
        Args:
            results: list of backtest results
        """
        if not results:
            st.info("No results available for visualization")
            return
        
        # Import advanced charts
        try:
            from .advanced_charts import AdvancedCharts
            advanced_charts = AdvancedCharts()
            has_advanced_charts = True
        except ImportError:
            has_advanced_charts = False
            st.warning("Advanced charts not available")
        
        # Chart selection
        chart_options = [
            "Return Comparison",
            "Performance Radar",
            "Risk-Return Scatter",
            "Drawdown Comparison",
            "Metrics Table"
        ]
        
        # Add advanced chart options if available
        if has_advanced_charts:
            chart_options.extend([
                "Equity Curve",
                "Performance Comparison",
                "OHLCV with Trades (Sample)"
            ])
        
        chart_type = st.selectbox(
            "Select Chart Type",
            chart_options
        )
        
        # Render selected chart
        if chart_type == "Return Comparison":
            fig = self.create_return_comparison_chart(results)
            st.plotly_chart(fig, width='stretch', config=self.chart_config)
        
        elif chart_type == "Performance Radar":
            fig = self.create_performance_radar_chart(results)
            st.plotly_chart(fig, width='stretch', config=self.chart_config)
        
        elif chart_type == "Risk-Return Scatter":
            fig = self.create_risk_return_scatter(results)
            st.plotly_chart(fig, width='stretch', config=self.chart_config)
        
        elif chart_type == "Drawdown Comparison":
            fig = self.create_drawdown_comparison_chart(results)
            st.plotly_chart(fig, width='stretch', config=self.chart_config)
        
        elif chart_type == "Metrics Table":
            df = self.create_metrics_comparison_table(results)
            if not df.empty:
                st.dataframe(df, width='stretch')
            else:
                st.info("No data available for table")
        
        # Advanced charts
        elif chart_type == "Equity Curve" and has_advanced_charts:
            fig = advanced_charts.create_equity_curve(results)
            st.plotly_chart(fig, width='stretch', config=self.chart_config)
        
        elif chart_type == "Performance Comparison" and has_advanced_charts:
            fig = advanced_charts.create_performance_comparison_chart(results)
            st.plotly_chart(fig, width='stretch', config=self.chart_config)
        
        elif chart_type == "OHLCV with Trades (Sample)" and has_advanced_charts:
            # Create sample OHLCV data for demonstration
            dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
            sample_ohlcv = pd.DataFrame({
                'date': dates,
                'open': np.random.uniform(100, 110, 100),
                'high': np.random.uniform(110, 120, 100),
                'low': np.random.uniform(90, 100, 100),
                'close': np.random.uniform(100, 110, 100),
                'volume': np.random.uniform(1000, 5000, 100)
            })
            
            # Use first result for demonstration
            if results:
                fig = advanced_charts.create_ohlcv_chart_with_trades(sample_ohlcv, results[0].trades)
                st.plotly_chart(fig, width='stretch', config=self.chart_config)
            else:
                st.info("No results available for OHLCV chart")
        
        # Individual strategy analysis
        if len(results) > 1:
            st.subheader("Individual Strategy Analysis")
            
            selected_strategy = st.selectbox(
                "Select Strategy for Detailed Analysis",
                [result.strategy_name for result in results]
            )
            
            selected_result = next(
                (r for r in results if r.strategy_name == selected_strategy),
                None
            )
            
            if selected_result:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Trade distribution
                    fig = self.create_trade_distribution_chart(selected_result)
                    st.plotly_chart(fig, width='stretch', config=self.chart_config)
                
                with col2:
                    # Strategy metrics
                    metrics = selected_result.metrics
                    st.metric("Total Return", f"{metrics.total_return_pct:.2f}%")
                    st.metric("Win Rate", f"{metrics.win_rate:.2f}%")
                    st.metric("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%")
                    st.metric("Sharpe Ratio", f"{metrics.sharpe_ratio:.3f}")
                    st.metric("Total Trades", metrics.total_trades)