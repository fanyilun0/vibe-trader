# 提示词管理器使用指南

## 概述

提示词管理器（`PromptManager`）是一个专门用于处理 AI 交易决策提示词的模块，负责：

1. 加载系统提示词和用户提示词模板
2. 基于真实交易数据构建完整的提示词
3. 支持多币种市场数据格式
4. 为 DeepSeek API 调用准备消息列表

## 文件结构

```
vibe-trader/
├── src/
│   ├── prompt_manager.py          # 提示词管理器核心模块
│   └── ai_decision.py             # AI 决策核心（已集成 PromptManager）
├── prompt-template/
│   └── prompts/
│       ├── predictive_system_prompt_cn.md    # 系统提示词模板
│       └── user_prompt_cn.md                 # 用户提示词模板（参考）
└── prompts/                       # 保存生成的提示词（用于调试）
```

## 主要功能

### 1. 提示词管理器初始化

```python
from src.prompt_manager import create_prompt_manager

# 创建提示词管理器
pm = create_prompt_manager()
```

提示词管理器会自动加载：
- 系统提示词：`prompt-template/prompts/predictive_system_prompt_cn.md`
- 用户提示词模板：`prompt-template/prompts/user_prompt_cn.md`（作为参考）

### 2. 构建多币种市场数据

提示词管理器支持多币种数据输入：

```python
market_features_by_coin = {
    "BTC": {
        "symbol": "BTCUSDT",
        "current_price": 110493.5,
        "current_ema20": 110569.568,
        "current_macd": -24.498,
        "current_rsi_7": 37.586,
        "latest_open_interest": 27262.63,
        "average_open_interest": 27259.01,
        "funding_rate": 2.7394e-06,
        "mid_prices_list": [110696.5, 110585.5, ...],
        "ema20_list": [110621.386, 110618.016, ...],
        # ... 更多技术指标
    },
    "ETH": {
        # ... ETH 的市场数据
    }
}
```

### 3. 构建账户特征数据

```python
account_features = {
    "total_return_percent": 31.81,
    "available_cash": 4927.64,
    "account_value": 13180.63,
    "list_of_position_dictionaries": [
        {
            "symbol": "ETH",
            "quantity": 4.87,
            "entry_price": 3844.03,
            "current_price": 3978.05,
            "leverage": 15,
            "exit_plan": {
                "profit_target": 4227.35,
                "stop_loss": 3714.95,
                "invalidation_condition": "如果价格在 3 分钟 K 线上收于 3800 以下"
            },
            "confidence": 0.75,
            "risk_usd": 624.38
        }
    ]
}
```

### 4. 生成完整消息列表

```python
# 构建消息列表（用于 API 调用）
messages = pm.get_messages(
    market_features_by_coin,
    account_features,
    global_state
)

# messages 格式：
# [
#   {"role": "system", "content": "系统提示词..."},
#   {"role": "user", "content": "用户提示词..."}
# ]
```

### 5. 保存提示词到文件（调试用）

```python
# 保存提示词到文件
filepath = pm.save_prompt_to_file(
    market_features_by_coin,
    account_features,
    global_state,
    save_dir="prompts"  # 默认保存目录
)

# 生成的文件名格式：prompt_20251030_211610_inv1691.txt
```

## 在 AI 决策核心中的集成

提示词管理器已经集成到 `ai_decision.py` 中：

```python
class AIDecisionCore:
    def __init__(self, api_key, base_url, model):
        # ...
        # 初始化提示词管理器
        self.prompt_manager = create_prompt_manager()
    
    def call_llm(self, market_features_by_coin, account_features, global_state):
        # 使用 PromptManager 构建消息
        messages = self.prompt_manager.get_messages(
            market_features_by_coin,
            account_features,
            global_state
        )
        
        # 调用 DeepSeek API
        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": 8000,
                "temperature": 1.0,
                "response_format": {"type": "json_object"}
            }
        )
        return response.json()
```

## DeepSeek 返回格式

DeepSeek 会返回多币种 JSON 格式：

```json
{
  "BTC": {
    "trade_signal_args": {
      "coin": "BTC",
      "signal": "hold",
      "quantity": 0.12,
      "profit_target": 118136.15,
      "stop_loss": 102026.675,
      "invalidation_condition": "如果价格在 3 分钟 K 线上收于 105000 以下",
      "leverage": 10,
      "confidence": 0.75,
      "risk_usd": 619.23,
      "justification": ""
    }
  },
  "ETH": {
    "trade_signal_args": {
      "coin": "ETH",
      "signal": "buy_to_enter",
      "quantity": 5.0,
      "profit_target": 4200.0,
      "stop_loss": 3700.0,
      "invalidation_condition": "如果价格在 3 分钟 K 线上收于 3700 以下",
      "leverage": 15,
      "confidence": 0.8,
      "risk_usd": 650.0,
      "justification": "RSI 超卖，MACD 金叉，EMA 支撑位"
    }
  }
}
```

## 信号类型映射

提示词管理器会将 DeepSeek 返回的信号类型映射到系统支持的动作：

| DeepSeek 信号 | 系统动作 | 说明 |
|--------------|---------|------|
| `hold` | `HOLD` | 持有当前仓位 |
| `buy_to_enter` | `BUY` | 开多仓 |
| `sell_to_enter` | `SELL` | 开空仓 |
| `close_position` | `CLOSE_POSITION` | 平仓 |

## 数据流程

```
1. 数据摄取 (data_ingestion.py)
   ↓
2. 数据处理 (data_processing.py)
   ↓
3. 提示词管理器 (prompt_manager.py)
   - 加载系统提示词模板
   - 构建用户提示词
   - 组装完整消息列表
   ↓
4. AI 决策核心 (ai_decision.py)
   - 调用 DeepSeek API
   - 解析多币种 JSON 响应
   - 转换为 TradingDecision 对象
   ↓
5. 风险管理 (risk_management.py)
   ↓
6. 执行管理 (execution/manager.py)
```

## 与旧版本的区别

### 旧版本（已移除）
- 硬编码的英文提示词
- 单币种数据格式
- 提示词逻辑混在 `ai_decision.py` 中

### 新版本（当前）
- 从文件加载中文提示词模板
- 支持多币种数据格式
- 提示词逻辑独立在 `prompt_manager.py` 中
- 更好的可维护性和可扩展性
- 真实数据流（移除了 mock 逻辑）

## 最佳实践

1. **提示词模板维护**：
   - 系统提示词在 `prompt-template/prompts/predictive_system_prompt_cn.md`
   - 修改后无需重启，下次调用自动生效

2. **调试提示词**：
   - 查看 `prompts/` 目录下生成的提示词文件
   - 每次 AI 调用都会保存一份提示词快照

3. **多币种扩展**：
   - 只需在 `market_features_by_coin` 中添加新币种的数据
   - 提示词管理器会自动格式化所有币种的数据

4. **性能优化**：
   - 使用 `system` 和 `user` 两条消息结构
   - 系统提示词可以被 DeepSeek 缓存，减少 token 消耗

## 故障排查

### 问题：提示词模板加载失败
**解决方案**：
- 确认文件路径：`prompt-template/prompts/predictive_system_prompt_cn.md`
- 检查文件编码：应为 UTF-8
- 查看日志中的警告信息

### 问题：DeepSeek 返回格式错误
**解决方案**：
- 检查生成的提示词文件（`prompts/` 目录）
- 确认系统提示词中的 JSON schema 正确
- 查看 DeepSeek API 的响应内容

### 问题：币种数据缺失
**解决方案**：
- 确保 `market_features_by_coin` 包含所有必需字段
- 参考测试脚本中的数据格式
- 检查数据处理模块的输出

## 未来扩展

可能的改进方向：

1. **多语言支持**：支持英文提示词模板切换
2. **提示词版本管理**：记录提示词模板的版本历史
3. **A/B 测试**：支持多个提示词模板的对比测试
4. **动态提示词**：根据市场条件动态调整提示词内容
5. **提示词优化器**：自动优化提示词以提高 AI 决策质量

## 总结

提示词管理器提供了一个清晰、可维护的方式来管理 AI 交易决策的提示词。通过将提示词逻辑独立出来，系统变得更加模块化和易于扩展。

