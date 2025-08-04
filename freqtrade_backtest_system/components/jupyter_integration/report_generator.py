"""
Automated report generation system (simplified version)
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import nbformat
    from nbconvert import HTMLExporter, PDFExporter, MarkdownExporter
    from nbconvert.preprocessors import ExecutePreprocessor
    HAS_NBCONVERT = True
except ImportError:
    HAS_NBCONVERT = False

from utils.data_models import BacktestResult
from utils.error_handling import ErrorHandler, error_handler, ExecutionError
from .template_manager import JupyterTemplateManager

class ReportGenerator:
    """Automated report generation system"""
    
    def __init__(self, template_manager: JupyterTemplateManager = None):
        """
        Initialize report generator
        Args:
            template_manager: template manager instance
        """
        self.template_manager = template_manager or JupyterTemplateManager()
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Supported output formats
        if HAS_NBCONVERT:
            self.exporters = {
                'html': HTMLExporter(),
                'pdf': PDFExporter(),
                'markdown': MarkdownExporter()
            }
        else:
            self.exporters = {}
    
    @error_handler(Exception, show_error=True)
    def generate_strategy_report(self, 
                               result: BacktestResult,
                               output_format: str = 'html',
                               include_trades: bool = True) -> Optional[Path]:
        """
        Generate strategy analysis report
        Args:
            result: backtest result
            output_format: output format (html, pdf, markdown, json)
            include_trades: whether to include trade details
        Returns:
            path to generated report
        """
        ErrorHandler.log_info(f"Generating strategy report for {result.strategy_name}")
        
        # Prepare data for template
        data = {
            'strategy_name': result.strategy_name,
            'results_data': {
                'metrics': {
                    'total_return_pct': result.metrics.total_return_pct,
                    'win_rate': result.metrics.win_rate,
                    'max_drawdown_pct': result.metrics.max_drawdown_pct,
                    'sharpe_ratio': result.metrics.sharpe_ratio,
                    'sortino_ratio': result.metrics.sortino_ratio,
                    'total_trades': result.metrics.total_trades,
                    'winning_trades': result.metrics.winning_trades,
                    'losing_trades': result.metrics.losing_trades,
                    'avg_profit': result.metrics.avg_profit
                },
                'timestamp': result.timestamp.isoformat(),
                'execution_time': result.execution_time
            },
            'config_data': result.config.to_dict() if result.config else {},
            'trades_data': [trade.to_dict() for trade in result.trades] if include_trades else []
        }
        
        # Generate report based on format
        if output_format == 'json':
            return self._generate_json_report(data, result.strategy_name)
        elif HAS_NBCONVERT and output_format in self.exporters:
            return self._generate_notebook_report(data, result.strategy_name, output_format)
        else:
            return self._generate_simple_report(data, result.strategy_name, output_format)
    
    def _generate_json_report(self, data: Dict[str, Any], strategy_name: str) -> Path:
        """Generate JSON report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.reports_dir / f"{strategy_name}_report_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        ErrorHandler.log_info(f"JSON report generated: {report_path}")
        return report_path
    
    def _generate_simple_report(self, data: Dict[str, Any], strategy_name: str, output_format: str) -> Path:
        """Generate simple text-based report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'html':
            report_path = self.reports_dir / f"{strategy_name}_report_{timestamp}.html"
            content = self._create_html_report(data)
        else:
            report_path = self.reports_dir / f"{strategy_name}_report_{timestamp}.md"
            content = self._create_markdown_report(data)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        ErrorHandler.log_info(f"Simple report generated: {report_path}")
        return report_path
    
    def _create_html_report(self, data: Dict[str, Any]) -> str:
        """Create HTML report content"""
        strategy_name = data['strategy_name']
        metrics = data['results_data']['metrics']
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Strategy Report - {strategy_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f8ff; padding: 20px; border-radius: 8px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #1f77b4; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 Strategy Analysis Report</h1>
        <h2>{strategy_name}</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h3>📊 Performance Metrics</h3>
    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value">{metrics['total_return_pct']:.2f}%</div>
            <div class="metric-label">Total Return</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{metrics['win_rate']:.2f}%</div>
            <div class="metric-label">Win Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{metrics['max_drawdown_pct']:.2f}%</div>
            <div class="metric-label">Max Drawdown</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{metrics['sharpe_ratio']:.3f}</div>
            <div class="metric-label">Sharpe Ratio</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{metrics['total_trades']}</div>
            <div class="metric-label">Total Trades</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{metrics['avg_profit']:.2f}</div>
            <div class="metric-label">Avg Profit</div>
        </div>
    </div>
    
    <h3>📋 Configuration</h3>
    <pre>{json.dumps(data['config_data'], indent=2)}</pre>
    
    <h3>📊 Raw Data</h3>
    <details>
        <summary>Click to view raw data</summary>
        <pre>{json.dumps(data, indent=2)}</pre>
    </details>
</body>
</html>
"""
        return html_content
    
    def _create_markdown_report(self, data: Dict[str, Any]) -> str:
        """Create Markdown report content"""
        strategy_name = data['strategy_name']
        metrics = data['results_data']['metrics']
        
        markdown_content = f"""# 📈 Strategy Analysis Report

## {strategy_name}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Total Return | {metrics['total_return_pct']:.2f}% |
| Win Rate | {metrics['win_rate']:.2f}% |
| Max Drawdown | {metrics['max_drawdown_pct']:.2f}% |
| Sharpe Ratio | {metrics['sharpe_ratio']:.3f} |
| Total Trades | {metrics['total_trades']} |
| Average Profit | {metrics['avg_profit']:.2f} |

## 📋 Configuration

```json
{json.dumps(data['config_data'], indent=2)}
```

## 📊 Summary

This report was generated for strategy **{strategy_name}** with the following key findings:

- **Performance:** {'Positive' if metrics['total_return_pct'] > 0 else 'Negative'} return of {metrics['total_return_pct']:.2f}%
- **Risk:** Maximum drawdown of {metrics['max_drawdown_pct']:.2f}%
- **Consistency:** Win rate of {metrics['win_rate']:.2f}% over {metrics['total_trades']} trades
- **Risk-Adjusted Return:** Sharpe ratio of {metrics['sharpe_ratio']:.3f}

## 📊 Raw Data

<details>
<summary>Click to view raw data</summary>

```json
{json.dumps(data, indent=2)}
```

</details>
"""
        return markdown_content
    
    def _generate_notebook_report(self, data: Dict[str, Any], strategy_name: str, output_format: str) -> Optional[Path]:
        """Generate notebook-based report (when nbconvert is available)"""
        if not HAS_NBCONVERT:
            ErrorHandler.log_warning("nbconvert not available, falling back to simple report")
            return self._generate_simple_report(data, strategy_name, output_format)
        
        try:
            # Create notebook from template
            notebook_path = self.template_manager.create_analysis_notebook(
                'strategy_analysis',
                data,
                f"{strategy_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if not notebook_path:
                raise ExecutionError("Failed to create analysis notebook")
            
            # Execute notebook
            executed_notebook = self._execute_notebook(notebook_path)
            
            # Convert to desired format
            report_path = self._convert_notebook(executed_notebook, output_format, strategy_name)
            
            ErrorHandler.log_info(f"Notebook report generated: {report_path}")
            return report_path
            
        except Exception as e:
            ErrorHandler.log_error(f"Error generating notebook report: {str(e)}")
            # Fallback to simple report
            return self._generate_simple_report(data, strategy_name, output_format)
    
    def _execute_notebook(self, notebook_path: Path) -> Path:
        """Execute notebook and return path to executed version"""
        if not HAS_NBCONVERT:
            return notebook_path
            
        try:
            # Read notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            # Execute notebook
            ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
            ep.preprocess(nb, {'metadata': {'path': str(notebook_path.parent)}})
            
            # Save executed notebook
            executed_path = notebook_path.parent / f"executed_{notebook_path.name}"
            with open(executed_path, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)
            
            return executed_path
            
        except Exception as e:
            ErrorHandler.log_error(f"Error executing notebook: {str(e)}")
            # Return original notebook if execution fails
            return notebook_path
    
    def _convert_notebook(self, notebook_path: Path, output_format: str, base_name: str) -> Path:
        """Convert notebook to specified format"""
        if output_format not in self.exporters:
            raise ExecutionError(f"Unsupported output format: {output_format}")
        
        try:
            # Read notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            # Convert notebook
            exporter = self.exporters[output_format]
            (body, resources) = exporter.from_notebook_node(nb)
            
            # Determine output extension
            extensions = {
                'html': '.html',
                'pdf': '.pdf',
                'markdown': '.md'
            }
            
            # Save converted report
            output_path = self.reports_dir / f"{base_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extensions[output_format]}"
            
            if output_format == 'pdf':
                # For PDF, write binary
                with open(output_path, 'wb') as f:
                    f.write(body)
            else:
                # For HTML and Markdown, write text
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(body)
            
            return output_path
            
        except Exception as e:
            ErrorHandler.log_error(f"Error converting notebook: {str(e)}")
            raise ExecutionError(f"Failed to convert notebook to {output_format}: {str(e)}")
    
    def get_available_formats(self) -> List[str]:
        """Get list of available output formats"""
        formats = ['json', 'html', 'markdown']
        if HAS_NBCONVERT:
            formats.extend(list(self.exporters.keys()))
        return list(set(formats))  # Remove duplicates
    
    def get_generated_reports(self) -> List[Dict[str, Any]]:
        """Get list of generated reports"""
        reports = []
        for report_file in self.reports_dir.glob("*"):
            if report_file.is_file():
                reports.append({
                    'name': report_file.name,
                    'path': str(report_file),
                    'size': report_file.stat().st_size,
                    'created': datetime.fromtimestamp(report_file.stat().st_ctime),
                    'format': report_file.suffix[1:] if report_file.suffix else 'unknown'
                })
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x['created'], reverse=True)
        return reports
    
    def delete_report(self, report_name: str) -> bool:
        """Delete a generated report"""
        report_path = self.reports_dir / report_name
        try:
            if report_path.exists():
                report_path.unlink()
                ErrorHandler.log_info(f"Deleted report: {report_name}")
                return True
            else:
                ErrorHandler.log_warning(f"Report not found: {report_name}")
                return False
        except Exception as e:
            ErrorHandler.log_error(f"Error deleting report: {str(e)}")
            return False