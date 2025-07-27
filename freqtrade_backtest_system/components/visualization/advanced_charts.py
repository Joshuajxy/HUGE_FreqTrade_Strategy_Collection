import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List
from freqtrade_backtest_system.utils.data_models import BacktestResult

class AdvancedCharts:

    def create_equity_curve(self, results: List[BacktestResult]):
        fig = go.Figure()
        for result in results:
            df = pd.DataFrame(result.trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp')
            df['cumulative_profit'] = df['profit'].cumsum()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['cumulative_profit'], mode='lines', name=result.strategy_name))
        
        fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Cumulative Profit')
        return fig

    def create_drawdown_plot(self, result: BacktestResult):
        df = pd.DataFrame(result.trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp')
        df['cumulative_profit'] = df['profit'].cumsum()
        df['peak'] = df['cumulative_profit'].cummax()
        df['drawdown'] = df['peak'] - df['cumulative_profit']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['drawdown'], fill='tozeroy', mode='lines', name='Drawdown'))
        fig.update_layout(title='Drawdown Plot', xaxis_title='Date', yaxis_title='Drawdown')
        return fig

    def create_trade_markers_chart(self, result: BacktestResult, ohlcv: pd.DataFrame):
        fig = go.Figure(data=[go.Candlestick(x=ohlcv['date'],
                                               open=ohlcv['open'],
                                               high=ohlcv['high'],
                                               low=ohlcv['low'],
                                               close=ohlcv['close'])])

        buys = [trade for trade in result.trades if trade.side == 'buy']
        sells = [trade for trade in result.trades if trade.side == 'sell']

        buy_dates = [trade.timestamp for trade in buys]
        buy_prices = [trade.price for trade in buys]

        sell_dates = [trade.timestamp for trade in sells]
        sell_prices = [trade.price for trade in sells]

        fig.add_trace(go.Scatter(x=buy_dates, y=buy_prices, mode='markers', name='Buys', marker=dict(color='green', size=10, symbol='triangle-up')))
        fig.add_trace(go.Scatter(x=sell_dates, y=sell_prices, mode='markers', name='Sells', marker=dict(color='red', size=10, symbol='triangle-down')))

        fig.update_layout(title='Trade Markers', xaxis_title='Date', yaxis_title='Price')
        return fig
