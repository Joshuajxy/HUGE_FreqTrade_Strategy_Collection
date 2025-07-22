# Requirements Document

## Introduction

本项目旨在创建一个图形化的交互界面，用于分析和理解freqtrade交易策略的设计思路。该工具将通过流程图的形式展示交易策略的接口函数和调用流程，并提供详细的实现逻辑解释，帮助用户更好地理解复杂的交易策略。

## Requirements

### Requirement 1

**User Story:** 作为一个交易策略分析师，我希望能够看到freqtrade完整的执行流程图，包含所有关键节点，以便理解交易策略在整个系统中的位置和作用。

#### Acceptance Criteria

1. WHEN 用户打开应用 THEN 系统 SHALL 显示一个包含freqtrade所有关键执行节点的完整流程图
2. WHEN 用户查看流程图 THEN 系统 SHALL 显示包括数据获取、策略初始化、指标计算、信号生成、风险管理、订单执行等所有关键环节
3. WHEN 用户查看流程图 THEN 系统 SHALL 以清晰的视觉方式展示各个环节之间的调用关系和执行顺序
4. WHEN 用户查看非策略相关的节点时 THEN 系统 SHALL 显示节点的基本功能说明但不提供详细的代码解释
5. WHEN 用户查看策略相关的接口节点时 THEN 系统 SHALL 提供可展开的详细解释和伪代码说明功能

### Requirement 2

**User Story:** 作为一个策略开发者，我希望能够加载经过LM处理的标准化策略分析文件，查看该策略中每个接口函数的具体实现逻辑，以便深入理解策略的设计思路。

#### Acceptance Criteria

1. WHEN 用户选择一个标准化策略分析文件 THEN 系统 SHALL 加载该文件并显示策略的所有接口函数信息
2. WHEN 用户点击流程图中的某个接口节点 THEN 系统 SHALL 显示该接口在当前策略中的实现逻辑
3. WHEN 显示实现逻辑时 THEN 系统 SHALL 同时提供文字解释和伪代码形式的说明
4. IF 某个接口在当前策略中未实现 THEN 系统 SHALL 显示默认行为或标记为未实现
5. WHEN 系统加载分析文件时 THEN 系统 SHALL 验证文件格式的正确性和完整性

### Requirement 3

**User Story:** 作为一个交易策略研究者，我希望能够交互式地浏览流程图，获得每个环节的详细信息，以便全面理解交易策略的执行过程。

#### Acceptance Criteria

1. WHEN 用户将鼠标悬停在流程图节点上 THEN 系统 SHALL 显示该节点的基本信息提示
2. WHEN 用户点击流程图节点 THEN 系统 SHALL 在侧边栏或弹窗中显示详细的实现信息
3. WHEN 用户浏览实现信息时 THEN 系统 SHALL 提供代码高亮和语法着色
4. WHEN 用户查看复杂逻辑时 THEN 系统 SHALL 提供可折叠的代码块和分层显示
5. WHEN 用户点击接口节点时 THEN 系统 SHALL 显示该接口的输入参数和输出结果的数据结构
6. WHEN 查看输入输出时 THEN 系统 SHALL 提供示例数据和数据类型说明

### Requirement 4

**User Story:** 作为一个策略比较分析师，我希望能够同时加载多个策略文件进行对比分析，以便识别不同策略之间的差异和共同点。

#### Acceptance Criteria

1. WHEN 用户选择多个策略文件 THEN 系统 SHALL 支持同时加载和分析多个策略
2. WHEN 查看多个策略时 THEN 系统 SHALL 提供策略切换功能
3. WHEN 比较不同策略时 THEN 系统 SHALL 高亮显示相同接口的不同实现
4. WHEN 进行策略对比时 THEN 系统 SHALL 提供并排显示或差异高亮功能



### Requirement 6

**User Story:** 作为一个策略执行流程分析师，我希望能够以状态机的形式动态展示代码的执行过程，并查看每个环节的输入输出数据，以便深入理解策略的运行机制。

#### Acceptance Criteria

1. WHEN 用户启动执行流程演示 THEN 系统 SHALL 以动画形式按顺序高亮显示各个接口函数的执行
2. WHEN 流程图处于动态演示模式时 THEN 系统 SHALL 显示当前执行状态和下一步将要执行的函数
3. WHEN 用户查看某个执行步骤时 THEN 系统 SHALL 显示该步骤的输入数据、处理逻辑和输出结果
4. WHEN 演示执行过程时 THEN 系统 SHALL 提供暂停、继续、重置和步进控制功能
5. WHEN 用户点击正在执行的节点时 THEN 系统 SHALL 显示实时的数据流和变量状态
6. WHEN 展示数据流时 THEN 系统 SHALL 以可视化方式显示DataFrame结构和关键指标值

### Requirement 7

**User Story:** 作为一个策略回测分析师，我希望能够集成freqtrade的回测功能，在图形化界面中实时观察回测过程和策略执行状态，并同时查看详细的回测结果图表，以便全面理解策略的表现和决策过程。

#### Acceptance Criteria

1. WHEN 用户启动回测时 THEN 系统 SHALL 调用freqtrade的回测引擎执行策略
2. WHEN 回测执行过程中 THEN 系统 SHALL 实时更新流程图显示当前处理的时间点和执行状态
3. WHEN 产生交易信号时 THEN 系统 SHALL 在流程图中高亮显示相关的决策节点和触发条件
4. WHEN 回测进行中 THEN 系统 SHALL 同步显示技术指标计算、信号生成、风险管理等各个环节的实时数据
5. WHEN 遇到买入/卖出决策时 THEN 系统 SHALL 暂停并详细展示决策依据和相关参数
6. WHEN 回测执行时 THEN 系统 SHALL 在流程图下方实时显示价格走势图表，包括K线图和技术指标
7. WHEN 产生交易信号时 THEN 系统 SHALL 在价格图表上标记买入/卖出点位和对应的价格
8. WHEN 显示回测结果时 THEN 系统 SHALL 展示成交量柱状图和累计收益率曲线
9. WHEN 回测完成时 THEN 系统 SHALL 提供完整的回测结果统计，包括总收益率、最大回撤、夏普比率等关键指标
10. WHEN 用户查看回测历史时 THEN 系统 SHALL 支持回放特定时间段的执行过程并同步更新图表显示

### Requirement 8

**User Story:** 作为一个界面交互用户，我希望流程图能够自适应不同长度的文字内容，保持良好的视觉效果和可读性，以便舒适地浏览和理解策略信息。

#### Acceptance Criteria

1. WHEN 流程图显示节点信息时 THEN 系统 SHALL 根据文字内容长度自动调整节点大小
2. WHEN 节点包含长文本解释时 THEN 系统 SHALL 提供文本换行和滚动功能
3. WHEN 展开详细解释时 THEN 系统 SHALL 动态调整布局以适应内容变化
4. WHEN 多个节点同时展开时 THEN 系统 SHALL 自动重新排列流程图布局避免重叠
5. WHEN 用户缩放流程图时 THEN 系统 SHALL 保持文字的清晰度和可读性
6. WHEN 显示伪代码时 THEN 系统 SHALL 根据代码长度自适应调整代码块大小

### Requirement 9

**User Story:** 作为一个策略分析工具的开发者，我希望定义统一的LM处理prompt和标准化输出格式，确保所有策略代码都能被一致地转换为可视化工具能够理解的格式。

#### Acceptance Criteria

1. WHEN 项目初始化时 THEN 系统 SHALL 提供标准的LM prompt模板用于分析freqtrade策略代码
2. WHEN 使用LM处理策略时 THEN 系统 SHALL 确保输出格式包含策略名称、接口函数列表、每个函数的实现逻辑、输入输出参数等标准字段
3. WHEN 生成标准化文件时 THEN 系统 SHALL 使用JSON或YAML格式确保结构化和可解析性
4. WHEN 定义prompt时 THEN 系统 SHALL 包含对freqtrade所有标准接口函数的识别和分析指令
5. WHEN 处理复杂策略逻辑时 THEN 系统 SHALL 要求LM提供分层的伪代码和文字解释
6. WHEN 输出分析结果时 THEN 系统 SHALL 包含策略的整体描述、关键技术指标、交易逻辑摘要等元信息

### Requirement 10

**User Story:** 作为一个开发效率优化者，我希望系统尽可能使用现有的成熟框架和库来实现图形化功能，以减少代码开发量并提高系统的稳定性和可维护性。

#### Acceptance Criteria

1. WHEN 选择技术栈时 THEN 系统 SHALL 优先使用成熟的Web框架（如React、Vue等）来构建用户界面
2. WHEN 实现流程图功能时 THEN 系统 SHALL 使用现有的图形库（如D3.js、Cytoscape.js、Mermaid等）而非从零开发
3. WHEN 处理数据可视化时 THEN 系统 SHALL 利用现有的可视化库（如Chart.js、Plotly等）
4. WHEN 实现代码高亮时 THEN 系统 SHALL 使用成熟的语法高亮库（如Prism.js、highlight.js等）
5. WHEN 构建项目时 THEN 系统 SHALL 使用标准的构建工具和包管理器
6. WHEN 实现复杂功能时 THEN 系统 SHALL 优先寻找现有解决方案而非重新发明轮子

### Requirement 11

**User Story:** 作为一个技术用户，我希望系统具有良好的性能和用户体验，能够快速加载和处理大量的策略文件，以便高效地进行策略分析工作。

#### Acceptance Criteria

1. WHEN 系统加载策略文件时 THEN 系统 SHALL 在3秒内完成单个策略文件的解析
2. WHEN 处理大型策略文件时 THEN 系统 SHALL 显示加载进度指示器
3. WHEN 用户进行交互操作时 THEN 系统 SHALL 在500毫秒内响应用户操作
4. WHEN 系统遇到解析错误时 THEN 系统 SHALL 提供清晰的错误信息和建议解决方案