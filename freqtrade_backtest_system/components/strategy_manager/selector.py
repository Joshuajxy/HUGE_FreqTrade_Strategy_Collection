"""
Strategy selection interface
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils.data_models import StrategyInfo
from utils.error_handling import ErrorHandler


class StrategySelector:
    """Strategy selection interface"""
    
    def __init__(self):
        """Initialize strategy selector"""
        self.selected_strategies = []
        self.search_term = ""
        self.filter_criteria = {}
    
    def render_strategy_selection(self, strategies: List[StrategyInfo]) -> List[StrategyInfo]:
        """
        Render strategy selection interface
        
        Args:
            strategies: list of strategy information
            
        Returns:
            list of selected StrategyInfo objects
        """
        if not strategies:
            st.info("No strategies found. Please scan for strategy files first.")
            return []
        
        # Create a quick lookup map
        strategy_map = {s.name: s for s in strategies}

        # Search and filter controls
        self._render_search_controls(strategies)
        
        # Filter strategies based on search and filters
        filtered_strategies = self._filter_strategies(strategies)
        
        # Strategy selection interface (returns list of names)
        selected_strategy_names = self._render_strategy_table(filtered_strategies)
        
        # Selection summary
        self._render_selection_summary(selected_strategy_names, len(strategies))
        
        # Convert selected names back to StrategyInfo objects
        selected_strategy_objects = [strategy_map[name] for name in selected_strategy_names if name in strategy_map]

        return selected_strategy_objects
    
    def _render_search_controls(self, strategies: List[StrategyInfo]):
        """Render search and filter controls"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            self.search_term = st.text_input(
                "🔍 Search Strategies",
                value=self.search_term,
                placeholder="Enter strategy name or description...",
                help="Search by strategy name, description, or author"
            )
        
        with col2:
            # Author filter
            authors = list(set([s.author for s in strategies if s.author]))
            if authors:
                selected_author = st.selectbox(
                    "👤 Filter by Author",
                    ["All"] + authors,
                    help="Filter strategies by author"
                )
                self.filter_criteria['author'] = None if selected_author == "All" else selected_author
        
        with col3:
            # Sort options
            sort_options = {
                "Name (A-Z)": "name_asc",
                "Name (Z-A)": "name_desc", 
                "Modified (Newest)": "modified_desc",
                "Modified (Oldest)": "modified_asc"
            }
            
            sort_by = st.selectbox(
                "📊 Sort by",
                list(sort_options.keys()),
                help="Sort strategies by different criteria"
            )
            self.filter_criteria['sort'] = sort_options[sort_by]
    
    def _filter_strategies(self, strategies: List[StrategyInfo]) -> List[StrategyInfo]:
        """Filter strategies based on search term and criteria"""
        filtered = strategies.copy()
        
        # Apply search filter
        if self.search_term:
            search_lower = self.search_term.lower()
            filtered = [
                s for s in filtered
                if (search_lower in s.name.lower() or
                    search_lower in (s.description or "").lower() or
                    search_lower in (s.author or "").lower())
            ]
        
        # Apply author filter
        if self.filter_criteria.get('author'):
            filtered = [s for s in filtered if s.author == self.filter_criteria['author']]
        
        # Apply sorting
        sort_key = self.filter_criteria.get('sort', 'name_asc')
        
        if sort_key == 'name_asc':
            filtered.sort(key=lambda x: x.name.lower())
        elif sort_key == 'name_desc':
            filtered.sort(key=lambda x: x.name.lower(), reverse=True)
        elif sort_key == 'modified_desc':
            filtered.sort(key=lambda x: x.last_modified or 0, reverse=True)
        elif sort_key == 'modified_asc':
            filtered.sort(key=lambda x: x.last_modified or 0)
        
        return filtered
    
    def _render_strategy_table(self, strategies: List[StrategyInfo]) -> List[str]:
        """Render strategy selection as a table with checkboxes"""
        if not strategies:
            st.warning("No strategies match your search criteria.")
            return []
        
        # Initialize session state for selected strategies
        if 'selected_strategies' not in st.session_state:
            st.session_state.selected_strategies = []
        
        # Batch selection controls
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Select All", width='stretch'):
                st.session_state.selected_strategies = [s.name for s in strategies]
                st.rerun()
        
        with col2:
            if st.button("❌ Clear All", width='stretch'):
                st.session_state.selected_strategies = []
                st.rerun()
        
        # Prepare table data
        table_data = []
        for strategy in strategies:
            try:
                file_size = strategy.file_path.stat().st_size
                formatted_size = self._format_file_size(file_size)
            except:
                formatted_size = "N/A"
            
            # Check if strategy is selected
            is_selected = strategy.name in st.session_state.selected_strategies
            
            row = {
                "Select": is_selected,
                "Strategy Name": strategy.name,
                "File Name": strategy.file_path.name,
                "Author": strategy.author or "Unknown",
                "Version": strategy.version or "N/A",
                "Modified": strategy.last_modified.strftime('%Y-%m-%d %H:%M') if strategy.last_modified else "N/A",
                "Size": formatted_size,
                "Description": (strategy.description or "")[:50] + "..." if strategy.description and len(strategy.description) > 50 else strategy.description or ""
            }
            table_data.append(row)
        
        # Create DataFrame for the table
        import pandas as pd
        df = pd.DataFrame(table_data)
        
        # Display the table with selection
        st.subheader("Strategy Selection Table")
        
        # Display editable table
        edited_df = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select strategies for backtesting",
                    default=False,
                ),
                "Strategy Name": st.column_config.TextColumn(
                    "Strategy Name",
                    help="Name of the strategy",
                ),
                "File Name": st.column_config.TextColumn(
                    "File Name",
                    help="Strategy file name",
                ),
                "Author": st.column_config.TextColumn(
                    "Author",
                    help="Strategy author",
                ),
                "Version": st.column_config.TextColumn(
                    "Version",
                    help="Strategy version",
                ),
                "Modified": st.column_config.TextColumn(
                    "Modified",
                    help="Last modification date",
                ),
                "Size": st.column_config.TextColumn(
                    "Size",
                    help="File size",
                ),
                "Description": st.column_config.TextColumn(
                    "Description",
                    help="Strategy description",
                    width="medium",
                )
            },
            disabled=["Strategy Name", "File Name", "Author", "Version", "Modified", "Size", "Description"],
            hide_index=True,
            width='stretch',
            height=600,
        )
        
        # Update session state based on selections
        selected_strategies = [
            row["Strategy Name"] for _, row in edited_df.iterrows() if row["Select"]
        ]
        
        st.session_state.selected_strategies = selected_strategies
        
        # Show selection summary
        st.success(f"✅ Selected {len(selected_strategies)} out of {len(strategies)} strategies")
        
        return selected_strategies
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _render_selection_summary(self, selected_strategies: List[str], total_strategies: int):
        """Render selection summary"""
        if selected_strategies:
            st.success(f"✅ Selected {len(selected_strategies)} out of {total_strategies} strategies")
            
            # Show selected strategies
            with st.expander("📋 Selected Strategies", expanded=False):
                for i, strategy in enumerate(selected_strategies, 1):
                    st.write(f"{i}. {strategy}")
        else:
            st.info(f"📊 Found {total_strategies} strategies. Please select strategies to proceed.")
    
    def render_strategy_comparison_table(self, strategies: List[StrategyInfo]) -> List[str]:
        """
        Render strategy comparison table
        
        Args:
            strategies: list of strategy information
            
        Returns:
            list of selected strategy names
        """
        if not strategies:
            return []
        
        # Prepare data for table
        table_data = []
        for strategy in strategies:
            table_data.append({
                "Select": False,
                "Name": strategy.name,
                "Author": strategy.author or "Unknown",
                "Version": strategy.version or "N/A",
                "Modified": strategy.last_modified.strftime('%Y-%m-%d') if strategy.last_modified else "N/A",
                "File": strategy.file_path.name,
                "Description": (strategy.description or "")[:50] + "..." if strategy.description and len(strategy.description) > 50 else strategy.description or ""
            })
        
        # Display table with selection
        st.subheader("📊 Strategy Comparison Table")
        
        # Use st.data_editor for interactive table
        edited_data = st.data_editor(
            table_data,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select strategies for backtesting",
                    default=False,
                ),
                "Name": st.column_config.TextColumn(
                    "Strategy Name",
                    help="Name of the strategy",
                    max_chars=50,
                ),
                "Author": st.column_config.TextColumn(
                    "Author",
                    help="Strategy author",
                    max_chars=30,
                ),
                "Version": st.column_config.TextColumn(
                    "Version",
                    help="Strategy version",
                    max_chars=20,
                ),
                "Modified": st.column_config.TextColumn(
                    "Last Modified",
                    help="Last modification date",
                ),
                "File": st.column_config.TextColumn(
                    "File Name",
                    help="Strategy file name",
                ),
                "Description": st.column_config.TextColumn(
                    "Description",
                    help="Strategy description",
                    max_chars=100,
                )
            },
            disabled=["Name", "Author", "Version", "Modified", "File", "Description"],
            hide_index=True,
            width='stretch'
        )
        
        # Get selected strategies
        selected_strategies = [
            row["Name"] for row in edited_data if row["Select"]
        ]
        
        return selected_strategies
    
    def get_strategy_details(self, strategy_name: str, strategies: List[StrategyInfo]) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific strategy
        
        Args:
            strategy_name: name of the strategy
            strategies: list of all strategies
            
        Returns:
            detailed strategy information
        """
        strategy = next((s for s in strategies if s.name == strategy_name), None)
        
        if not strategy:
            return None
        
        try:
            # Read strategy file for additional analysis
            with open(strategy.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic file statistics
            lines = content.splitlines()
            
            details = {
                'name': strategy.name,
                'file_path': str(strategy.file_path),
                'author': strategy.author,
                'version': strategy.version,
                'description': strategy.description,
                'last_modified': strategy.last_modified.isoformat() if strategy.last_modified else None,
                'file_size': strategy.file_path.stat().st_size,
                'line_count': len(lines),
                'has_docstring': bool(strategy.description),
                'imports': self._extract_imports(content),
                'methods': self._extract_methods(content),
                'parameters': self._extract_parameters(content)
            }
            
            return details
        
        except Exception as e:
            ErrorHandler.log_warning(f"Error getting strategy details for {strategy_name}: {str(e)}")
            return None
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from strategy file"""
        imports = []
        lines = content.splitlines()
        
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return imports
    
    def _extract_methods(self, content: str) -> List[str]:
        """Extract method names from strategy file"""
        methods = []
        lines = content.splitlines()
        
        for line in lines:
            line = line.strip()
            if line.startswith('def ') and '(' in line:
                method_name = line.split('def ')[1].split('(')[0].strip()
                methods.append(method_name)
        
        return methods
    
    def _extract_parameters(self, content: str) -> List[Dict[str, str]]:
        """Extract class parameters from strategy file"""
        parameters = []
        lines = content.splitlines()
        
        in_class = False
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('class ') and 'IStrategy' in stripped:
                in_class = True
                continue
            
            if in_class and stripped.startswith('def '):
                break
            
            if in_class and '=' in stripped and not stripped.startswith('#'):
                if not stripped.startswith('def ') and not stripped.startswith('class '):
                    try:
                        param_name = stripped.split('=')[0].strip()
                        param_value = stripped.split('=')[1].strip()
                        
                        parameters.append({
                            'name': param_name,
                            'value': param_value,
                            'type': self._infer_type(param_value)
                        })
                    except:
                        pass
        
        return parameters
    
    def _infer_type(self, value: str) -> str:
        """Infer parameter type from string value"""
        value = value.strip()
        
        if value.startswith('"') or value.startswith("'"):
            return "string"
        elif value.lower() in ['true', 'false']:
            return "boolean"
        elif value.replace('.', '').replace('-', '').isdigit():
            return "number"
        elif value.startswith('[') and value.endswith(']'):
            return "list"
        elif value.startswith('{') and value.endswith('}'):
            return "dict"
        else:
            return "unknown"
    
    def render_strategy_validation(self, strategies: List[StrategyInfo]) -> Dict[str, bool]:
        """
        Render strategy validation interface
        
        Args:
            strategies: list of strategies to validate
            
        Returns:
            dictionary mapping strategy names to validation status
        """
        st.subheader("🔍 Strategy Validation")
        
        validation_results = {}
        
        if not strategies:
            st.info("No strategies to validate.")
            return validation_results
        
        # Validate each strategy
        for strategy in strategies:
            with st.expander(f"📋 {strategy.name}", expanded=False):
                try:
                    # Basic file checks
                    file_exists = strategy.file_path.exists()
                    is_python_file = strategy.file_path.suffix == '.py'
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**File Checks:**")
                        st.write(f"✅ File exists" if file_exists else "❌ File missing")
                        st.write(f"✅ Python file" if is_python_file else "❌ Not a Python file")
                    
                    with col2:
                        st.write("**Content Checks:**")
                        
                        if file_exists:
                            # Read and analyze file content
                            with open(strategy.file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            has_istrategy = 'IStrategy' in content
                            has_populate_indicators = 'populate_indicators' in content
                            has_populate_entry = 'populate_entry_trend' in content
                            has_populate_exit = 'populate_exit_trend' in content
                            
                            st.write(f"✅ IStrategy inheritance" if has_istrategy else "❌ Missing IStrategy")
                            st.write(f"✅ populate_indicators" if has_populate_indicators else "❌ Missing populate_indicators")
                            st.write(f"✅ populate_entry_trend" if has_populate_entry else "❌ Missing populate_entry_trend")
                            st.write(f"✅ populate_exit_trend" if has_populate_exit else "❌ Missing populate_exit_trend")
                            
                            # Overall validation
                            is_valid = all([
                                file_exists, is_python_file, has_istrategy,
                                has_populate_indicators, has_populate_entry, has_populate_exit
                            ])
                        else:
                            is_valid = False
                    
                    validation_results[strategy.name] = is_valid
                    
                    # Validation summary
                    if is_valid:
                        st.success("✅ Strategy validation passed")
                    else:
                        st.error("❌ Strategy validation failed")
                
                except Exception as e:
                    st.error(f"❌ Validation error: {str(e)}")
                    validation_results[strategy.name] = False
        
        return validation_results