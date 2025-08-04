"""
Jupyter template management system (simplified version)
"""
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import nbformat
    from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False

from utils.data_models import BacktestResult
from utils.error_handling import ErrorHandler, error_handler, DataError

class NotebookTemplate:
    """Simple notebook template data class"""
    def __init__(self, name: str, description: str, file_path: Path, 
                 parameters: List[str] = None, template_type: str = "custom"):
        self.name = name
        self.description = description
        self.file_path = file_path
        self.parameters = parameters or []
        self.template_type = template_type

class JupyterTemplateManager:
    """Jupyter template management system"""
    
    def __init__(self, templates_dir: str = "notebook_templates"):
        """
        Initialize template manager
        Args:
            templates_dir: directory for storing templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.outputs_dir = Path("notebook_outputs")
        self.outputs_dir.mkdir(exist_ok=True)
        
        # Initialize default templates if nbformat is available
        if HAS_NBFORMAT:
            self._create_default_templates()
        else:
            self._create_simple_templates()
    
    def _create_simple_templates(self):
        """Create simple text-based templates when nbformat is not available"""
        templates = [
            {
                "name": "strategy_analysis",
                "description": "Strategy analysis template",
                "content": """# Strategy Analysis Template

## Import Libraries
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
```

## Load Data
```python
# Data will be loaded here
```

## Analysis
```python
# Add your analysis code here
```
"""
            },
            {
                "name": "performance_comparison", 
                "description": "Performance comparison template",
                "content": """# Performance Comparison Template

## Import Libraries
```python
import pandas as pd
import numpy as np
import plotly.graph_objects as go
```

## Load Data
```python
# Multiple strategy data will be loaded here
```

## Comparison Analysis
```python
# Add comparison code here
```
"""
            }
        ]
        
        for template_info in templates:
            template_path = self.templates_dir / f"{template_info['name']}.md"
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(template_info['content'])
    
    def _create_default_templates(self):
        """Create default analysis templates using nbformat"""
        templates = [
            {
                "name": "strategy_analysis",
                "description": "Comprehensive strategy analysis template",
                "template_type": "analysis",
                "parameters": ["strategy_name", "results_data", "config_data"]
            },
            {
                "name": "performance_comparison",
                "description": "Multi-strategy performance comparison template",
                "template_type": "comparison", 
                "parameters": ["strategies_data", "comparison_metrics"]
            },
            {
                "name": "risk_analysis",
                "description": "Risk analysis and drawdown analysis template",
                "template_type": "risk",
                "parameters": ["results_data", "risk_metrics"]
            }
        ]
        
        for template_info in templates:
            template_path = self.templates_dir / f"{template_info['name']}.ipynb"
            if not template_path.exists():
                self._create_template_notebook(template_info, template_path)
    
    def _create_template_notebook(self, template_info: Dict[str, Any], output_path: Path):
        """Create a template notebook"""
        if not HAS_NBFORMAT:
            ErrorHandler.log_warning("nbformat not available, cannot create notebook templates")
            return
            
        nb = new_notebook()
        
        # Add title cell
        title_cell = new_markdown_cell(f"""# {template_info['description']}
**Template Type:** {template_info['template_type']}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Parameters:** {', '.join(template_info['parameters'])}
---
""")
        nb.cells.append(title_cell)
        
        # Add imports cell
        imports_cell = new_code_cell("""# Import required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")
print("Libraries imported successfully!")""")
        nb.cells.append(imports_cell)
        
        # Add data loading cell
        data_cell = new_code_cell("""# Load data (this will be populated automatically)
# Parameters will be injected here by the template system
print("Data loading section - parameters will be injected automatically")""")
        nb.cells.append(data_cell)
        
        # Add template-specific content
        if template_info['template_type'] == 'analysis':
            self._add_strategy_analysis_cells(nb)
        elif template_info['template_type'] == 'comparison':
            self._add_comparison_analysis_cells(nb)
        elif template_info['template_type'] == 'risk':
            self._add_risk_analysis_cells(nb)
        
        # Save notebook
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)
            ErrorHandler.log_info(f"Created template notebook: {output_path}")
        except Exception as e:
            ErrorHandler.log_error(f"Error creating template notebook: {str(e)}")
    
    def _add_strategy_analysis_cells(self, nb):
        """Add strategy analysis specific cells"""
        if not HAS_NBFORMAT:
            return
            
        # Performance overview
        overview_cell = new_markdown_cell("## 📊 Performance Overview")
        nb.cells.append(overview_cell)
        
        overview_code = new_code_cell("""# Performance metrics overview
def display_performance_metrics(results_data):
    if not results_data:
        print("No results data available")
        return
    
    metrics = results_data.get('metrics', {})
    print("Performance Metrics:")
    print(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
    print(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
    print(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
    print(f"Total Trades: {metrics.get('total_trades', 0)}")

# Display metrics (will be populated with actual data)
print("Performance metrics will be displayed here")""")
        nb.cells.append(overview_code)
    
    def _add_comparison_analysis_cells(self, nb):
        """Add comparison analysis specific cells"""
        if not HAS_NBFORMAT:
            return
            
        comparison_cell = new_markdown_cell("## 🔄 Strategy Comparison Analysis")
        nb.cells.append(comparison_cell)
        
        comparison_code = new_code_cell("""# Multi-strategy comparison
def compare_strategies(strategies_data):
    if not strategies_data:
        print("No strategies data available")
        return
    
    print("Strategy Comparison:")
    for strategy_name, data in strategies_data.items():
        metrics = data.get('metrics', {})
        print(f"\\n{strategy_name}:")
        print(f"  Return: {metrics.get('total_return_pct', 0):.2f}%")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
        print(f"  Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")

# Compare strategies (will be populated with actual data)
print("Strategy comparison will be displayed here")""")
        nb.cells.append(comparison_code)
    
    def _add_risk_analysis_cells(self, nb):
        """Add risk analysis specific cells"""
        if not HAS_NBFORMAT:
            return
            
        risk_cell = new_markdown_cell("## 📉 Risk Analysis")
        nb.cells.append(risk_cell)
        
        risk_code = new_code_cell("""# Risk analysis
def analyze_risk(results_data):
    if not results_data:
        print("No results data available")
        return
    
    metrics = results_data.get('metrics', {})
    print("Risk Analysis:")
    print(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
    print(f"Volatility: {metrics.get('volatility', 0):.2f}%")

# Analyze risk (will be populated with actual data)
print("Risk analysis will be displayed here")""")
        nb.cells.append(risk_code)
    
    @error_handler(Exception, show_error=True)
    def get_available_templates(self) -> List[NotebookTemplate]:
        """Get list of available templates"""
        templates = []
        
        # Look for both .ipynb and .md files
        for template_file in self.templates_dir.glob("*"):
            if template_file.suffix in ['.ipynb', '.md']:
                try:
                    template = NotebookTemplate(
                        name=template_file.stem,
                        description=f"Template: {template_file.stem}",
                        file_path=template_file,
                        parameters=[],
                        template_type="custom"
                    )
                    templates.append(template)
                except Exception as e:
                    ErrorHandler.log_warning(f"Error reading template {template_file}: {str(e)}")
        
        return templates
    
    @error_handler(Exception, show_error=True)
    def create_analysis_notebook(self, 
                                template_name: str,
                                data: Dict[str, Any],
                                output_name: str = None) -> Optional[Path]:
        """
        Create analysis notebook from template
        Args:
            template_name: name of template to use
            data: data to inject into template
            output_name: name for output notebook
        Returns:
            path to created notebook
        """
        template_path = self.templates_dir / f"{template_name}.ipynb"
        
        # Try .md template if .ipynb doesn't exist
        if not template_path.exists():
            template_path = self.templates_dir / f"{template_name}.md"
        
        if not template_path.exists():
            raise DataError(f"Template not found: {template_name}")
        
        # Generate output filename
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"{template_name}_{timestamp}"
        
        if template_path.suffix == '.ipynb' and HAS_NBFORMAT:
            output_path = self.outputs_dir / f"{output_name}.ipynb"
            
            # Read template
            with open(template_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            # Inject data into notebook
            self._inject_data_into_notebook(nb, data)
            
            # Save output notebook
            with open(output_path, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)
        else:
            # Create simple text output
            output_path = self.outputs_dir / f"{output_name}.md"
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple data injection for markdown
            content += f"\\n\\n## Data\\n```json\\n{json.dumps(data, indent=2)}\\n```"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        ErrorHandler.log_info(f"Created analysis notebook: {output_path}")
        return output_path
    
    def _inject_data_into_notebook(self, nb, data: Dict[str, Any]):
        """Inject data into notebook cells"""
        if not HAS_NBFORMAT:
            return
            
        # Find data loading cell and inject parameters
        for cell in nb.cells:
            if cell.cell_type == 'code' and 'Parameters will be injected here' in cell.source:
                # Create data injection code
                injection_code = "# Data injected by template system\\n"
                for key, value in data.items():
                    if isinstance(value, str):
                        injection_code += f"{key} = '{value}'\\n"
                    elif isinstance(value, dict):
                        injection_code += f"{key} = {json.dumps(value, indent=2)}\\n"
                    elif isinstance(value, list):
                        injection_code += f"{key} = {json.dumps(value, indent=2)}\\n"
                    else:
                        injection_code += f"{key} = {value}\\n"
                
                injection_code += "\\nprint('Data injected successfully!')\\n"
                injection_code += "print(f'Available parameters: {list(locals().keys())}')"
                
                # Replace cell content
                cell.source = injection_code
                break
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed template information"""
        template_path = self.templates_dir / f"{template_name}.ipynb"
        
        # Try .md template if .ipynb doesn't exist
        if not template_path.exists():
            template_path = self.templates_dir / f"{template_name}.md"
        
        if not template_path.exists():
            return None
        
        try:
            return {
                'name': template_name,
                'path': str(template_path),
                'created': datetime.fromtimestamp(template_path.stat().st_ctime),
                'modified': datetime.fromtimestamp(template_path.stat().st_mtime),
                'size': template_path.stat().st_size,
                'type': template_path.suffix
            }
        except Exception as e:
            ErrorHandler.log_error(f"Error reading template info: {str(e)}")
            return None
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a template"""
        for suffix in ['.ipynb', '.md']:
            template_path = self.templates_dir / f"{template_name}{suffix}"
            if template_path.exists():
                try:
                    template_path.unlink()
                    ErrorHandler.log_info(f"Deleted template: {template_name}")
                    return True
                except Exception as e:
                    ErrorHandler.log_error(f"Error deleting template: {str(e)}")
                    return False
        
        ErrorHandler.log_warning(f"Template not found: {template_name}")
        return False