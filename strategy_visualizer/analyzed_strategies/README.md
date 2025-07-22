# 策略分析结果

本目录包含经过LLM分析的freqtrade策略文件，每个策略都被转换为标准化的JSON格式，可以直接在策略可视化工具中使用。

## 文件结构

- `*.json` - 策略分析结果文件
- `README.md` - 本说明文件

## 使用方法

1. 在策略可视化工具中点击"上传策略分析文件"
2. 选择对应的JSON文件
3. 查看策略的可视化分析结果

## 分析标准

每个JSON文件包含以下标准字段：
- `strategy_name` - 策略名称
- `description` - 策略描述
- `interfaces` - 接口函数实现详情
- `indicators` - 技术指标列表
- `parameters` - 策略参数配置
- `buy_conditions` - 买入条件
- `sell_conditions` - 卖出条件
- `risk_management` - 风险管理设置