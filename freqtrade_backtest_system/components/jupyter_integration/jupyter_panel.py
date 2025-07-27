"""
Jupyter analysis panel for Streamlit interface
"""
import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import webbrowser
import threading

from utils.data_models import BacktestResult
from utils.error_handling import ErrorHandler, error_handler
from .template_manager import JupyterTemplateManager
from .report_generator import ReportGenerator
from .lab_integration import JupyterLabIntegration

class JupyterAnalysisPanel:
    """Jupyter analysis panel for Streamlit interface"""
    
    def __init__(self):
        """Initialize Jupyter analysis panel"""
        self.template_manager = JupyterTemplateManager()
        self.report_generator = ReportGenerator(self.template_manager)
        self.lab_integration = JupyterLabIntegration()
        
        # Initialize session state
        if 'jupyter_lab_running' not in st.session_state:
            st.session_state.jupyter_lab_running = False
        if 'jupyter_reports' not in st.session_state:
            st.session_state.jupyter_reports = []
    
    def render(self, results: List[BacktestResult] = None):
        """
        Render Jupyter analysis panel
        Args:
            results: list of backtest results for analysis
        """
        st.header("📊 Jupyter 分析面板")
        
        # Create tabs for different functions
        tab1, tab2, tab3, tab4 = st.tabs([
            "🚀 Jupyter Lab", 
            "📝 分析模板", 
            "📊 生成报告", 
            "📁 报告管理"
        ])
        
        with tab1:
            self._render_jupyter_lab_tab()
        
        with tab2:
            self._render_templates_tab()
        
        with tab3:
            self._render_reports_tab(results)
        
        with tab4:
            self._render_reports_management_tab()
    
    def _render_jupyter_lab_tab(self):
        """Render Jupyter Lab control tab"""
        st.subheader("🚀 Jupyter Lab 控制")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            **Jupyter Lab 集成功能：**
            - 一键启动 Jupyter Lab 环境
            - 自动导入回测数据
            - 预配置分析模板
            - 实时数据同步
            """)
        
        with col2:
            # Check if Jupyter Lab is running
            is_running = self.lab_integration.is_running()
            st.session_state.jupyter_lab_running = is_running
            
            if is_running:
                st.success("✅ Jupyter Lab 正在运行")
                if st.button("🛑 停止 Jupyter Lab", type="secondary"):
                    with st.spinner("正在停止 Jupyter Lab..."):
                        if self.lab_integration.stop_jupyter_lab():
                            st.success("Jupyter Lab 已停止")
                            st.session_state.jupyter_lab_running = False
                            st.rerun()
                        else:
                            st.error("停止 Jupyter Lab 失败")
                
                if st.button("🌐 打开浏览器"):
                    try:
                        webbrowser.open(f"http://localhost:{self.lab_integration.port}")
                        st.success("已在浏览器中打开 Jupyter Lab")
                    except Exception as e:
                        st.error(f"打开浏览器失败: {str(e)}")
            else:
                st.warning("⏸️ Jupyter Lab 未运行")
                if st.button("🚀 启动 Jupyter Lab", type="primary"):
                    with st.spinner("正在启动 Jupyter Lab..."):
                        if self.lab_integration.start_jupyter_lab(auto_open=False):
                            st.success("Jupyter Lab 启动成功！")
                            st.session_state.jupyter_lab_running = True
                            st.info(f"访问地址: http://localhost:{self.lab_integration.port}")
                            st.rerun()
                        else:
                            st.error("启动 Jupyter Lab 失败")
        
        # Configuration section
        st.subheader("⚙️ 配置选项")
        
        col1, col2 = st.columns(2)
        with col1:
            port = st.number_input("端口号", min_value=8000, max_value=9999, value=8888)
            if port != self.lab_integration.port:
                self.lab_integration.port = port
        
        with col2:
            auto_open = st.checkbox("启动时自动打开浏览器", value=True)
        
        # Workspace info
        st.subheader("📁 工作空间信息")
        workspace_path = self.lab_integration.work_dir
        st.code(f"工作目录: {workspace_path}")
        
        # Show workspace structure
        if workspace_path.exists():
            st.write("**目录结构:**")
            structure = self._get_workspace_structure(workspace_path)
            st.text(structure)
    
    def _render_templates_tab(self):
        """Render analysis templates tab"""
        st.subheader("📝 分析模板管理")
        
        # Get available templates
        templates = self.template_manager.get_available_templates()
        
        if not templates:
            st.warning("没有可用的分析模板")
            return
        
        # Template selection
        template_names = [t.name for t in templates]
        selected_template = st.selectbox("选择模板", template_names)
        
        if selected_template:
            template = next(t for t in templates if t.name == selected_template)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**描述:** {template.description}")
                st.write(f"**类型:** {template.template_type}")
                st.write(f"**参数:** {', '.join(template.parameters)}")
                
                # Show template info
                template_info = self.template_manager.get_template_info(selected_template)
                if template_info:
                    st.write(f"**创建时间:** {template_info['created']}")
                    st.write(f"**文件大小:** {template_info['size']} bytes")
                    st.write(f"**单元格数量:** {template_info['cells_count']}")
            
            with col2:
                if st.button("📋 复制到工作空间"):
                    try:
                        import shutil
                        dest_path = self.lab_integration.work_dir / "templates" / f"{selected_template}.ipynb"
                        shutil.copy2(template.file_path, dest_path)
                        st.success(f"模板已复制到: {dest_path}")
                    except Exception as e:
                        st.error(f"复制失败: {str(e)}")
                
                if st.button("🗑️ 删除模板"):
                    if self.template_manager.delete_template(selected_template):
                        st.success("模板已删除")
                        st.rerun()
                    else:
                        st.error("删除失败")
        
        # Create custom template section
        st.subheader("➕ 创建自定义模板")
        
        with st.expander("创建新模板"):
            template_name = st.text_input("模板名称")
            template_desc = st.text_area("模板描述")
            template_type = st.selectbox("模板类型", ["analysis", "comparison", "risk", "trades", "custom"])
            
            parameters = st.text_area("参数列表 (每行一个)", placeholder="strategy_name\nresults_data\nconfig_data")
            
            if st.button("创建模板") and template_name:
                try:
                    param_list = [p.strip() for p in parameters.split('\n') if p.strip()]
                    
                    # Create basic template structure
                    cells_content = [
                        {
                            "type": "markdown",
                            "content": f"## {template_desc}\n\n这是一个自定义分析模板。"
                        },
                        {
                            "type": "code", 
                            "content": "# 导入必要的库\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\nprint('库导入成功！')"
                        },
                        {
                            "type": "code",
                            "content": "# 数据加载区域\n# 参数将在此处自动注入\nprint('等待数据注入...')"
                        },
                        {
                            "type": "markdown",
                            "content": "## 分析结果\n\n在此添加您的分析代码和可视化。"
                        }
                    ]
                    
                    template_path = self.template_manager.create_custom_template(
                        template_name,
                        template_desc,
                        template_type,
                        param_list,
                        cells_content
                    )
                    
                    st.success(f"模板创建成功: {template_path}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"创建模板失败: {str(e)}")
    
    def _render_reports_tab(self, results: List[BacktestResult]):
        """Render report generation tab"""
        st.subheader("📊 生成分析报告")
        
        if not results:
            st.warning("没有可用的回测结果数据")
            return
        
        # Report type selection
        report_types = {
            "strategy": "策略分析报告",
            "comparison": "策略对比报告", 
            "risk": "风险分析报告",
            "trade": "交易详情报告",
            "custom": "自定义报告"
        }
        
        selected_report_type = st.selectbox(
            "选择报告类型",
            options=list(report_types.keys()),
            format_func=lambda x: report_types[x]
        )
        
        # Output format selection
        output_formats = ["html", "pdf", "markdown"]
        output_format = st.selectbox("输出格式", output_formats)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if selected_report_type in ["strategy", "risk", "trade"]:
                # Single strategy selection
                strategy_names = [r.strategy_name for r in results]
                selected_strategy = st.selectbox("选择策略", strategy_names)
                selected_result = next(r for r in results if r.strategy_name == selected_strategy)
            
            elif selected_report_type == "comparison":
                # Multiple strategy selection
                strategy_names = [r.strategy_name for r in results]
                selected_strategies = st.multiselect("选择要对比的策略", strategy_names, default=strategy_names[:3])
                selected_results = [r for r in results if r.strategy_name in selected_strategies]
            
            elif selected_report_type == "custom":
                # Custom template selection
                templates = self.template_manager.get_available_templates()
                template_names = [t.name for t in templates if t.template_type == "custom"]
                if template_names:
                    selected_template = st.selectbox("选择自定义模板", template_names)
                else:
                    st.warning("没有可用的自定义模板")
                    return
        
        with col2:
            # Additional options
            if selected_report_type == "strategy":
                include_trades = st.checkbox("包含交易详情", value=True)
            
            report_name = st.text_input("报告名称 (可选)", placeholder="自动生成")
        
        # Generate report button
        if st.button("🔄 生成报告", type="primary"):
            try:
                with st.spinner("正在生成报告..."):
                    report_path = None
                    
                    if selected_report_type == "strategy":
                        report_path = self.report_generator.generate_strategy_report(
                            selected_result, 
                            output_format, 
                            include_trades
                        )
                    
                    elif selected_report_type == "comparison" and selected_results:
                        # Create comparison result
                        from components.results.comparator import ResultComparator
                        comparator = ResultComparator()
                        comparison = comparator.compare_strategies(selected_results)
                        
                        report_path = self.report_generator.generate_comparison_report(
                            selected_results,
                            comparison,
                            output_format
                        )
                    
                    elif selected_report_type == "risk":
                        report_path = self.report_generator.generate_risk_report(
                            selected_result,
                            output_format
                        )
                    
                    elif selected_report_type == "trade":
                        report_path = self.report_generator.generate_trade_report(
                            selected_result,
                            output_format
                        )
                    
                    elif selected_report_type == "custom":
                        # Prepare data for custom template
                        data = {
                            "results": [r.to_dict() for r in results],
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        output_name = report_name or f"custom_report_{int(time.time())}"
                        report_path = self.report_generator.generate_custom_report(
                            selected_template,
                            data,
                            output_name,
                            output_format
                        )
                    
                    if report_path:
                        st.success(f"报告生成成功: {report_path.name}")
                        
                        # Add to session state
                        if 'jupyter_reports' not in st.session_state:
                            st.session_state.jupyter_reports = []
                        
                        st.session_state.jupyter_reports.append({
                            'name': report_path.name,
                            'path': str(report_path),
                            'type': selected_report_type,
                            'format': output_format,
                            'created': datetime.now(),
                            'size': report_path.stat().st_size
                        })
                        
                        # Provide download link
                        with open(report_path, 'rb') as f:
                            st.download_button(
                                label="📥 下载报告",
                                data=f.read(),
                                file_name=report_path.name,
                                mime=self._get_mime_type(output_format)
                            )
                    else:
                        st.error("报告生成失败")
                        
            except Exception as e:
                st.error(f"生成报告时出错: {str(e)}")
                ErrorHandler.log_error(f"Report generation error: {str(e)}")
    
    def _render_reports_management_tab(self):
        """Render reports management tab"""
        st.subheader("📁 报告管理")
        
        # Get generated reports
        reports = self.report_generator.get_generated_reports()
        
        if not reports:
            st.info("暂无生成的报告")
            return
        
        # Display reports table
        df_reports = pd.DataFrame(reports)
        df_reports['created'] = pd.to_datetime(df_reports['created'])
        df_reports['size_mb'] = (df_reports['size'] / 1024 / 1024).round(2)
        
        # Sort by creation time
        df_reports = df_reports.sort_values('created', ascending=False)
        
        st.dataframe(
            df_reports[['name', 'format', 'size_mb', 'created']],
            column_config={
                'name': '报告名称',
                'format': '格式',
                'size_mb': '大小(MB)',
                'created': '创建时间'
            },
            use_container_width=True
        )
        
        # Report actions
        st.subheader("📋 报告操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download selected report
            report_names = df_reports['name'].tolist()
            selected_report = st.selectbox("选择报告", report_names)
            
            if selected_report and st.button("📥 下载报告"):
                report_info = df_reports[df_reports['name'] == selected_report].iloc[0]
                report_path = Path(report_info['path'])
                
                if report_path.exists():
                    with open(report_path, 'rb') as f:
                        st.download_button(
                            label=f"下载 {selected_report}",
                            data=f.read(),
                            file_name=selected_report,
                            mime=self._get_mime_type(report_info['format'])
                        )
                else:
                    st.error("报告文件不存在")
        
        with col2:
            # Delete selected report
            if selected_report and st.button("🗑️ 删除报告"):
                if self.report_generator.delete_report(selected_report):
                    st.success("报告已删除")
                    st.rerun()
                else:
                    st.error("删除失败")
        
        with col3:
            # Cleanup old reports
            days_old = st.number_input("清理天数前的报告", min_value=1, max_value=365, value=30)
            if st.button("🧹 清理旧报告"):
                deleted_count = self.report_generator.cleanup_old_reports(days_old)
                st.success(f"已清理 {deleted_count} 个旧报告")
                if deleted_count > 0:
                    st.rerun()
        
        # Export data section
        st.subheader("📤 数据导出")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox("导出格式", ["json", "csv", "pickle"])
        
        with col2:
            if st.button("📤 导出到工作空间"):
                try:
                    # Get current results from session state
                    if 'backtest_results' in st.session_state:
                        results = st.session_state.backtest_results
                        exported_files = self.lab_integration.export_data_to_workspace(
                            results, export_format
                        )
                        
                        st.success(f"数据已导出: {len(exported_files)} 个文件")
                        for file_type, file_path in exported_files.items():
                            st.write(f"- {file_type}: {file_path.name}")
                    else:
                        st.warning("没有可导出的回测结果")
                        
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
    
    def _get_workspace_structure(self, path: Path, prefix: str = "", max_depth: int = 2, current_depth: int = 0) -> str:
        """Get workspace directory structure"""
        if current_depth > max_depth:
            return ""
        
        structure = ""
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                structure += f"{prefix}{current_prefix}{item.name}\n"
                
                if item.is_dir() and current_depth < max_depth:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    structure += self._get_workspace_structure(item, next_prefix, max_depth, current_depth + 1)
        except PermissionError:
            structure += f"{prefix}[Permission Denied]\n"
        
        return structure
    
    def _get_mime_type(self, format_type: str) -> str:
        """Get MIME type for file format"""
        mime_types = {
            'html': 'text/html',
            'pdf': 'application/pdf',
            'markdown': 'text/markdown',
            'json': 'application/json',
            'csv': 'text/csv'
        }
        return mime_types.get(format_type, 'application/octet-stream')