"""
Strategy file scanner
"""
import ast
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from utils.data_models import StrategyInfo
from utils.error_handling import ErrorHandler, StrategyError, error_handler

class StrategyScanner:
    """Strategy file scanner"""
    
    def __init__(self, base_paths: List[str] = None):
        """
        Initialize scanner
        
        Args:
            base_paths: list of base paths to scan, defaults to current directory
        """
        self.base_paths = [Path(path) for path in (base_paths or ["."])]
        
        # File patterns to exclude
        self.exclude_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv"
        ]
        
        # Strategy class identifiers
        self.strategy_indicators = [
            "IStrategy",
            "populate_indicators",
            "populate_entry_trend",
            "populate_exit_trend"
        ]
    
    @error_handler(StrategyError, show_error=False)
    def scan_strategies(self, use_cache: bool = False) -> List[StrategyInfo]:
        """
        Scan and identify strategy files
        
        Args:
            use_cache: whether to use cached results
            
        Returns:
            list of strategy information
        """
        ErrorHandler.log_info(f"Starting strategy file scan: {', '.join(str(p) for p in self.base_paths)}")
        
        strategies = []
        
        try:
            for base_path in self.base_paths:
                if not base_path.exists():
                    ErrorHandler.log_warning(f"Scan path does not exist: {base_path}")
                    continue
                
                # Recursively scan Python files
                python_files = self._find_python_files(base_path)
                
                for py_file in python_files:
                    strategy_info = self._analyze_strategy_file(py_file)
                    if strategy_info:
                        strategies.append(strategy_info)
            
            ErrorHandler.log_info(f"Scan completed, found {len(strategies)} strategies")
            return strategies
        
        except Exception as e:
            ErrorHandler.log_error(f"Strategy scan failed: {str(e)}")
            raise StrategyError(f"Strategy scan failed: {str(e)}")
    
    def _find_python_files(self, base_path: Path) -> List[Path]:
        """Find all Python files in the given path"""
        python_files = []
        
        try:
            # Use glob to find all .py files recursively
            for py_file in base_path.rglob("*.py"):
                # Skip excluded directories
                if any(exclude in str(py_file) for exclude in self.exclude_patterns):
                    continue
                
                # Skip files that are too large (>1MB)
                if py_file.stat().st_size > 1024 * 1024:
                    continue
                
                python_files.append(py_file)
        
        except Exception as e:
            ErrorHandler.log_warning(f"Error finding Python files in {base_path}: {str(e)}")
        
        return python_files
    
    def _analyze_strategy_file(self, file_path: Path) -> Optional[StrategyInfo]:
        """Analyze a Python file to determine if it's a strategy"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Quick text-based check first
            if not self._quick_strategy_check(content):
                return None
            
            # Parse AST for detailed analysis
            strategy_info = self._parse_strategy_ast(file_path, content)
            
            if strategy_info:
                # Get file modification time
                strategy_info.last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                ErrorHandler.log_info(f"Strategy found: {strategy_info.name} in {file_path}")
                return strategy_info
        
        except Exception as e:
            ErrorHandler.log_warning(f"Error analyzing file {file_path}: {str(e)}")
        
        return None
    
    def _quick_strategy_check(self, content: str) -> bool:
        """Quick text-based check for strategy indicators"""
        # Check for required strategy components
        required_count = 0
        
        for indicator in self.strategy_indicators:
            if indicator in content:
                required_count += 1
        
        # Need at least 3 out of 4 indicators
        return required_count >= 3
    
    def _parse_strategy_ast(self, file_path: Path, content: str) -> Optional[StrategyInfo]:
        """Parse Python AST to extract strategy information"""
        try:
            # Parse the AST
            tree = ast.parse(content)
            
            # Find strategy class
            strategy_class = self._find_strategy_class(tree)
            
            if not strategy_class:
                return None
            
            # Extract strategy information
            strategy_name = strategy_class.name
            description = self._extract_class_docstring(strategy_class)
            author = self._extract_author_info(content)
            version = self._extract_version_info(content)
            
            return StrategyInfo(
                name=strategy_name,
                file_path=file_path,
                description=description or f"Strategy class: {strategy_name}",
                author=author,
                version=version
            )
        
        except SyntaxError as e:
            ErrorHandler.log_warning(f"Syntax error in {file_path}: {str(e)}")
            return None
        
        except Exception as e:
            ErrorHandler.log_warning(f"AST parsing error in {file_path}: {str(e)}")
            return None
    
    def _find_strategy_class(self, tree: ast.AST) -> Optional[ast.ClassDef]:
        """Find the strategy class in the AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if class inherits from IStrategy or has strategy methods
                if self._is_strategy_class(node):
                    return node
        
        return None
    
    def _is_strategy_class(self, class_node: ast.ClassDef) -> bool:
        """Check if a class is a strategy class"""
        # Check inheritance
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id == "IStrategy":
                return True
        
        # Check for required methods
        method_names = []
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
        
        required_methods = ["populate_indicators", "populate_entry_trend", "populate_exit_trend"]
        found_methods = sum(1 for method in required_methods if method in method_names)
        
        return found_methods >= 2  # At least 2 out of 3 required methods
    
    def _extract_class_docstring(self, class_node: ast.ClassDef) -> Optional[str]:
        """Extract docstring from class"""
        if (class_node.body and 
            isinstance(class_node.body[0], ast.Expr) and 
            isinstance(class_node.body[0].value, ast.Constant) and 
            isinstance(class_node.body[0].value.value, str)):
            
            return class_node.body[0].value.value.strip()
        
        return None
    
    def _extract_author_info(self, content: str) -> Optional[str]:
        """Extract author information from file content"""
        # Look for common author patterns
        author_patterns = [
            r'__author__\s*=\s*["\']([^"\']+)["\']',
            r'@author[:\s]+([^\n]+)',
            r'Author[:\s]+([^\n]+)',
            r'Created by[:\s]+([^\n]+)'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_version_info(self, content: str) -> Optional[str]:
        """Extract version information from file content"""
        # Look for common version patterns
        version_patterns = [
            r'__version__\s*=\s*["\']([^"\']+)["\']',
            r'@version[:\s]+([^\n]+)',
            r'Version[:\s]+([^\n]+)',
            r'v(\d+\.\d+(?:\.\d+)?)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def get_strategy_details(self, strategy_info: StrategyInfo) -> Dict[str, Any]:
        """
        Get detailed information about a strategy
        
        Args:
            strategy_info: strategy information object
            
        Returns:
            detailed strategy information dictionary
        """
        details = {
            'name': strategy_info.name,
            'file_path': str(strategy_info.file_path),
            'description': strategy_info.description,
            'author': strategy_info.author,
            'version': strategy_info.version,
            'last_modified': strategy_info.last_modified.isoformat() if strategy_info.last_modified else None,
            'file_size': 0,
            'line_count': 0,
            'methods': [],
            'parameters': []
        }
        
        try:
            # Get file statistics
            file_stat = strategy_info.file_path.stat()
            details['file_size'] = file_stat.st_size
            
            # Read file content for analysis
            with open(strategy_info.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            details['line_count'] = len(content.splitlines())
            
            # Parse AST for method and parameter information
            tree = ast.parse(content)
            strategy_class = self._find_strategy_class(tree)
            
            if strategy_class:
                # Extract methods
                for node in strategy_class.body:
                    if isinstance(node, ast.FunctionDef):
                        details['methods'].append({
                            'name': node.name,
                            'args': [arg.arg for arg in node.args.args if arg.arg != 'self'],
                            'docstring': self._extract_function_docstring(node)
                        })
                
                # Extract class-level parameters
                for node in strategy_class.body:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                details['parameters'].append({
                                    'name': target.id,
                                    'type': type(node.value).__name__,
                                    'value': self._get_node_value(node.value)
                                })
        
        except Exception as e:
            ErrorHandler.log_warning(f"Error getting strategy details: {str(e)}")
        
        return details
    
    def _extract_function_docstring(self, func_node: ast.FunctionDef) -> Optional[str]:
        """Extract docstring from function"""
        if (func_node.body and 
            isinstance(func_node.body[0], ast.Expr) and 
            isinstance(func_node.body[0].value, ast.Constant) and 
            isinstance(func_node.body[0].value.value, str)):
            
            return func_node.body[0].value.value.strip()
        
        return None
    
    def _get_node_value(self, node: ast.AST) -> Any:
        """Get value from AST node"""
        try:
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Name):
                return f"<{node.id}>"
            elif isinstance(node, ast.List):
                return [self._get_node_value(item) for item in node.elts]
            elif isinstance(node, ast.Dict):
                return {self._get_node_value(k): self._get_node_value(v) 
                       for k, v in zip(node.keys, node.values)}
            else:
                return f"<{type(node).__name__}>"
        except:
            return "<unknown>"
    
    def validate_strategy_file(self, file_path: Path) -> tuple[bool, List[str]]:
        """
        Validate strategy file
        
        Args:
            file_path: strategy file path
            
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check file existence
            if not file_path.exists():
                errors.append(f"File does not exist: {file_path}")
                return False, errors
            
            # Check file extension
            if file_path.suffix != '.py':
                errors.append("File must have .py extension")
            
            # Read and parse file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"Syntax error: {str(e)}")
            
            # Check for strategy components
            if not self._quick_strategy_check(content):
                errors.append("File does not appear to contain a valid strategy")
            
            # Check for required methods
            tree = ast.parse(content)
            strategy_class = self._find_strategy_class(tree)
            
            if not strategy_class:
                errors.append("No valid strategy class found")
            else:
                # Check for required methods
                method_names = [node.name for node in strategy_class.body 
                              if isinstance(node, ast.FunctionDef)]
                
                required_methods = ["populate_indicators", "populate_entry_trend", "populate_exit_trend"]
                missing_methods = [method for method in required_methods 
                                 if method not in method_names]
                
                if missing_methods:
                    errors.append(f"Missing required methods: {', '.join(missing_methods)}")
        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return len(errors) == 0, errors