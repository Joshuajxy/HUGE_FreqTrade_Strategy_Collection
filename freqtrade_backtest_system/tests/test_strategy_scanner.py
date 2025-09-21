"""
Unit tests for strategy scanner component
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from components.strategy_manager.scanner import StrategyScanner
from utils.data_models import StrategyInfo


class TestStrategyScanner:
    """Test cases for StrategyScanner class"""
    
    def test_init_with_default_path(self):
        """Test initialization with default path"""
        scanner = StrategyScanner()
        assert len(scanner.base_paths) == 1
        assert str(scanner.base_paths[0]) == "."

    def test_init_with_custom_paths(self):
        """Test initialization with custom paths"""
        paths = ["../strategies", "./custom"]
        scanner = StrategyScanner(paths)
        assert len(scanner.base_paths) == 2
        # Handle Windows path separator and normalization
        assert str(scanner.base_paths[0]).replace("\\", "/") == "../strategies"
        # For relative paths like "./custom", Path normalizes it to "custom"
        assert str(scanner.base_paths[1]) in ["./custom", "custom", ".\\custom", "custom"]
    
    def test_find_python_files(self):
        """Test finding Python files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            (tmp_path / "test1.py").touch()
            (tmp_path / "test2.py").touch()
            (tmp_path / "test.txt").touch()
            (tmp_path / "__pycache__").mkdir()
            (tmp_path / "__pycache__" / "cached.py").touch()
            
            scanner = StrategyScanner([str(tmp_path)])
            files = scanner._find_python_files(tmp_path)
            
            # Should find only the .py files, excluding __pycache__
            assert len(files) == 2
            filenames = [f.name for f in files]
            assert "test1.py" in filenames
            assert "test2.py" in filenames
            assert "test.txt" not in filenames
            assert "cached.py" not in filenames
    
    def test_quick_strategy_check(self):
        """Test quick strategy check"""
        scanner = StrategyScanner()
        
        # Valid strategy content
        valid_content = """
class MyStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        return dataframe
        
    def populate_entry_trend(self, dataframe, metadata):
        return dataframe
        
    def populate_exit_trend(self, dataframe, metadata):
        return dataframe
"""
        
        # Invalid strategy content
        invalid_content = """
class MyStrategy:
    def some_method(self):
        pass
"""
        
        assert scanner._quick_strategy_check(valid_content) == True
        assert scanner._quick_strategy_check(invalid_content) == False
    
    def test_extract_author_info(self):
        """Test extracting author information"""
        scanner = StrategyScanner()
        
        # Test different author patterns
        content1 = '__author__ = "John Doe"'
        content2 = '# @author: Jane Smith'
        content3 = '# Author: Bob Wilson'
        content4 = '# Created by: Alice Brown'
        
        assert scanner._extract_author_info(content1) == "John Doe"
        assert scanner._extract_author_info(content2) == "Jane Smith"
        assert scanner._extract_author_info(content3) == "Bob Wilson"
        assert scanner._extract_author_info(content4) == "Alice Brown"
    
    def test_extract_version_info(self):
        """Test extracting version information"""
        scanner = StrategyScanner()
        
        # Test different version patterns
        content1 = '__version__ = "1.0.0"'
        content2 = '# @version: 2.1.3'
        content3 = '# Version: v3.2.1'
        content4 = '# v4.0.0'
        
        assert scanner._extract_version_info(content1) == "1.0.0"
        assert scanner._extract_version_info(content2) == "2.1.3"
        assert scanner._extract_version_info(content3) == "v3.2.1"
        assert scanner._extract_version_info(content4) == "4.0.0"
    
    def test_is_strategy_class(self):
        """Test checking if a class is a strategy class"""
        import ast
        
        scanner = StrategyScanner()
        
        # Valid strategy class AST
        valid_code = """
class MyStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        return dataframe
        
    def populate_entry_trend(self, dataframe, metadata):
        return dataframe
"""
        
        # Invalid class AST
        invalid_code = """
class MyStrategy:
    def some_method(self):
        pass
"""
        
        valid_tree = ast.parse(valid_code)
        invalid_tree = ast.parse(invalid_code)
        
        valid_class = valid_tree.body[0]
        invalid_class = invalid_tree.body[0]
        
        assert scanner._is_strategy_class(valid_class) == True
        assert scanner._is_strategy_class(invalid_class) == False


if __name__ == "__main__":
    pytest.main([__file__])
