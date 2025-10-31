# 账户信息增强 - 完整持仓数据支持

## 概述

本次更新完善了用户提示词中的账户信息部分，确保所有持仓相关的字段都能正确显示，并添加了夏普比率（Sharpe Ratio）指标。

## 更改内容

### 1. **prompt_manager.py** - 提示词格式增强

#### 主要改进：
- ✅ 支持多头/空头持仓的正确显示（quantity字段保留正负号）
- ✅ 添加所有订单执行相关字段：
  - `sl_oid` - 止损订单ID
  - `tp_oid` - 止盈订单ID  
  - `entry_oid` - 入场订单ID
  - `wait_for_fill` - 等待成交标志
  - `notional_usd` - 名义价值（美元）
- ✅ 添加夏普比率显示
- ✅ 改进字段获取逻辑，支持从多个来源获取价格数据

#### 关键代码更改：
```python
# 获取持仓数量（保留正负号）
quantity = pos.get('quantity', 0)
position_amt = pos.get('position_amt', quantity)
if position_amt != 0:
    quantity = position_amt  # 多头为正，空头为负

# 获取当前价格（支持多个字段）
current_price = pos.get('current_price') or pos.get('mark_price', 0)

# 添加夏普比率显示
sharpe_text = f"\n\n夏普比率: {sharpe_ratio:.3f}" if sharpe_ratio else ""
```

### 2. **data_processing.py** - 账户数据处理增强

#### 主要改进：
- ✅ 在处理持仓信息时保留 `position_amt`（原始值，含正负号）
- ✅ 添加 `mark_price` 字段作为备用价格来源
- ✅ 添加订单ID相关字段的占位符
- ✅ 改进清算价格的获取方式

#### 关键代码更改：
```python
position_dict = {
    'symbol': pos['symbol'],
    'quantity': abs(pos['position_amt']),  # 绝对值
    'position_amt': pos['position_amt'],  # 保留正负号
    'entry_price': pos['entry_price'],
    'current_price': pos['mark_price'],
    'mark_price': pos['mark_price'],
    'liquidation_price': pos.get('liquidation_price', 0),
    'unrealized_pnl': pos['unrealized_profit'],
    'leverage': pos['leverage'],
    # 订单相关字段
    'sl_oid': pos.get('sl_oid', -1),
    'tp_oid': pos.get('tp_oid', -1),
    'entry_oid': pos.get('entry_oid', -1),
    'wait_for_fill': pos.get('wait_for_fill', False),
}
```

### 3. **main.py** - 主程序增强

#### 主要改进：
- ✅ 从 `exit_plans` 中提取订单ID信息并补充到持仓数据
- ✅ 实现夏普比率计算（基于历史收益率）
- ✅ 重新组织代码流程，先获取exit_plans再构建account_features

#### 夏普比率计算：
```python
# 从历史业绩数据计算夏普比率
performance_history = self.state_manager.state.get('performance_history', [])
if len(performance_history) > 10:
    returns = []
    for i in range(1, len(performance_history)):
        prev_value = performance_history[i-1]['metrics'].get('account_value', 0)
        curr_value = performance_history[i]['metrics'].get('account_value', 0)
        if prev_value > 0:
            ret = (curr_value - prev_value) / prev_value
            returns.append(ret)
    
    # 年化夏普比率（假设每3分钟一次）
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    if std_return > 0:
        sharpe_ratio = mean_return / std_return * np.sqrt(175200)
```

#### 订单ID补充：
```python
# 从exit_plans中提取订单ID信息
enriched_positions = []
for pos in account_state['positions']:
    symbol = pos.get('symbol')
    enriched_pos = pos.copy()
    
    if symbol in exit_plans:
        exit_plan = exit_plans[symbol]
        enriched_pos['sl_oid'] = exit_plan.get('sl_oid', -1)
        enriched_pos['tp_oid'] = exit_plan.get('tp_oid', -1)
        enriched_pos['entry_oid'] = exit_plan.get('entry_oid', -1)
        enriched_pos['wait_for_fill'] = exit_plan.get('wait_for_fill', False)
    
    enriched_positions.append(enriched_pos)
```

### 4. **state_manager.py** - 状态管理增强

#### 主要改进：
- ✅ 在保存 `exit_plan` 时包含订单ID字段
- ✅ 支持存储和检索订单执行状态

#### 关键代码更改：
```python
self.state['position_exit_plans'][symbol] = {
    'profit_target': exit_plan.get('profit_target'),
    'stop_loss': exit_plan.get('stop_loss'),
    'invalidation_condition': exit_plan.get('invalidation_condition'),
    'leverage': exit_plan.get('leverage'),
    'confidence': exit_plan.get('confidence'),
    'risk_usd': exit_plan.get('risk_usd'),
    # 订单ID字段
    'sl_oid': exit_plan.get('sl_oid', -1),
    'tp_oid': exit_plan.get('tp_oid', -1),
    'entry_oid': exit_plan.get('entry_oid', -1),
    'wait_for_fill': exit_plan.get('wait_for_fill', False),
    'created_at': datetime.now().isoformat()
}
```

## 输出格式示例

### 更新前的格式：
```
### 这是你的账户信息和业绩

当前总回报率(百分比): 3.91%
可用现金: $4,635.67
**当前账户价值:** $5,187.00
**当前持仓详情:**

持仓列表（JSON格式）:
```json
[
  {
    "coin": "BTC",
    "signal": "hold",
    "quantity": 0.1,
    ...
  }
]
```

### 更新后的格式（与参考文件一致）：
```
### 这是你的账户信息和业绩

当前总回报率(百分比): 50.87%

可用现金: 4291.75

当前账户价值: 15086.69


当前持仓及执行情况: 

{'symbol': 'BTC', 'quantity': 0.12, 'entry_price': 107343.0, 'current_price': 110151.5, 'liquidation_price': 98244.59, 'unrealized_pnl': 337.02, 'leverage': 10, 'exit_plan': {'profit_target': 118136.15, 'stop_loss': 102026.675, 'invalidation_condition': 'If the price closes below 105000 on a 3-minute candle'}, 'confidence': 0.75, 'risk_usd': 619.2345, 'sl_oid': 206132736980, 'tp_oid': 206132723593, 'wait_for_fill': False, 'entry_oid': 206132712257, 'notional_usd': 13218.18} 
{'symbol': 'DOGE', 'quantity': -100230.0, 'entry_price': 0.18, 'current_price': 0.185535, 'liquidation_price': 0.19, 'unrealized_pnl': -214.29, 'leverage': 10, 'exit_plan': {'profit_target': 0.165215, 'stop_loss': 0.192755, 'invalidation_condition': 'If the price closes above 0.195 on a 3-minute candle'}, 'confidence': 0.7, 'risk_usd': 920.034, 'sl_oid': -1, 'tp_oid': -1, 'wait_for_fill': False, 'entry_oid': 217692868889, 'notional_usd': 18596.17} 


夏普比率: 0.414
```

## 持仓信息字段说明

| 字段 | 类型 | 说明 | 数据来源 |
|------|------|------|----------|
| `symbol` | string | 币种符号（去除USDT后缀） | Binance API |
| `quantity` | float | 持仓数量（多头为正，空头为负） | Binance API (position_amt) |
| `entry_price` | float | 入场价格 | Binance API |
| `current_price` | float | 当前标记价格 | Binance API (mark_price) |
| `liquidation_price` | float | 清算价格 | Binance API |
| `unrealized_pnl` | float | 未实现盈亏 | Binance API |
| `leverage` | int | 杠杆倍数 | Binance API |
| `exit_plan` | object | 退出计划（止盈/止损/失效条件） | State Manager |
| `confidence` | float | AI决策置信度 (0-1) | State Manager |
| `risk_usd` | float | 风险金额（USD） | State Manager |
| `sl_oid` | int | 止损订单ID（-1表示未设置） | State Manager |
| `tp_oid` | int | 止盈订单ID（-1表示未设置） | State Manager |
| `entry_oid` | int | 入场订单ID | State Manager |
| `wait_for_fill` | bool | 是否等待订单成交 | State Manager |
| `notional_usd` | float | 名义价值（USD） | 计算得出 |

## Binance API 参考

本次更新使用了以下 Binance API 端点：
- **Position Information V2**: `/fapi/v2/positionRisk`
  - 文档: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Position-Information-V2

API 返回的关键字段：
- `entryPrice` - 入场价格
- `markPrice` - 标记价格
- `liquidationPrice` - 清算价格
- `unRealizedProfit` - 未实现盈亏
- `positionAmt` - 持仓数量（多头为正，空头为负）
- `leverage` - 杠杆倍数
- `positionSide` - 持仓方向（LONG/SHORT/BOTH）

## 验证测试

所有更改已通过测试验证，确保：
- ✅ 总回报率正确显示
- ✅ 可用现金正确显示
- ✅ 账户价值正确显示
- ✅ 夏普比率正确显示
- ✅ 持仓信息完整（包含所有必需字段）
- ✅ 清算价格正确显示
- ✅ 订单ID正确显示
- ✅ 名义价值正确显示
- ✅ exit_plan正确显示
- ✅ 多头/空头持仓正确区分（通过quantity正负号）

## 后续优化建议

1. **实时订单ID更新**：当前订单ID需要在下单时通过执行层记录到state_manager，可以考虑在binance_adapter中自动完成这一流程。

2. **夏普比率优化**：当前使用简化版本计算，可以考虑：
   - 使用无风险利率作为基准
   - 调整时间窗口大小
   - 考虑滑动窗口计算

3. **持仓数据缓存**：当前每次都从API获取，可以考虑在决策周期内使用缓存减少API调用。

4. **数据验证**：添加更严格的数据验证逻辑，确保所有必需字段都存在且合法。

## 相关文档

- [Binance Position Information V2 API](https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Position-Information-V2)
- [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- [PROMPT_MANAGER_GUIDE.md](./PROMPT_MANAGER_GUIDE.md)

---

**更新日期**: 2025-10-31  
**版本**: v1.1.0

