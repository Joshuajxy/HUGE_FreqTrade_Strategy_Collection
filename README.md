# Freqtrade策略可视化工具

一个图形化的交互界面，用于分析和理解freqtrade交易策略的设计思路。

## 功能特性

- 📊 **流程图可视化** - 显示freqtrade完整执行流程图
- 🔍 **策略分析** - 详细展示策略接口实现和参数配置
- 📈 **回测集成** - 集成freqtrade回测功能并实时可视化结果
- 🎯 **交互式界面** - 点击节点查看详细信息，支持动态展示

## 快速开始

### 1. 安装依赖

```bash
cd strategy_visualizer
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

### 3. 使用示例

1. 打开浏览器访问 http://localhost:8501
2. 上传策略分析JSON文件（可下载示例文件）
3. 查看流程图和策略详情
4. 点击流程图节点获取详细信息

## 项目结构

```
strategy_visualizer/
├── app.py                      # 主应用入口
├── components/                 # 组件模块
│   ├── flowchart/              # 流程图组件
│   ├── backtest/               # 回测组件
│   └── strategy_details/       # 策略详情组件
├── utils/                      # 工具模块
├── prompts/                    # LM处理模板
└── tests/                      # 测试文件
```

## 使用说明

### 策略分析文件格式

工具需要经过LM处理的标准化策略分析JSON文件，包含以下字段：

- `strategy_name`: 策略名称
- `description`: 策略描述
- `interfaces`: 接口函数实现详情
- `indicators`: 技术指标列表
- `parameters`: 参数配置
- `buy_conditions`: 买入条件
- `sell_conditions`: 卖出条件
- `risk_management`: 风险管理设置

### LM处理Prompt

使用 `prompts/strategy_analysis.yaml` 中的prompt模板来分析freqtrade策略代码。

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码结构

- 每个组件都是独立的模块，便于维护和扩展
- 使用Streamlit构建Web界面，纯Python开发
- 使用Plotly + NetworkX实现交互式流程图
- 模块化设计，单个文件代码量控制在15-50行

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。

## 许可证

MIT License