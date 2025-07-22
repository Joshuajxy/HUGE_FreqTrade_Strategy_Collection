# 用户使用指南

## 快速开始

### 1. 安装和运行

```bash
# 进入项目目录
cd strategy_visualizer

# 安装依赖
pip install -r requirements.txt

# 启动应用
python run.py
# 或者
streamlit run app.py
```

### 2. 使用流程

1. **打开应用** - 浏览器访问 http://localhost:8501
2. **上传文件** - 在侧边栏上传策略分析JSON文件
3. **查看流程图** - 在主界面查看策略执行流程图
4. **交互探索** - 点击流程图节点查看详细信息
5. **策略分析** - 在右侧面板查看策略详情
6. **回测分析** - 配置并运行回测（开发中）

## 功能说明

### 流程图可视化

- **绿色节点**: 已实现的策略接口
- **黄色节点**: 未实现的策略接口  
- **蓝色节点**: Freqtrade核心流程
- **点击节点**: 查看详细实现信息
- **悬停节点**: 查看简要描述

### 策略详情面板

- **基本信息**: 策略名称、描述、作者等
- **参数配置**: ROI、止损、时间框架等
- **技术指标**: 使用的技术指标及参数
- **接口实现**: 详细的接口实现情况

### 回测功能（开发中）

- **配置回测**: 设置时间范围、交易对等
- **执行回测**: 调用Freqtrade回测引擎
- **结果可视化**: 显示收益曲线、交易信号等

## 策略分析文件格式

工具需要标准化的JSON格式策略分析文件，包含：

```json
{
  "strategy_name": "策略名称",
  "description": "策略描述", 
  "interfaces": {
    "populate_indicators": {
      "implemented": true,
      "description": "功能描述",
      "pseudocode": "伪代码",
      "input_params": [...],
      "output_description": "输出描述",
      "logic_explanation": "逻辑说明"
    }
  },
  "indicators": [...],
  "parameters": {...},
  "buy_conditions": [...],
  "sell_conditions": [...],
  "risk_management": {...}
}
```

## 生成策略分析文件

使用LM工具和提供的prompt模板分析freqtrade策略代码：

1. 使用 `prompts/strategy_analysis.yaml` 中的prompt
2. 输入freqtrade策略代码
3. 获得标准化JSON分析结果
4. 上传到可视化工具

## 常见问题

### Q: 如何生成策略分析文件？
A: 使用LM工具（如ChatGPT、Claude等）配合提供的prompt模板分析策略代码。

### Q: 支持哪些策略文件？
A: 支持所有标准的freqtrade策略文件，需要先转换为JSON分析格式。

### Q: 回测功能何时可用？
A: 回测功能正在开发中，当前版本提供模拟界面。

### Q: 如何贡献代码？
A: 欢迎提交Issue和Pull Request到项目仓库。

## 技术支持

如遇到问题，请：

1. 检查依赖是否正确安装
2. 确认策略分析文件格式正确
3. 查看控制台错误信息
4. 提交Issue描述问题详情