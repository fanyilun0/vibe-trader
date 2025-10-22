## **模板使用的数据说明**

此模板结构化地整合了多种数据，主要分为三大类：**总体状态**、**各币种市场数据**和**账户信息**。

### **1\. 总体状态数据**

这些是关于交易机器人本身运行状态的宏观数据。

* {minutes\_trading}: 交易开始至今的总分钟数。  
* {current\_timestamp}: 当前的时间戳。  
* {invocation\_count}: 程序被调用的总次数。

### **2\. 各币种市场数据**

模板为每个加密货币（如 BTC, ETH, SOL 等）都提供了相同结构的数据块。

* **当前状态指标**:  
  * {current\_price}: 最新中间价。  
  * {current\_ema20}: 最新的20周期指数移动平均线。  
  * {current\_macd}: 最新的MACD指标值。  
  * {current\_rsi\_7\_period}: 最新的7周期相对强弱指数。  
* **衍生品市场数据**:  
  * {latest\_open\_interest}: 最新持仓量。  
  * {average\_open\_interest}: 平均持仓量。  
  * {funding\_rate}: 当前资金费率。  
* **短期（Intraday）时间序列数据**:  
  * {mid\_prices\_list}: 一系列中间价。  
  * {ema20\_list}: 一系列20周期EMA值。  
  * {macd\_list}: 一系列MACD指标值。  
  * {rsi\_7\_period\_list}: 一系列7周期RSI值。  
  * {rsi\_14\_period\_list}: 一系列14周期RSI值。  
* **长期（4小时）时间序列数据**:  
  * {long\_term\_ema20} vs. {long\_term\_ema50}: 20周期EMA vs 50周期EMA。  
  * {long\_term\_atr3} vs. {long\_term\_atr14}: 3周期ATR vs 14周期ATR（平均真实波幅）。  
  * {long\_term\_current\_volume} vs. {long\_term\_average\_volume}: 当前交易量 vs 平均交易量。  
  * {long\_term\_macd\_list}: 一系列长周期的MACD指标值。  
  * {long\_term\_rsi\_14\_period\_list}: 一系列长周期的14周期RSI值。

### **3\. 账户信息与表现**

这部分提供了关于您交易账户的财务状况和风险指标。

* {total\_return\_percent}: 当前总回报率。  
* {available\_cash}: 可用现金。  
* {account\_value}: 当前账户总价值。  
* {sharpe\_ratio}: 夏普比率，衡量经风险调整后的收益。  
* {list\_of\_position\_dictionaries}: 一个包含所有当前持仓信息的列表。每个持仓信息是一个字典，包含以下关键数据：  
  * symbol: 交易对符号。  
  * quantity: 持仓数量。  
  * entry\_price: 开仓价格。  
  * current\_price: 当前价格。  
  * liquidation\_price: 强平价格。  
  * unrealized\_pnl: 未实现盈亏。  
  * leverage: 杠杆倍数。  
  * exit\_plan: 包含止盈、止损和失效条件的退出计划。  
  * confidence: 对该笔交易的置信度。  
  * risk\_usd: 以美元计价的风险敞口。  
  * notional\_usd: 以美元计价的名义价值。