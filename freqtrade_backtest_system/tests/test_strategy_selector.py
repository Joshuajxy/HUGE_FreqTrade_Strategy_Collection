"""
Unit tests for strategy selector component
"""
import pytest
import streamlit as st
from datetime import datetime
from pathlib import Path

from components.strategy_manager.selector import StrategySelector
from utils.data_models import StrategyInfo


class TestStrategySelector:
    """Test cases for StrategySelector class"""
    
    def test_init(self):
        """Test initialization"""
        selector = StrategySelector()
        assert selector.selected_strategies == []
        assert selector.search_term == ""
        assert selector.filter_criteria == {}
    
    def test_format_file_size(self):
        """Test file size formatting"""
        selector = StrategySelector()
        
        assert selector._format_file_size(512) == "512 B"
        assert selector._format_file_size(1024) == "1.0 KB"
        assert selector._format_file_size(1024 * 1024) == "1.0 MB"
        assert selector._format_file_size(1024 * 1024 * 1.5) == "1.5 MB"
    
    def test_filter_strategies_by_search(self):
        """Test filtering strategies by search term"""
        selector = StrategySelector()
        selector.search_term = "test"
        
        strategies = [
            StrategyInfo(
                name="TestStrategy1",
                file_path=Path("test1.py"),
                description="A test strategy",
                author="Tester",
                version="1.0"
            ),
            StrategyInfo(
                name="AnotherStrategy",
                file_path=Path("another.py"),
                description="Another strategy",
                author="Developer",
                version="1.0"
            )
        ]
        
        filtered = selector._filter_strategies(strategies)
        assert len(filtered) == 1
        assert filtered[0].name == "TestStrategy1"
    
    def test_filter_strategies_by_author(self):
        """Test filtering strategies by author"""
        selector = StrategySelector()
        selector.filter_criteria = {'author': 'Tester'}
        
        strategies = [
            StrategyInfo(
                name="TestStrategy1",
                file_path=Path("test1.py"),
                description="A test strategy",
                author="Tester",
                version="1.0"
            ),
            StrategyInfo(
                name="AnotherStrategy",
                file_path=Path("another.py"),
                description="Another strategy",
                author="Developer",
                version="1.0"
            )
        ]
        
        filtered = selector._filter_strategies(strategies)
        assert len(filtered) == 1
        assert filtered[0].name == "TestStrategy1"
    
    def test_extract_imports(self):
        """Test extracting imports from strategy content"""
        selector = StrategySelector()
        
        content = """
import pandas as pd
from freqtrade.strategy import IStrategy
import talib
from datetime import datetime

class MyStrategy(IStrategy):
    pass
"""
        
        imports = selector._extract_imports(content)
        assert len(imports) == 4
        assert "import pandas as pd" in imports
        assert "from freqtrade.strategy import IStrategy" in imports
        assert "import talib" in imports
        assert "from datetime import datetime" in imports
    
    def test_extract_methods(self):
        """Test extracting methods from strategy content"""
        selector = StrategySelector()
        
        content = """
class MyStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        return dataframe
        
    def populate_entry_trend(self, dataframe, metadata):
        return dataframe
        
    def populate_exit_trend(self, dataframe, metadata):
        return dataframe
        
    def custom_method(self):
        pass
"""
        
        methods = selector._extract_methods(content)
        assert len(methods) == 4
        assert "populate_indicators" in methods
        assert "populate_entry_trend" in methods
        assert "populate_exit_trend" in methods
        assert "custom_method" in methods
    
    def test_infer_type(self):
        """Test inferring parameter types"""
        selector = StrategySelector()
        
        assert selector._infer_type('"string"') == "string"
        assert selector._infer_type("'another string'") == "string"
        assert selector._infer_type('True') == "boolean"
        assert selector._infer_type('False') == "boolean"
        assert selector._infer_type('123') == "number"
        assert selector._infer_type('123.45') == "number"
        assert selector._infer_type('-123.45') == "number"
        assert selector._infer_type('[1, 2, 3]') == "list"
        assert selector._infer_type('{"key": "value"}') == "dict"
        assert selector._infer_type('unknown') == "unknown"


if __name__ == "__main__":
    pytest.main([__file__])