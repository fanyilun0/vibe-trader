# 提示词构建验证报告

## 概述

本文档验证 `signal_generator.py` 中的提示词构建是否完全符合 `template-description.md` 的要求。

## 验证结果：✅ 通过

所有必需的数据字段都已正确实现，并且添加了额外的增强指标。

---

## 详细对比

### 1. 总体状态数据 ✅

| 字段名 | template-description.md | signal_generator.py | 状态 |
|--------|------------------------|---------------------|------|
| minutes_trading | ✅ 必需 | ✅ 实现 (`metadata['minutes_trading']`) | ✅ |
| current_timestamp | ✅ 必需 | ✅ 实现 (`metadata['current_timestamp']`) | ✅ |
| invocation_count | ✅ 必需 | ✅ 实现 (`metadata['invocation_count']`) | ✅ |

**实现位置**: `signal_generator.py` 第 134-142 行

```python
It has been {metadata.get('minutes_trading', 0)} minutes since you started trading.
The current time is {metadata.get('current_timestamp', 'N/A')} and you've been invoked {metadata.get('invocation_count', 0)} times.
```

---

### 2. 各币种市场数据 ✅

#### 2.1 当前状态指标

| 字段名 | template-description.md | signal_generator.py | 状态 |
|--------|------------------------|---------------------|------|
| current_price | ✅ 必需 | ✅ 实现 (`data['current_price']`) | ✅ |
| current_ema20 | ✅ 必需 | ✅ 实现 (`current_ind['ema20']`) | ✅ |
| current_macd | ✅ 必需 | ✅ 实现 (`current_ind['macd']`) | ✅ |
| current_rsi_7_period | ✅ 必需 | ✅ 实现 (`current_ind['rsi7']`) | ✅ |

**实现位置**: `signal_generator.py` 第 190 行

```python
current_price = {data.get('current_price', 0.0):.2f}, current_ema20 = {current_ind.get('ema20', 0.0):.2f}, current_macd = {current_ind.get('macd', 0.0):.2f}, current_rsi (7 period) = {current_ind.get('rsi7', 0.0):.2f}
```

#### 2.2 衍生品市场数据

| 字段名 | template-description.md | signal_generator.py | 状态 |
|--------|------------------------|---------------------|------|
| latest_open_interest | ✅ 必需 | ✅ 实现 (`open_interest['latest']`) | ✅ |
| average_open_interest | ✅ 必需 | ✅ 实现 (`open_interest['average']`) | ✅ |
| funding_rate | ✅ 必需 | ✅ 实现 (`data['funding_rate']`) | ✅ |

**实现位置**: `signal_generator.py` 第 192-194 行

```python
Open Interest: Latest: {data.get('open_interest', {}).get('latest', 0.0)} Average: {data.get('open_interest', {}).get('average', 0.0)}
Funding Rate: {data.get('funding_rate', 0.0):.6f}
```

#### 2.3 短期（Intraday）时间序列数据

| 字段名 | template-description.md | signal_generator.py | 状态 |
|--------|------------------------|---------------------|------|
| mid_prices_list | ✅ 必需 | ✅ 实现 (`prices_str`) | ✅ |
| ema20_list | ✅ 必需 | ✅ 实现 (`ema20_str`) | ✅ |
| macd_list | ✅ 必需 | ✅ 实现 (`macd_str`) | ✅ |
| rsi_7_period_list | ✅ 必需 | ✅ 实现 (`rsi7_str`) | ✅ |
| rsi_14_period_list | ✅ 必需 | ✅ 实现 (`rsi14_str`) | ✅ |

**实现位置**: `signal_generator.py` 第 196-201 行

```python
Intraday series ({intraday.get('interval', Config.INTRADAY_INTERVAL)} interval, oldest → latest):
Mid prices: {prices_str}
EMA indicators (20-period): {ema20_str}
MACD indicators: {macd_str}
RSI indicators (7-Period): {rsi7_str}
RSI indicators (14-Period): {rsi14_str}
```

#### 2.4 长期（4小时）时间序列数据

| 字段名 | template-description.md | signal_generator.py | 状态 |
|--------|------------------------|---------------------|------|
| long_term_ema20 | ✅ 必需 | ✅ 实现 (`longterm_current['ema20']`) | ✅ |
| long_term_ema50 | ✅ 必需 | ✅ 实现 (`longterm_current['ema50']`) | ✅ |
| long_term_atr3 | ✅ 必需 | ✅ 实现 (`longterm_current['atr3']`) | ✅ |
| long_term_atr14 | ✅ 必需 | ✅ 实现 (`longterm_current['atr14']`) | ✅ |
| long_term_macd_list | ✅ 必需 | ✅ 实现 (`longterm_macd_str`) | ✅ |
| long_term_rsi_14_period_list | ✅ 必需 | ✅ 实现 (`longterm_rsi14_str`) | ✅ |

**实现位置**: `signal_generator.py` 第 208-212 行

```python
Longer-term context ({longterm.get('interval', Config.LONGTERM_INTERVAL)} timeframe):
20-Period EMA: {longterm_current.get('ema20', 0.0):.2f} vs. 50-Period EMA: {longterm_current.get('ema50', 0.0):.2f}
3-Period ATR: {longterm_current.get('atr3', 0.0):.2f} vs. 14-Period ATR: {longterm_current.get('atr14', 0.0):.2f}
MACD indicators: {longterm_macd_str}
RSI indicators (14-Period): {longterm_rsi14_str}
```

#### 2.5 增强指标（额外实现） 🎁

| 字段名 | 说明 | 状态 |
|--------|------|------|
| Bollinger Bands | 布林带上中下轨 | ✅ 已实现 |
| VWAP | 成交量加权平均价 | ✅ 已实现 |
| ADX | 趋势强度指标 | ✅ 已实现 |

**实现位置**: `signal_generator.py` 第 203-206 行

```python
Additional Intraday Indicators:
Bollinger Bands: Upper={current_ind.get('bb_upper', 0.0):.2f}, Middle={current_ind.get('bb_middle', 0.0):.2f}, Lower={current_ind.get('bb_lower', 0.0):.2f}
VWAP: {current_ind.get('vwap', 0.0):.2f}
ADX (14-period): {current_ind.get('adx', 0.0):.2f}
```

---

### 3. 账户信息与表现 ✅

| 字段名 | template-description.md | signal_generator.py | 状态 |
|--------|------------------------|---------------------|------|
| total_return_percent | ✅ 必需 | ✅ 实现 (`account_info['total_return_percent']`) | ✅ |
| available_cash | ✅ 必需 | ✅ 实现 (`account_info['available_cash']`) | ✅ |
| account_value | ✅ 必需 | ✅ 实现 (`account_info['account_value']`) | ✅ |
| sharpe_ratio | ✅ 必需 | ✅ 实现 (`account_info['sharpe_ratio']`) | ✅ |
| list_of_position_dictionaries | ✅ 必需 | ✅ 实现 (`account_info['positions']`) | ✅ |

**实现位置**: `signal_generator.py` 第 220-229 行

```python
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {account_info.get('total_return_percent', 0.0):.2f}%
Available Cash: ${account_info.get('available_cash', 0.0):.2f}
Current Account Value: ${account_info.get('account_value', 0.0):.2f}
Sharpe Ratio: {account_info.get('sharpe_ratio', 0.0):.2f}

Current live positions & performance:
{positions_str}
```

#### 持仓信息字段（来自 data_aggregator.py）

每个持仓字典包含以下字段（符合 template-description.md 要求）：

| 字段名 | 说明 | 状态 |
|--------|------|------|
| symbol | 交易对符号 | ✅ |
| side | LONG/SHORT | ✅ |
| size | 持仓数量 | ✅ |
| entry_price | 开仓价格 | ✅ |
| mark_price | 当前价格 | ✅ |
| liquidation_price | 强平价格 | ✅ |
| unrealized_pnl | 未实现盈亏 | ✅ |
| leverage | 杠杆倍数 | ✅ |
| notional | 名义价值 | ✅ |

**实现位置**: `data_aggregator.py` 第 279-289 行

---

## 数据流验证 ✅

### 完整的数据流程

```
1. data_aggregator.py: fetch_all_data()
   └─> 获取市场数据和账户信息
   
2. data_aggregator.py: _fetch_symbol_data()
   └─> 获取每个币种的 K线、资金费率、订单簿等
   
3. data_aggregator.py: _calculate_indicators()
   └─> 计算所有技术指标（EMA, RSI, MACD, ATR, Bollinger Bands, VWAP, ADX）
   
4. signal_generator.py: _construct_prompt()
   └─> 构建完整的 LLM 提示词
       ├─> _format_coin_data() - 格式化币种数据
       ├─> _format_account_info() - 格式化账户信息
       └─> _get_trading_instructions() - 添加交易指令
       
5. DeepSeek API
   └─> 返回交易信号 JSON
```

---

## 提示词模板示例

### 完整提示词结构

```
================================================================================
总体状态
================================================================================
It has been {minutes_trading} minutes since you started trading.
The current time is {current_timestamp} and you've been invoked {invocation_count} times.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST
Timeframes note: Intraday series are provided at 3m intervals. Long-term context uses 4h intervals.

CURRENT MARKET STATE FOR ALL COINS

================================================================================
币种数据（重复每个交易对）
================================================================================
ALL BTCUSDT DATA
current_price = 67500.00, current_ema20 = 67200.00, current_macd = 150.50, current_rsi (7 period) = 55.30

In addition, here is the latest BTCUSDT open interest and funding rate for perps:
Open Interest: Latest: 1234567890.0 Average: 1200000000.0
Funding Rate: 0.000100

Intraday series (3m interval, oldest → latest):
Mid prices: [67400, 67420, 67450, ...]
EMA indicators (20-period): [67100, 67120, 67150, ...]
MACD indicators: [145.2, 147.5, 150.5, ...]
RSI indicators (7-Period): [52.3, 54.1, 55.3, ...]
RSI indicators (14-Period): [58.2, 59.1, 60.0, ...]

Additional Intraday Indicators:
Bollinger Bands: Upper=67800.00, Middle=67400.00, Lower=67000.00
VWAP: 67450.00
ADX (14-period): 32.50

Longer-term context (4h timeframe):
20-Period EMA: 67000.00 vs. 50-Period EMA: 66500.00
3-Period ATR: 450.00 vs. 14-Period ATR: 520.00
MACD indicators: [120.5, 130.2, 140.8, ...]
RSI indicators (14-Period): [60.5, 62.1, 63.8, ...]

================================================================================
账户信息
================================================================================
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): 5.25%
Available Cash: $9500.00
Current Account Value: $10525.00
Sharpe Ratio: 1.85

Current live positions & performance:
[
  {
    "symbol": "BTCUSDT",
    "side": "LONG",
    "size": 0.001,
    "entry_price": 67000.0,
    "mark_price": 67500.0,
    "liquidation_price": 60000.0,
    "unrealized_pnl": 0.5,
    "leverage": 5,
    "notional": 67.5
  }
]

================================================================================
交易指令
================================================================================
TRADING INSTRUCTIONS
... (详细的交易规则和风险管理要求)
```

---

## 验证结论

### ✅ 完全符合要求

1. **所有必需字段**: 100% 实现
2. **数据格式**: 符合 template-description.md 规范
3. **增强功能**: 
   - 添加了布林带（Bollinger Bands）
   - 添加了 VWAP（成交量加权平均价）
   - 添加了 ADX（趋势强度指标）
   - 添加了订单簿深度数据

4. **提示词结构**: 清晰、有序、易于 LLM 理解

### 🎯 最佳实践

当前实现遵循了以下最佳实践：

1. **数据时序**: "OLDEST → NEWEST" 明确标注
2. **单位标注**: 时间间隔明确标注（3m, 4h）
3. **数值格式化**: 保留适当的小数位数
4. **缺失值处理**: 使用默认值避免 None
5. **可读性**: 使用清晰的标题和分隔符

---

## 建议

### 当前实现已经非常完善，可以考虑的未来增强：

1. **市场情绪指标**: 
   - 恐慌贪婪指数
   - 多空比例

2. **链上数据**:
   - 大额转账监控
   - 交易所净流入/流出

3. **宏观数据**:
   - BTC 主导率
   - DeFi TVL 变化

但这些都是可选的，当前实现已经满足所有必需要求。

---

## 相关文件

- `signal_generator.py` - 提示词构建核心逻辑
- `data_aggregator.py` - 数据获取和指标计算
- `template-description.md` - 数据字段要求文档
- `template.md` - 提示词模板示例

---

**验证日期**: 2025-10-23  
**验证状态**: ✅ 通过  
**覆盖率**: 100%

