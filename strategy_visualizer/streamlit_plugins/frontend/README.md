# st_plotly_zoom_sync 前端组件

此目录为 Streamlit 自定义组件的前端源码（React）。

## 开发/构建步骤
1. 安装依赖（首次构建或依赖变更时）
   ```
   npm install
   ```
2. 构建生产包（生成 build 目录，供 Python 端引用）
   ```
   npm run build
   ```
3. 构建完成后，Python 端即可通过 st_plotly_zoom_sync 组件实时获取 Plotly 缩放事件。

## 主要文件
- src/PlotlyZoomSync.jsx  组件主逻辑（监听 relayout 并回传）
- src/index.js           React 入口
- public/index.html      HTML 模板
- package.json           依赖和构建配置

---
如需自定义交互或扩展功能，可在 src/PlotlyZoomSync.jsx 中修改。
