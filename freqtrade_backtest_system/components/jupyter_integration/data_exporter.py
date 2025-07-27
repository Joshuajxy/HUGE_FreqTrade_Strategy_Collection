"""
Data export functionality for Jupyter analysis
"""
import pickle
import json
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import streamlit as st

from utils.data_models import BacktestResult, ComparisonResult, TradeRecord
from utils.error_handling import ErrorHandler, error_handler

class DataExporter:
    """Data export functionality for Jupyter analysis"""
    
    def __init__(self, export_dir: str = "jupyter_exports"):
        """
        Initialize data exporter
        
        Args:
            export_dir: directory for exported data
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.export_dir / "pickle").mkdir(exist_ok=True)
        (self.export_dir / "csv").mkdir(exist_ok=True)
        (self.export_dir / "json").mkdir(exist_ok=True)
        (self.export_dir / "excel").mkdir(exist_ok=True)
        
        ErrorHandler.log_info(f"Data exporter initialized: {self.export_dir}")
    
    @error_handler(Exception, show_error=True)
    def export_backtest_results(self, 
                               results: List[BacktestResult], 
                               format_type: str = "pickle",
                               filename: Optional[str] = None) -> Optional[Path]:
        """
        Export backtest results in specified format
        
        Args:
            results: list of backtest results
            format_type: export format (pickle, csv, json, excel)
            filename: custom filename (optional)
            
        Returns:
            path to exported file
        """
        if not results:
            st.warning("No results to export")
            return None
        
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"backtest_results_{timestamp}"
            
            # Export based on format
            if format_type == "pickle":
                return self._export_pickle(results, filename, "backtest_results")
            elif format_type == "csv":
                return self._export_csv(results, filename)
            elif format_type == "json":
                return self._export_json(results, filename)
            elif format_type == "excel":
                return self._export_excel(results, filename)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to export backtest results: {str(e)}")
            st.error(f"Export failed: {str(e)}")
            return None
    
    @error_handler(Exception, show_error=True)
    def export_comparison_result(self, 
                                comparison: ComparisonResult,
                                format_type: str = "pickle",
                                filename: Optional[str] = None) -> Optional[Path]:
        """
        Export comparison result
        
        Args:
            comparison: comparison result
            format_type: export format
            filename: custom filename (optional)
            
        Returns:
            path to exported file
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"comparison_result_{timestamp}"
            
            if format_type == "pickle":
                return self._export_pickle(comparison, filename, "comparison")
            elif format_type == "json":
                return self._export_comparison_json(comparison, filename)
            else:
                raise ValueError(f"Unsupported format for comparison: {format_type}")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to export comparison result: {str(e)}")
            st.error(f"Export failed: {str(e)}")
            return None
    
    @error_handler(Exception, show_error=True)
    def export_trades(self, 
                     trades: List[TradeRecord],
                     format_type: str = "csv",
                     filename: Optional[str] = None) -> Optional[Path]:
        """
        Export trade records
        
        Args:
            trades: list of trade records
            format_type: export format
            filename: custom filename (optional)
            
        Returns:
            path to exported file
        """
        if not trades:
            st.warning("No trades to export")
            return None
        
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"trades_{timestamp}"
            
            if format_type == "csv":
                return self._export_trades_csv(trades, filename)
            elif format_type == "json":
                return self._export_trades_json(trades, filename)
            elif format_type == "pickle":
                return self._export_pickle(trades, filename, "trades")
            else:
                raise ValueError(f"Unsupported format for trades: {format_type}")
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to export trades: {str(e)}")
            st.error(f"Export failed: {str(e)}")
            return None
    
    def _export_pickle(self, data: Any, filename: str, data_type: str) -> Path:
        """Export data as pickle file"""
        file_path = self.export_dir / "pickle" / f"{filename}.pkl"
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        
        # Create metadata file
        metadata = {
            "filename": filename,
            "data_type": data_type,
            "export_time": datetime.now().isoformat(),
            "format": "pickle",
            "size_bytes": file_path.stat().st_size
        }
        
        metadata_path = file_path.with_suffix('.pkl.meta')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        ErrorHandler.log_info(f"Exported pickle file: {file_path}")
        return file_path
    
    def _export_csv(self, results: List[BacktestResult], filename: str) -> Path:
        """Export backtest results as CSV"""
        file_path = self.export_dir / "csv" / f"{filename}.csv"
        
        # Convert results to DataFrame
        data = []
        for result in results:
            metrics = result.metrics
            data.append({
                'strategy_name': result.strategy_name,
                'timestamp': result.timestamp.isoformat(),
                'total_return_pct': metrics.total_return_pct,
                'win_rate': metrics.win_rate,
                'max_drawdown_pct': metrics.max_drawdown_pct,
                'sharpe_ratio': metrics.sharpe_ratio,
                'sortino_ratio': metrics.sortino_ratio,
                'calmar_ratio': metrics.calmar_ratio,
                'total_trades': metrics.total_trades,
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'avg_profit': metrics.avg_profit,
                'avg_profit_pct': metrics.avg_profit_pct,
                'execution_time': result.execution_time,
                'status': result.status.value,
                'error_message': result.error_message
            })
        
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding='utf-8')
        
        ErrorHandler.log_info(f"Exported CSV file: {file_path}")
        return file_path
    
    def _export_json(self, results: List[BacktestResult], filename: str) -> Path:
        """Export backtest results as JSON"""
        file_path = self.export_dir / "json" / f"{filename}.json"
        
        # Convert results to JSON-serializable format
        data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "format": "json",
                "count": len(results)
            },
            "results": [result.to_dict() for result in results]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        ErrorHandler.log_info(f"Exported JSON file: {file_path}")
        return file_path
    
    def _export_excel(self, results: List[BacktestResult], filename: str) -> Path:
        """Export backtest results as Excel file"""
        file_path = self.export_dir / "excel" / f"{filename}.xlsx"
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for result in results:
                metrics = result.metrics
                summary_data.append({
                    'Strategy': result.strategy_name,
                    'Total Return (%)': metrics.total_return_pct,
                    'Win Rate (%)': metrics.win_rate,
                    'Max Drawdown (%)': metrics.max_drawdown_pct,
                    'Sharpe Ratio': metrics.sharpe_ratio,
                    'Total Trades': metrics.total_trades,
                    'Execution Time (s)': result.execution_time,
                    'Status': result.status.value
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed metrics sheet
            detailed_data = []
            for result in results:
                metrics = result.metrics
                detailed_data.append({
                    'Strategy': result.strategy_name,
                    'Timestamp': result.timestamp,
                    'Total Return': metrics.total_return,
                    'Total Return (%)': metrics.total_return_pct,
                    'Win Rate (%)': metrics.win_rate,
                    'Max Drawdown': metrics.max_drawdown,
                    'Max Drawdown (%)': metrics.max_drawdown_pct,
                    'Sharpe Ratio': metrics.sharpe_ratio,
                    'Sortino Ratio': metrics.sortino_ratio,
                    'Calmar Ratio': metrics.calmar_ratio,
                    'Total Trades': metrics.total_trades,
                    'Winning Trades': metrics.winning_trades,
                    'Losing Trades': metrics.losing_trades,
                    'Average Profit': metrics.avg_profit,
                    'Average Profit (%)': metrics.avg_profit_pct,
                    'Average Duration': metrics.avg_duration
                })
            
            detailed_df = pd.DataFrame(detailed_data)
            detailed_df.to_excel(writer, sheet_name='Detailed Metrics', index=False)
            
            # Trades sheet (if available)
            all_trades = []
            for result in results:
                for trade in result.trades:
                    all_trades.append({
                        'Strategy': result.strategy_name,
                        'Pair': trade.pair,
                        'Side': trade.side,
                        'Timestamp': trade.timestamp,
                        'Price': trade.price,
                        'Amount': trade.amount,
                        'Profit': trade.profit,
                        'Profit (%)': trade.profit_pct,
                        'Reason': trade.reason
                    })
            
            if all_trades:
                trades_df = pd.DataFrame(all_trades)
                trades_df.to_excel(writer, sheet_name='All Trades', index=False)
        
        ErrorHandler.log_info(f"Exported Excel file: {file_path}")
        return file_path    
 
   def _export_comparison_json(self, comparison: ComparisonResult, filename: str) -> Path:
        """Export comparison result as JSON"""
        file_path = self.export_dir / "json" / f"{filename}.json"
        
        data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "format": "json",
                "type": "comparison_result"
            },
            "comparison": comparison.to_dict()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        ErrorHandler.log_info(f"Exported comparison JSON: {file_path}")
        return file_path
    
    def _export_trades_csv(self, trades: List[TradeRecord], filename: str) -> Path:
        """Export trades as CSV"""
        file_path = self.export_dir / "csv" / f"{filename}.csv"
        
        data = []
        for trade in trades:
            data.append({
                'pair': trade.pair,
                'side': trade.side,
                'timestamp': trade.timestamp.isoformat(),
                'price': trade.price,
                'amount': trade.amount,
                'profit': trade.profit,
                'profit_pct': trade.profit_pct,
                'reason': trade.reason
            })
        
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding='utf-8')
        
        ErrorHandler.log_info(f"Exported trades CSV: {file_path}")
        return file_path
    
    def _export_trades_json(self, trades: List[TradeRecord], filename: str) -> Path:
        """Export trades as JSON"""
        file_path = self.export_dir / "json" / f"{filename}.json"
        
        data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "format": "json",
                "type": "trades",
                "count": len(trades)
            },
            "trades": [trade.to_dict() for trade in trades]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        ErrorHandler.log_info(f"Exported trades JSON: {file_path}")
        return file_path
    
    @error_handler(Exception, show_error=True)
    def validate_data_integrity(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate data integrity of exported file
        
        Args:
            file_path: path to exported file
            
        Returns:
            validation results
        """
        try:
            validation_result = {
                "file_exists": file_path.exists(),
                "file_size": 0,
                "format": file_path.suffix,
                "readable": False,
                "data_count": 0,
                "validation_time": datetime.now().isoformat(),
                "errors": []
            }
            
            if not file_path.exists():
                validation_result["errors"].append("File does not exist")
                return validation_result
            
            validation_result["file_size"] = file_path.stat().st_size
            
            # Validate based on format
            if file_path.suffix == '.pkl':
                validation_result.update(self._validate_pickle(file_path))
            elif file_path.suffix == '.csv':
                validation_result.update(self._validate_csv(file_path))
            elif file_path.suffix == '.json':
                validation_result.update(self._validate_json(file_path))
            elif file_path.suffix == '.xlsx':
                validation_result.update(self._validate_excel(file_path))
            
            return validation_result
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to validate data integrity: {str(e)}")
            return {
                "file_exists": False,
                "readable": False,
                "errors": [str(e)]
            }
    
    def _validate_pickle(self, file_path: Path) -> Dict[str, Any]:
        """Validate pickle file"""
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            data_count = len(data) if isinstance(data, (list, dict)) else 1
            
            return {
                "readable": True,
                "data_count": data_count,
                "data_type": type(data).__name__
            }
        
        except Exception as e:
            return {
                "readable": False,
                "errors": [f"Pickle validation failed: {str(e)}"]
            }
    
    def _validate_csv(self, file_path: Path) -> Dict[str, Any]:
        """Validate CSV file"""
        try:
            df = pd.read_csv(file_path)
            
            return {
                "readable": True,
                "data_count": len(df),
                "columns": list(df.columns),
                "column_count": len(df.columns)
            }
        
        except Exception as e:
            return {
                "readable": False,
                "errors": [f"CSV validation failed: {str(e)}"]
            }
    
    def _validate_json(self, file_path: Path) -> Dict[str, Any]:
        """Validate JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data_count = 0
            if isinstance(data, dict):
                if "results" in data:
                    data_count = len(data["results"])
                elif "trades" in data:
                    data_count = len(data["trades"])
                else:
                    data_count = 1
            elif isinstance(data, list):
                data_count = len(data)
            
            return {
                "readable": True,
                "data_count": data_count,
                "data_type": type(data).__name__
            }
        
        except Exception as e:
            return {
                "readable": False,
                "errors": [f"JSON validation failed: {str(e)}"]
            }
    
    def _validate_excel(self, file_path: Path) -> Dict[str, Any]:
        """Validate Excel file"""
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names
            
            total_rows = 0
            for sheet in sheets:
                df = pd.read_excel(file_path, sheet_name=sheet)
                total_rows += len(df)
            
            return {
                "readable": True,
                "data_count": total_rows,
                "sheets": sheets,
                "sheet_count": len(sheets)
            }
        
        except Exception as e:
            return {
                "readable": False,
                "errors": [f"Excel validation failed: {str(e)}"]
            }
    
    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get export history"""
        history = []
        
        try:
            # Scan all export directories
            for format_dir in ["pickle", "csv", "json", "excel"]:
                format_path = self.export_dir / format_dir
                if not format_path.exists():
                    continue
                
                for file_path in format_path.iterdir():
                    if file_path.is_file() and not file_path.name.endswith('.meta'):
                        stat = file_path.stat()
                        
                        # Try to read metadata if available
                        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                        metadata = {}
                        if metadata_path.exists():
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                            except:
                                pass
                        
                        history.append({
                            'filename': file_path.name,
                            'format': format_dir,
                            'size_mb': stat.st_size / (1024 * 1024),
                            'created': datetime.fromtimestamp(stat.st_ctime),
                            'modified': datetime.fromtimestamp(stat.st_mtime),
                            'path': str(file_path),
                            'metadata': metadata
                        })
            
            # Sort by creation time (newest first)
            history.sort(key=lambda x: x['created'], reverse=True)
            return history
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to get export history: {str(e)}")
            return []
    
    def cleanup_old_exports(self, days_old: int = 30) -> int:
        """
        Clean up old export files
        
        Args:
            days_old: delete files older than this many days
            
        Returns:
            number of files deleted
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            for format_dir in ["pickle", "csv", "json", "excel"]:
                format_path = self.export_dir / format_dir
                if not format_path.exists():
                    continue
                
                for file_path in format_path.iterdir():
                    if file_path.is_file():
                        if file_path.stat().st_ctime < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                            
                            # Also delete metadata file if exists
                            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                            if metadata_path.exists():
                                metadata_path.unlink()
            
            ErrorHandler.log_info(f"Cleaned up {deleted_count} old export files")
            return deleted_count
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to cleanup old exports: {str(e)}")
            return 0
    
    def render_export_interface(self, results: List[BacktestResult] = None):
        """Render data export interface"""
        st.subheader("📤 Data Export")
        
        if not results:
            st.info("No results available for export")
            return
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                ["pickle", "csv", "json", "excel"],
                help="Choose export format for Jupyter analysis"
            )
            
            custom_filename = st.text_input(
                "Custom Filename (optional)",
                placeholder="Leave empty for auto-generated name"
            )
        
        with col2:
            st.write("**Export Options:**")
            
            include_trades = st.checkbox(
                "Include Trade Details",
                value=True,
                help="Include individual trade records"
            )
            
            validate_export = st.checkbox(
                "Validate After Export",
                value=True,
                help="Validate data integrity after export"
            )
        
        # Export button
        if st.button("📤 Export Data", type="primary"):
            with st.spinner("Exporting data..."):
                exported_file = self.export_backtest_results(
                    results, 
                    export_format, 
                    custom_filename
                )
                
                if exported_file:
                    st.success(f"Data exported successfully: {exported_file.name}")
                    
                    # Validate if requested
                    if validate_export:
                        validation_result = self.validate_data_integrity(exported_file)
                        
                        if validation_result.get("readable", False):
                            st.success("✅ Data validation passed")
                            st.info(f"Exported {validation_result.get('data_count', 0)} records")
                        else:
                            st.error("❌ Data validation failed")
                            for error in validation_result.get("errors", []):
                                st.error(error)
                    
                    # Provide download link
                    with open(exported_file, 'rb') as f:
                        st.download_button(
                            "📥 Download Exported File",
                            data=f.read(),
                            file_name=exported_file.name,
                            mime="application/octet-stream"
                        )
        
        # Export history
        st.subheader("📜 Export History")
        history = self.get_export_history()
        
        if history:
            history_data = []
            for item in history:
                history_data.append({
                    'Filename': item['filename'],
                    'Format': item['format'].upper(),
                    'Size (MB)': f"{item['size_mb']:.2f}",
                    'Created': item['created'].strftime('%Y-%m-%d %H:%M:%S'),
                    'Path': item['path']
                })
            
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
            
            # Cleanup option
            if st.button("🧹 Clean Old Exports (30+ days)"):
                deleted_count = self.cleanup_old_exports(30)
                if deleted_count > 0:
                    st.success(f"Deleted {deleted_count} old export files")
                    st.rerun()
                else:
                    st.info("No old files to delete")
        else:
            st.info("No export history available")