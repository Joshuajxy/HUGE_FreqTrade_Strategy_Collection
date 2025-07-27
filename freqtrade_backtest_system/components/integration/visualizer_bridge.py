"""
Strategy Visualizer integration bridge
"""
import json
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import streamlit as st

from utils.data_models import StrategyInfo, BacktestResult
from utils.error_handling import ErrorHandler, error_handler, ExecutionError

class StrategyVisualizerBridge:
    """Bridge for integrating with strategy_visualizer project"""
    
    def __init__(self, visualizer_path: str = "../strategy_visualizer"):
        """
        Initialize visualizer bridge
        Args:
            visualizer_path: path to strategy_visualizer project
        """
        self.visualizer_path = Path(visualizer_path)
        self.data_exchange_dir = Path("data_exchange")
        self.data_exchange_dir.mkdir(exist_ok=True)
        
        # Check if visualizer project exists
        self.is_available = self._check_visualizer_availability()
    
    def _check_visualizer_availability(self) -> bool:
        """Check if strategy visualizer is available"""
        try:
            app_file = self.visualizer_path / "app.py"
            return app_file.exists()
        except Exception:
            return False
    
    @error_handler(Exception, show_error=True)
    def export_strategy_for_visualization(self, strategy_info: StrategyInfo) -> Optional[Path]:
        """
        Export strategy data for visualization
        Args:
            strategy_info: strategy information
        Returns:
            path to exported data file
        """
        if not self.is_available:
            ErrorHandler.log_warning("Strategy visualizer not available")
            return None
        
        try:
            # Prepare strategy data for export
            export_data = {
                "strategy_name": strategy_info.name,
                "file_path": str(strategy_info.file_path),
                "class_name": strategy_info.class_name,
                "description": strategy_info.description,
                "parameters": strategy_info.parameters,
                "exported_at": datetime.now().isoformat(),
                "source": "freqtrade_backtest_system"
            }
            
            # Export to JSON file
            export_file = self.data_exchange_dir / f"strategy_{strategy_info.name}_{int(datetime.now().timestamp())}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Strategy data exported: {export_file}")
            return export_file
            
        except Exception as e:
            ErrorHandler.log_error(f"Error exporting strategy data: {str(e)}")
            raise ExecutionError(f"Failed to export strategy data: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def export_backtest_results(self, results: List[BacktestResult]) -> Optional[Path]:
        """
        Export backtest results for analysis
        Args:
            results: list of backtest results
        Returns:
            path to exported results file
        """
        if not results:
            return None
        
        try:
            # Prepare results data for export
            export_data = {
                "results": [],
                "exported_at": datetime.now().isoformat(),
                "source": "freqtrade_backtest_system",
                "total_strategies": len(results)
            }
            
            for result in results:
                result_data = {
                    "strategy_name": result.strategy_name,
                    "metrics": {
                        "total_return_pct": result.metrics.total_return_pct,
                        "win_rate": result.metrics.win_rate,
                        "max_drawdown_pct": result.metrics.max_drawdown_pct,
                        "sharpe_ratio": result.metrics.sharpe_ratio,
                        "sortino_ratio": result.metrics.sortino_ratio,
                        "total_trades": result.metrics.total_trades,
                        "winning_trades": result.metrics.winning_trades,
                        "losing_trades": result.metrics.losing_trades,
                        "avg_profit": result.metrics.avg_profit,
                        "avg_profit_pct": result.metrics.avg_profit_pct
                    },
                    "config": {
                        "timeframe": result.config.timeframe,
                        "start_date": result.config.start_date,
                        "end_date": result.config.end_date,
                        "pairs": result.config.pairs,
                        "initial_balance": result.config.initial_balance
                    },
                    "timestamp": result.timestamp.isoformat(),
                    "execution_time": result.execution_time,
                    "trades_count": len(result.trades)
                }
                export_data["results"].append(result_data)
            
            # Export to JSON file
            export_file = self.data_exchange_dir / f"backtest_results_{int(datetime.now().timestamp())}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Backtest results exported: {export_file}")
            return export_file
            
        except Exception as e:
            ErrorHandler.log_error(f"Error exporting backtest results: {str(e)}")
            raise ExecutionError(f"Failed to export backtest results: {str(e)}")
    
    @error_handler(Exception, show_error=True)
    def launch_visualizer(self, strategy_file: str = None) -> bool:
        """
        Launch strategy visualizer application
        Args:
            strategy_file: specific strategy file to visualize
        Returns:
            whether launch was successful
        """
        if not self.is_available:
            ErrorHandler.log_warning("Strategy visualizer not available")
            return False
        
        try:
            # Build command to launch visualizer
            cmd = ["streamlit", "run", "app.py"]
            
            if strategy_file:
                cmd.extend(["--", "--strategy", strategy_file])
            
            # Launch in background
            process = subprocess.Popen(
                cmd,
                cwd=self.visualizer_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            ErrorHandler.log_info("Strategy visualizer launched")
            return True
            
        except Exception as e:
            ErrorHandler.log_error(f"Error launching visualizer: {str(e)}")
            return False
    
    def get_visualizer_url(self, port: int = 8501) -> str:
        """Get strategy visualizer URL"""
        return f"http://localhost:{port}"
    
    @error_handler(Exception, show_error=True)
    def create_integration_link(self, strategy_name: str, result_data: Dict[str, Any]) -> str:
        """
        Create integration link for strategy visualization
        Args:
            strategy_name: name of strategy
            result_data: backtest result data
        Returns:
            integration link URL
        """
        try:
            # Create data file for integration
            link_data = {
                "strategy_name": strategy_name,
                "backtest_data": result_data,
                "created_at": datetime.now().isoformat(),
                "integration_type": "backtest_result"
            }
            
            link_file = self.data_exchange_dir / f"link_{strategy_name}_{int(datetime.now().timestamp())}.json"
            with open(link_file, 'w', encoding='utf-8') as f:
                json.dump(link_data, f, indent=2, ensure_ascii=False)
            
            # Create URL with data file parameter
            base_url = self.get_visualizer_url()
            link_url = f"{base_url}?data_file={link_file.name}"
            
            return link_url
            
        except Exception as e:
            ErrorHandler.log_error(f"Error creating integration link: {str(e)}")
            return self.get_visualizer_url()
    
    def get_data_exchange_files(self) -> List[Dict[str, Any]]:
        """Get list of data exchange files"""
        files = []
        try:
            for file_path in self.data_exchange_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "type": data.get("source", "unknown"),
                        "created": datetime.fromtimestamp(file_path.stat().st_ctime),
                        "size": file_path.stat().st_size
                    })
                except Exception:
                    continue
        except Exception as e:
            ErrorHandler.log_warning(f"Error reading data exchange files: {str(e)}")
        
        return sorted(files, key=lambda x: x["created"], reverse=True)
    
    def cleanup_old_exchange_files(self, days_old: int = 7) -> int:
        """Clean up old data exchange files"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        try:
            for file_path in self.data_exchange_dir.glob("*.json"):
                if file_path.stat().st_ctime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception:
                        continue
        except Exception as e:
            ErrorHandler.log_warning(f"Error cleaning up exchange files: {str(e)}")
        
        return deleted_count

class VisualizerIntegrationPanel:
    """Streamlit panel for visualizer integration"""
    
    def __init__(self):
        """Initialize integration panel"""
        self.bridge = StrategyVisualizerBridge()
    
    def render(self, strategies: List[StrategyInfo] = None, results: List[BacktestResult] = None):
        """
        Render integration panel
        Args:
            strategies: available strategies
            results: backtest results
        """
        st.subheader("🔗 Strategy Visualizer 集成")
        
        if not self.bridge.is_available:
            st.error("❌ Strategy Visualizer 不可用")
            st.info("请确保 strategy_visualizer 项目在正确的路径下")
            return
        
        st.success("✅ Strategy Visualizer 可用")
        
        # Create tabs for different functions
        tab1, tab2, tab3 = st.tabs(["🚀 启动可视化", "📤 数据导出", "📁 数据管理"])
        
        with tab1:
            self._render_launch_tab(strategies, results)
        
        with tab2:
            self._render_export_tab(strategies, results)
        
        with tab3:
            self._render_management_tab()
    
    def _render_launch_tab(self, strategies: List[StrategyInfo], results: List[BacktestResult]):
        """Render launch tab"""
        st.write("**启动 Strategy Visualizer 进行深度分析**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 启动 Strategy Visualizer", type="primary"):
                with st.spinner("正在启动 Strategy Visualizer..."):
                    if self.bridge.launch_visualizer():
                        st.success("Strategy Visualizer 启动成功！")
                        visualizer_url = self.bridge.get_visualizer_url()
                        st.info(f"访问地址: {visualizer_url}")
                        
                        # Provide link to open in browser
                        if st.button("🌐 在浏览器中打开"):
                            webbrowser.open(visualizer_url)
                    else:
                        st.error("启动失败，请检查 Strategy Visualizer 配置")
        
        with col2:
            if strategies and st.button("📊 分析选定策略"):
                # Export current strategies for analysis
                exported_files = []
                for strategy in strategies[:5]:  # Limit to 5 strategies
                    export_file = self.bridge.export_strategy_for_visualization(strategy)
                    if export_file:
                        exported_files.append(export_file)
                
                if exported_files:
                    st.success(f"已导出 {len(exported_files)} 个策略数据")
                    # Launch visualizer with exported data
                    self.bridge.launch_visualizer()
        
        # Integration links
        if results:
            st.subheader("🔗 集成链接")
            st.write("为每个策略创建可视化链接：")
            
            for result in results[:3]:  # Show first 3 results
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**{result.strategy_name}**")
                    st.write(f"收益率: {result.metrics.total_return_pct:.2f}%")
                
                with col2:
                    if st.button(f"🔗 可视化", key=f"viz_{result.strategy_name}"):
                        # Create integration link
                        result_data = {
                            "metrics": result.metrics.to_dict(),
                            "config": result.config.to_dict(),
                            "trades_count": len(result.trades)
                        }
                        
                        link_url = self.bridge.create_integration_link(
                            result.strategy_name, 
                            result_data
                        )
                        
                        st.success(f"集成链接已创建")
                        st.code(link_url)
    
    def _render_export_tab(self, strategies: List[StrategyInfo], results: List[BacktestResult]):
        """Render export tab"""
        st.write("**导出数据到 Strategy Visualizer**")
        
        # Export strategies
        if strategies:
            st.subheader("📋 导出策略信息")
            
            selected_strategies = st.multiselect(
                "选择要导出的策略",
                [s.name for s in strategies],
                default=[s.name for s in strategies[:3]]
            )
            
            if selected_strategies and st.button("📤 导出策略数据"):
                exported_files = []
                for strategy_name in selected_strategies:
                    strategy = next(s for s in strategies if s.name == strategy_name)
                    export_file = self.bridge.export_strategy_for_visualization(strategy)
                    if export_file:
                        exported_files.append(export_file)
                
                if exported_files:
                    st.success(f"成功导出 {len(exported_files)} 个策略文件")
                    for file_path in exported_files:
                        st.write(f"- {file_path.name}")
        
        # Export backtest results
        if results:
            st.subheader("📊 导出回测结果")
            
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox("导出格式", ["完整数据", "仅指标", "仅配置"])
            
            with col2:
                include_trades = st.checkbox("包含交易详情", value=False)
            
            if st.button("📤 导出回测结果"):
                export_file = self.bridge.export_backtest_results(results)
                if export_file:
                    st.success(f"回测结果已导出: {export_file.name}")
                    
                    # Show export summary
                    st.write("**导出摘要:**")
                    st.write(f"- 策略数量: {len(results)}")
                    st.write(f"- 文件大小: {export_file.stat().st_size / 1024:.1f} KB")
                    st.write(f"- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _render_management_tab(self):
        """Render data management tab"""
        st.write("**数据交换文件管理**")
        
        # Get exchange files
        exchange_files = self.bridge.get_data_exchange_files()
        
        if not exchange_files:
            st.info("暂无数据交换文件")
            return
        
        # Display files table
        import pandas as pd
        df_files = pd.DataFrame(exchange_files)
        df_files['size_kb'] = (df_files['size'] / 1024).round(1)
        
        st.dataframe(
            df_files[['name', 'type', 'size_kb', 'created']],
            column_config={
                'name': '文件名',
                'type': '类型',
                'size_kb': '大小(KB)',
                'created': '创建时间'
            },
            use_container_width=True
        )
        
        # File operations
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ 清理旧文件"):
                days_old = st.number_input("清理天数前的文件", min_value=1, max_value=30, value=7)
                deleted_count = self.bridge.cleanup_old_exchange_files(days_old)
                st.success(f"已清理 {deleted_count} 个旧文件")
                if deleted_count > 0:
                    st.rerun()
        
        with col2:
            if st.button("📁 打开数据目录"):
                try:
                    import os
                    os.startfile(str(self.bridge.data_exchange_dir))
                    st.success("数据目录已打开")
                except Exception as e:
                    st.error(f"打开目录失败: {str(e)}")
        
        with col3:
            if st.button("🔄 刷新文件列表"):
                st.rerun()
        
        # Data exchange statistics
        st.subheader("📈 数据交换统计")
        
        if exchange_files:
            total_files = len(exchange_files)
            total_size = sum(f['size'] for f in exchange_files)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("总文件数", total_files)
            
            with col2:
                st.metric("总大小", f"{total_size / 1024:.1f} KB")
            
            with col3:
                latest_file = max(exchange_files, key=lambda x: x['created'])
                st.metric("最新文件", latest_file['name'][:20] + "...")