"""
Advanced charting components for backtest results visualization
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Optional
from utils.data_models import BacktestResult, TradeRecord


class AdvancedCharts:
    """Advanced charting components"""

    def create_equity_curve(self, results: List[BacktestResult]):
        """
        Create equity curve chart for multiple strategies
        Args:
            results: list of backtest results
        Returns:
            plotly figure
        """
        fig = go.Figure()
        for result in results:
            df = pd.DataFrame([trade.__dict__ for trade in result.trades])
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values(by='timestamp')
                df['cumulative_profit'] = df['profit'].cumsum()
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['cumulative_profit'], 
                                       mode='lines', name=result.strategy_name))
        
        fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Cumulative Profit')
        return fig

    def create_drawdown_plot(self, result: BacktestResult):
        """
        Create drawdown plot for a strategy
        Args:
            result: backtest result
        Returns:
            plotly figure
        """
        df = pd.DataFrame([trade.__dict__ for trade in result.trades])
        if df.empty or 'timestamp' not in df.columns:
            # Return empty figure if no data
            fig = go.Figure()
            fig.add_annotation(text="No trade data available", xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False, font=dict(size=16))
            return fig
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp')
        df['cumulative_profit'] = df['profit'].cumsum()
        df['peak'] = df['cumulative_profit'].cummax()
        df['drawdown'] = df['peak'] - df['cumulative_profit']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['drawdown'], 
                               fill='tozeroy', mode='lines', name='Drawdown'))
        fig.update_layout(title='Drawdown Plot', xaxis_title='Date', yaxis_title='Drawdown')
        return fig

    def create_trade_markers_chart(self, result: BacktestResult, ohlcv: pd.DataFrame):
        """
        Create candlestick chart with trade markers
        Args:
            result: backtest result
            ohlcv: OHLCV data DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
        Returns:
            plotly figure
        """
        # Create subplots with price and volume
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05,
                           row_heights=[0.7, 0.3],
                           subplot_titles=('Price Action', 'Volume'))
        
        # Add candlestick chart
        fig.add_trace(go.Candlestick(x=ohlcv['date'],
                                   open=ohlcv['open'],
                                   high=ohlcv['high'],
                                   low=ohlcv['low'],
                                   close=ohlcv['close'],
                                   name='OHLC'), row=1, col=1)
        
        # Add volume bars
        fig.add_trace(go.Bar(x=ohlcv['date'], y=ohlcv['volume'], 
                           name='Volume', marker_color='lightblue'), row=2, col=1)
        
        # Add trade markers
        buys = [trade for trade in result.trades if trade.side == 'buy']
        sells = [trade for trade in result.trades if trade.side == 'sell']
        
        if buys:
            buy_dates = [trade.timestamp for trade in buys]
            buy_prices = [trade.price for trade in buys]
            fig.add_trace(go.Scatter(x=buy_dates, y=buy_prices, mode='markers', 
                                   name='Buys', marker=dict(color='green', size=10, symbol='triangle-up')),
                         row=1, col=1)
        
        if sells:
            sell_dates = [trade.timestamp for trade in sells]
            sell_prices = [trade.price for trade in sells]
            fig.add_trace(go.Scatter(x=sell_dates, y=sell_prices, mode='markers', 
                                   name='Sells', marker=dict(color='red', size=10, symbol='triangle-down')),
                         row=1, col=1)
        
        fig.update_layout(title=f'Trade Analysis - {result.strategy_name}', 
                         xaxis_title='Date', yaxis_title='Price',
                         height=600)
        fig.update_xaxes(rangeslider_visible=False)
        return fig

    def create_ohlcv_chart_with_trades(self, ohlcv: pd.DataFrame, trades: List[TradeRecord]):
        """
        Create comprehensive OHLCV chart with trade markers and volume
        Args:
            ohlcv: OHLCV data DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
            trades: list of trade records
        Returns:
            plotly figure
        """
        # Validate OHLCV data
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in ohlcv.columns for col in required_columns):
            raise ValueError(f"OHLCV data must contain columns: {required_columns}")
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Price Action', 'Volume', 'Trade Points')
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=ohlcv['date'],
                open=ohlcv['open'],
                high=ohlcv['high'],
                low=ohlcv['low'],
                close=ohlcv['close'],
                name='OHLC',
                increasing_line_color='#2E8B57',  # Sea Green
                decreasing_line_color='#DC143C'   # Crimson
            ), 
            row=1, col=1
        )
        
        # Add volume bars
        colors = ['lightcoral' if close < open else 'lightgreen' 
                 for close, open in zip(ohlcv['close'], ohlcv['open'])]
        
        fig.add_trace(
            go.Bar(
                x=ohlcv['date'],
                y=ohlcv['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ), 
            row=2, col=1
        )
        
        # Add trade markers
        if trades:
            buy_trades = [t for t in trades if t.side.lower() == 'buy']
            sell_trades = [t for t in trades if t.side.lower() == 'sell']
            
            # Buy markers
            if buy_trades:
                buy_dates = [t.timestamp for t in buy_trades]
                buy_prices = [t.price for t in buy_trades]
                buy_amounts = [t.amount for t in buy_trades]
                
                # Scale marker size by trade amount
                marker_sizes = [max(8, min(20, amount * 10)) for amount in buy_amounts] if buy_amounts else [10] * len(buy_trades)
                
                fig.add_trace(
                    go.Scatter(
                        x=buy_dates,
                        y=buy_prices,
                        mode='markers',
                        name='Buy Orders',
                        marker=dict(
                            color='blue',
                            size=marker_sizes,
                            symbol='triangle-up',
                            line=dict(width=1, color='darkblue')
                        ),
                        hovertemplate='<b>Buy</b><br>Date: %{x}<br>Price: %{y}<br>Amount: %{marker.size}<extra></extra>'
                    ), 
                    row=1, col=1
                )
            
            # Sell markers
            if sell_trades:
                sell_dates = [t.timestamp for t in sell_trades]
                sell_prices = [t.price for t in sell_trades]
                sell_amounts = [t.amount for t in sell_trades]
                
                # Scale marker size by trade amount
                marker_sizes = [max(8, min(20, amount * 10)) for amount in sell_amounts] if sell_amounts else [10] * len(sell_trades)
                
                fig.add_trace(
                    go.Scatter(
                        x=sell_dates,
                        y=sell_prices,
                        mode='markers',
                        name='Sell Orders',
                        marker=dict(
                            color='red',
                            size=marker_sizes,
                            symbol='triangle-down',
                            line=dict(width=1, color='darkred')
                        ),
                        hovertemplate='<b>Sell</b><br>Date: %{x}<br>Price: %{y}<br>Amount: %{marker.size}<extra></extra>'
                    ), 
                    row=1, col=1
                )
        
        # Add trade points on separate subplot
        if trades:
            trade_dates = [t.timestamp for t in trades]
            trade_prices = [t.price for t in trades]
            trade_colors = ['blue' if t.side.lower() == 'buy' else 'red' for t in trades]
            trade_symbols = ['triangle-up' if t.side.lower() == 'buy' else 'triangle-down' for t in trades]
            
            fig.add_trace(
                go.Scatter(
                    x=trade_dates,
                    y=trade_prices,
                    mode='markers',
                    name='All Trades',
                    marker=dict(
                        color=trade_colors,
                        size=8,
                        symbol=trade_symbols
                    ),
                    showlegend=False
                ), 
                row=3, col=1
            )
        
        # Update layout
        fig.update_layout(
            title='Comprehensive OHLCV Chart with Trade Markers',
            height=800,
            template='plotly_white',
            hovermode='x unified'
        )
        
        # Update axes
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="Price", row=3, col=1)
        
        # Remove range slider from first subplot
        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
        
        return fig

    def create_performance_comparison_chart(self, results: List[BacktestResult]):
        """
        Create performance comparison chart for multiple strategies
        Args:
            results: list of backtest results
        Returns:
            plotly figure
        """
        if not results:
            fig = go.Figure()
            fig.add_annotation(text="No data available", xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False, font=dict(size=16))
            return fig
        
        # Extract metrics for comparison
        strategy_names = [r.strategy_name for r in results]
        returns = [r.metrics.total_return_pct for r in results]
        win_rates = [r.metrics.win_rate for r in results]
        max_drawdowns = [abs(r.metrics.max_drawdown_pct) for r in results]
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Total Return %', 'Win Rate %', 'Max Drawdown %', 'Risk-Return Profile'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Total Return chart
        fig.add_trace(
            go.Bar(x=strategy_names, y=returns, name='Total Return %', marker_color='lightblue'),
            row=1, col=1
        )
        
        # Win Rate chart
        fig.add_trace(
            go.Bar(x=strategy_names, y=win_rates, name='Win Rate %', marker_color='lightgreen'),
            row=1, col=2
        )
        
        # Max Drawdown chart
        fig.add_trace(
            go.Bar(x=strategy_names, y=max_drawdowns, name='Max Drawdown %', marker_color='lightcoral'),
            row=2, col=1
        )
        
        # Risk-Return scatter plot
        colors = ['red' if dd > 10 else 'orange' if dd > 5 else 'green' for dd in max_drawdowns]
        fig.add_trace(
            go.Scatter(
                x=max_drawdowns, y=returns,
                mode='markers+text',
                text=strategy_names,
                textposition="top center",
                marker=dict(size=[max(10, r.metrics.sharpe_ratio * 5) for r in results],
                           color=colors),
                name='Risk-Return'
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="Strategy Performance Comparison")
        return fig