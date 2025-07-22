# Sample BBRSI Strategy for demonstration
import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy.interface import IStrategy

class SampleBBRSI(IStrategy):
    """
    Sample Bollinger Bands + RSI Strategy
    This strategy uses Bollinger Bands and RSI indicators to generate buy/sell signals
    """
    
    INTERFACE_VERSION = 2
    
    # Strategy parameters
    minimal_roi = {
        "0": 0.215,
        "21": 0.055,
        "48": 0.013,
        "125": 0
    }
    
    stoploss = -0.36
    timeframe = '4h'
    startup_candle_count: int = 30
    
    # Optional order type mapping
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate technical indicators
        """
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_middleband'] = bollinger['mid']
        
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Generate buy signals based on RSI and Bollinger Bands
        """
        dataframe.loc[
            (
                (dataframe['rsi'] > 25) &  # RSI above oversold
                (dataframe['close'] < dataframe['bb_lowerband'])  # Price below lower BB
            ),
            'buy'] = 1
        
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Generate sell signals based on RSI and Bollinger Bands
        """
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) &  # RSI in overbought territory
                (dataframe['close'] > dataframe['bb_upperband'])  # Price above upper BB
            ),
            'sell'] = 1
        
        return dataframe