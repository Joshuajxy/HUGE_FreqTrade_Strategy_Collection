"""
Jupyter Notebook template management system
"""
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st

from utils.data_models import NotebookTemplate, BacktestResult
from utils.error_handling import ErrorHandler, error_handler

class NotebookTemplateManager:
    """Jupyter Notebook template management system"""
    
    def __init__(self, templates_dir: str = "notebook_templates"):
        """
        Initialize template manager
        
        Args:
            templates_dir: directory for storing notebook templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.templates_dir / "predefined").mkdir(exist_ok=True)
        (self.templates_dir / "custom").mkdir(exist_ok=True)
        (self.templates_dir / "versions").mkdir(exist_ok=True)
        
        # Initialize predefined templates
        self._create_predefined_templates()
        
        ErrorHandler.log_info(f"Notebook template manager initialized: {self.templates_dir}")
    
    def _create_predefined_templates(self):
        """Create predefined analysis templates"""
        predefined_templates = [
            {
                "name": "Single Strategy Analysis",
                "description": "Comprehensive analysis of a single strategy",
                "file_name": "single_strategy_analysis.ipynb",
                "parameters": ["strategy_name", "backtest_result", "config"],
                "template_type": "single_strategy"
            },
            {
                "name": "Strategy Comparison",
                "description": "Compare multiple strategies side by side",
                "file_name": "strategy_comparison.ipynb", 
                "parameters": ["strategy_results", "comparison_metrics"],
                "template_type": "comparison"
            },
            {
                "name": "Risk Analysis",
                "description": "Detailed risk analysis and drawdown study",
                "file_name": "risk_analysis.ipynb",
                "parameters": ["backtest_results", "risk_metrics"],
                "template_type": "risk_analysis"
            },
            {
                "name": "Performance Report",
                "description": "Generate professional performance report",
                "file_name": "performance_report.ipynb",
                "parameters": ["results", "report_config"],
                "template_type": "report"
            }
        ]
        
        for template_info in predefined_templates:
            template_path = self.templates_dir / "predefined" / template_info["file_name"]
            if not template_path.exists():
                self._create_template_file(template_path, template_info)    

    def _create_template_file(self, template_path: Path, template_info: Dict[str, Any]):
        """Create a notebook template file"""
        try:
            if template_info["template_type"] == "single_strategy":
                content = self._create_single_strategy_template()
            elif template_info["template_type"] == "comparison":
                content = self._create_comparison_template()
            elif template_info["template_type"] == "risk_analysis":
                content = self._create_risk_analysis_template()
            elif template_info["template_type"] == "report":
                content = self._create_report_template()
            else:
                content = self._create_basic_template()
            
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Created template: {template_path}")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create template {template_path}: {str(e)}")
    
    def _create_single_strategy_template(self) -> Dict[str, Any]:
        """Create single strategy analysis template"""
        return {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "# Single Strategy Analysis Report\n",
                        "\n",
                        "**Strategy:** {{strategy_name}}\n",
                        "**Generated:** {{timestamp}}\n",
                        "\n",
                        "This notebook provides comprehensive analysis of a single trading strategy."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "import plotly.graph_objects as go\n",
                        "import plotly.express as px\n",
                        "from datetime import datetime\n",
                        "import pickle\n",
                        "\n",
                        "# Load backtest result\n",
                        "with open('{{result_file}}', 'rb') as f:\n",
                        "    result = pickle.load(f)\n",
                        "\n",
                        "print(f\"Strategy: {result.strategy_name}\")\n",
                        "print(f\"Total Return: {result.metrics.total_return_pct:.2f}%\")\n",
                        "print(f\"Win Rate: {result.metrics.win_rate:.2f}%\")\n",
                        "print(f\"Max Drawdown: {result.metrics.max_drawdown_pct:.2f}%\")"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Performance Metrics"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "# Create performance metrics table\n",
                        "metrics_data = {\n",
                        "    'Metric': [\n",
                        "        'Total Return (%)',\n",
                        "        'Win Rate (%)',\n",
                        "        'Max Drawdown (%)',\n",
                        "        'Sharpe Ratio',\n",
                        "        'Sortino Ratio',\n",
                        "        'Total Trades',\n",
                        "        'Winning Trades',\n",
                        "        'Losing Trades'\n",
                        "    ],\n",
                        "    'Value': [\n",
                        "        f\"{result.metrics.total_return_pct:.2f}%\",\n",
                        "        f\"{result.metrics.win_rate:.2f}%\",\n",
                        "        f\"{result.metrics.max_drawdown_pct:.2f}%\",\n",
                        "        f\"{result.metrics.sharpe_ratio:.3f}\",\n",
                        "        f\"{result.metrics.sortino_ratio:.3f}\",\n",
                        "        result.metrics.total_trades,\n",
                        "        result.metrics.winning_trades,\n",
                        "        result.metrics.losing_trades\n",
                        "    ]\n",
                        "}\n",
                        "\n",
                        "metrics_df = pd.DataFrame(metrics_data)\n",
                        "print(metrics_df.to_string(index=False))"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
    
    def _create_comparison_template(self) -> Dict[str, Any]:
        """Create strategy comparison template"""
        return {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "# Strategy Comparison Analysis\n",
                        "\n",
                        "**Generated:** {{timestamp}}\n",
                        "**Strategies:** {{strategy_count}} strategies\n",
                        "\n",
                        "This notebook compares multiple trading strategies."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "import plotly.graph_objects as go\n",
                        "import plotly.express as px\n",
                        "import pickle\n",
                        "\n",
                        "# Load comparison results\n",
                        "with open('{{comparison_file}}', 'rb') as f:\n",
                        "    comparison = pickle.load(f)\n",
                        "\n",
                        "print(f\"Comparing {len(comparison.strategies)} strategies\")\n",
                        "print(f\"Best strategy: {comparison.best_strategy}\")"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
    
    def _create_risk_analysis_template(self) -> Dict[str, Any]:
        """Create risk analysis template"""
        return {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "# Risk Analysis Report\n",
                        "\n",
                        "**Generated:** {{timestamp}}\n",
                        "\n",
                        "Detailed risk analysis and drawdown study."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "import plotly.graph_objects as go\n",
                        "from scipy import stats\n",
                        "import pickle\n",
                        "\n",
                        "# Load results for risk analysis\n",
                        "with open('{{results_file}}', 'rb') as f:\n",
                        "    results = pickle.load(f)\n",
                        "\n",
                        "print(f\"Analyzing risk for {len(results)} strategies\")"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
    
    def _create_report_template(self) -> Dict[str, Any]:
        """Create performance report template"""
        return {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "# Professional Performance Report\n",
                        "\n",
                        "**Generated:** {{timestamp}}\n",
                        "**Report Type:** {{report_type}}\n",
                        "\n",
                        "Professional performance analysis report."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "import plotly.graph_objects as go\n",
                        "import plotly.express as px\n",
                        "from plotly.subplots import make_subplots\n",
                        "import pickle\n",
                        "\n",
                        "# Load data for report generation\n",
                        "with open('{{data_file}}', 'rb') as f:\n",
                        "    data = pickle.load(f)\n",
                        "\n",
                        "print(\"Generating professional performance report...\")"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
    
    def _create_basic_template(self) -> Dict[str, Any]:
        """Create basic template"""
        return {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "# Custom Analysis\n",
                        "\n",
                        "**Generated:** {{timestamp}}\n",
                        "\n",
                        "Custom analysis notebook."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "import plotly.graph_objects as go\n",
                        "\n",
                        "# Your analysis code here\n",
                        "print(\"Starting custom analysis...\")"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }  
  
    @error_handler(Exception, show_error=True)
    def get_available_templates(self) -> List[NotebookTemplate]:
        """Get list of available templates"""
        templates = []
        
        try:
            # Get predefined templates
            predefined_dir = self.templates_dir / "predefined"
            for template_file in predefined_dir.glob("*.ipynb"):
                template_info = self._extract_template_info(template_file, "predefined")
                if template_info:
                    templates.append(template_info)
            
            # Get custom templates
            custom_dir = self.templates_dir / "custom"
            for template_file in custom_dir.glob("*.ipynb"):
                template_info = self._extract_template_info(template_file, "custom")
                if template_info:
                    templates.append(template_info)
            
            return templates
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get available templates: {str(e)}")
            return []
    
    def _extract_template_info(self, template_file: Path, template_type: str) -> Optional[NotebookTemplate]:
        """Extract template information from file"""
        try:
            # Read notebook file
            with open(template_file, 'r', encoding='utf-8') as f:
                notebook_content = json.load(f)
            
            # Extract metadata
            metadata = notebook_content.get('metadata', {})
            
            # Extract description from first markdown cell
            description = "No description available"
            for cell in notebook_content.get('cells', []):
                if cell.get('cell_type') == 'markdown':
                    source = cell.get('source', [])
                    if isinstance(source, list) and len(source) > 0:
                        description = ''.join(source)[:200] + "..."
                    break
            
            # Extract parameters (placeholder implementation)
            parameters = self._extract_parameters_from_notebook(notebook_content)
            
            return NotebookTemplate(
                name=template_file.stem.replace('_', ' ').title(),
                description=description,
                file_path=template_file,
                parameters=parameters,
                template_type=template_type
            )
        
        except Exception as e:
            ErrorHandler.log_warning(f"Failed to extract template info from {template_file}: {str(e)}")
            return None
    
    def _extract_parameters_from_notebook(self, notebook_content: Dict[str, Any]) -> List[str]:
        """Extract parameters from notebook content"""
        parameters = []
        
        try:
            for cell in notebook_content.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', [])
                    source_text = ''.join(source) if isinstance(source, list) else str(source)
                    
                    # Look for template variables like {{variable_name}}
                    import re
                    matches = re.findall(r'\{\{(\w+)\}\}', source_text)
                    parameters.extend(matches)
            
            return list(set(parameters))  # Remove duplicates
        
        except Exception:
            return []
    
    @error_handler(Exception, show_error=True)
    def create_custom_template(self, 
                             name: str, 
                             description: str, 
                             notebook_content: Dict[str, Any]) -> bool:
        """Create a custom template"""
        try:
            # Validate name
            if not name or not name.strip():
                raise ValueError("Template name cannot be empty")
            
            # Create file path
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_name = safe_name.replace(' ', '_').lower() + '.ipynb'
            template_path = self.templates_dir / "custom" / file_name
            
            # Add metadata to notebook
            if 'metadata' not in notebook_content:
                notebook_content['metadata'] = {}
            
            notebook_content['metadata'].update({
                'template_name': name,
                'template_description': description,
                'created_at': datetime.now().isoformat(),
                'template_type': 'custom'
            })
            
            # Save template
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(notebook_content, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Created custom template: {name}")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create custom template: {str(e)}")
            return False
    
    @error_handler(Exception, show_error=True)
    def delete_template(self, template: NotebookTemplate) -> bool:
        """Delete a template"""
        try:
            if template.template_type == "predefined":
                raise ValueError("Cannot delete predefined templates")
            
            if template.file_path.exists():
                template.file_path.unlink()
                ErrorHandler.log_info(f"Deleted template: {template.name}")
                return True
            else:
                ErrorHandler.log_warning(f"Template file not found: {template.file_path}")
                return False
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to delete template: {str(e)}")
            return False
    
    @error_handler(Exception, show_error=True)
    def create_template_version(self, template: NotebookTemplate, version_name: str) -> bool:
        """Create a version of a template"""
        try:
            # Create version directory
            version_dir = self.templates_dir / "versions" / template.name.replace(' ', '_')
            version_dir.mkdir(exist_ok=True)
            
            # Create version file
            version_file = version_dir / f"{version_name}.ipynb"
            shutil.copy2(template.file_path, version_file)
            
            # Update metadata
            with open(version_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            if 'metadata' not in content:
                content['metadata'] = {}
            
            content['metadata'].update({
                'version_name': version_name,
                'version_created': datetime.now().isoformat(),
                'original_template': template.name
            })
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Created template version: {template.name} v{version_name}")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to create template version: {str(e)}")
            return False
    
    def get_template_versions(self, template: NotebookTemplate) -> List[str]:
        """Get available versions of a template"""
        try:
            version_dir = self.templates_dir / "versions" / template.name.replace(' ', '_')
            if not version_dir.exists():
                return []
            
            versions = []
            for version_file in version_dir.glob("*.ipynb"):
                versions.append(version_file.stem)
            
            return sorted(versions)
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get template versions: {str(e)}")
            return []
    
    def render_template_manager(self):
        """Render template management interface"""
        st.subheader("📓 Notebook Template Manager")
        
        # Get available templates
        templates = self.get_available_templates()
        
        if not templates:
            st.info("No templates available")
            return
        
        # Template management tabs
        tab1, tab2, tab3 = st.tabs(["Available Templates", "Create Custom", "Manage Versions"])
        
        with tab1:
            self._render_available_templates(templates)
        
        with tab2:
            self._render_create_custom_template()
        
        with tab3:
            self._render_version_management(templates)
    
    def _render_available_templates(self, templates: List[NotebookTemplate]):
        """Render available templates"""
        st.write("**Available Analysis Templates:**")
        
        for template in templates:
            with st.expander(f"📓 {template.name}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Type:** {template.template_type.title()}")
                    st.write(f"**Description:** {template.description}")
                    st.write(f"**Parameters:** {', '.join(template.parameters) if template.parameters else 'None'}")
                
                with col2:
                    if st.button(f"Use Template", key=f"use_{template.name}"):
                        st.session_state.selected_template = template
                        st.success(f"Selected template: {template.name}")
                    
                    if template.template_type == "custom":
                        if st.button(f"Delete", key=f"delete_{template.name}"):
                            if self.delete_template(template):
                                st.success("Template deleted")
                                st.rerun()
    
    def _render_create_custom_template(self):
        """Render create custom template interface"""
        st.write("**Create Custom Template:**")
        
        with st.form("create_template_form"):
            template_name = st.text_input("Template Name")
            template_description = st.text_area("Description")
            
            # Basic template structure
            st.write("**Template Structure:**")
            num_cells = st.number_input("Number of cells", min_value=1, max_value=20, value=3)
            
            cells = []
            for i in range(num_cells):
                st.write(f"**Cell {i+1}:**")
                cell_type = st.selectbox(f"Type", ["markdown", "code"], key=f"cell_type_{i}")
                cell_content = st.text_area(f"Content", key=f"cell_content_{i}")
                
                cells.append({
                    "cell_type": cell_type,
                    "metadata": {},
                    "source": [cell_content]
                })
            
            if st.form_submit_button("Create Template"):
                if template_name and template_description:
                    notebook_content = {
                        "cells": cells,
                        "metadata": {
                            "kernelspec": {
                                "display_name": "Python 3",
                                "language": "python",
                                "name": "python3"
                            }
                        },
                        "nbformat": 4,
                        "nbformat_minor": 4
                    }
                    
                    if self.create_custom_template(template_name, template_description, notebook_content):
                        st.success("Custom template created successfully!")
                        st.rerun()
                else:
                    st.error("Please provide template name and description")
    
    def _render_version_management(self, templates: List[NotebookTemplate]):
        """Render version management interface"""
        st.write("**Template Version Management:**")
        
        if not templates:
            st.info("No templates available for version management")
            return
        
        selected_template = st.selectbox(
            "Select Template",
            templates,
            format_func=lambda x: x.name
        )
        
        if selected_template:
            versions = self.get_template_versions(selected_template)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Current Versions for {selected_template.name}:**")
                if versions:
                    for version in versions:
                        st.write(f"- {version}")
                else:
                    st.write("No versions created yet")
            
            with col2:
                st.write("**Create New Version:**")
                version_name = st.text_input("Version Name")
                
                if st.button("Create Version"):
                    if version_name:
                        if self.create_template_version(selected_template, version_name):
                            st.success(f"Version '{version_name}' created!")
                            st.rerun()
                    else:
                        st.error("Please provide version name")