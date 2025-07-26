# st_plotly_zoom_sync

Streamlit自定义组件：Plotly流程图缩放同步

- 实时监听Plotly缩放/平移（relayout）事件
- 自动回传缩放比例到Python后端
- 用于动态调整流程图字体、节点等显示信息

## 目录结构
- frontend/  前端React组件源码
- __init__.py  Python包入口
- plotly_zoom_sync.py  Python组件接口

## 用法
1. 进入frontend目录，npm install & npm run build
2. Python端import st_plotly_zoom_sync.plotly_zoom_sync
3. 像st.plotly_chart一样调用，实时获得缩放数据

---
如需详细开发/集成说明，请查看本README或联系开发者。
