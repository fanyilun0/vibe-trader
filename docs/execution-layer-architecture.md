# 执行层架构说明

## 架构概述

执行层采用**适配器模式**和**管理器模式**，实现了平台无关的交易执行系统。

### 核心设计原则

1. **抽象与解耦**: 通过 `ExecutionInterface` 抽象接口，将交易策略逻辑与具体平台完全解耦
2. **统一管理**: `ExecutionManager` 作为协调器，统一管理账户状态查询和交易执行
3. **灵活扩展**: 通过适配器模式，轻松支持多个交易平台

## 架构层次

```
┌─────────────────────────────────────────────────┐
│            Main Application (主程序)             │
│                   src/main.py                   │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│         Execution Manager (执行管理器)           │
│          src/execution/manager.py               │
│                                                 │
│  职责:                                          │
│  - 状态查询 (账户余额、持仓)                     │
│  - 数据反馈 (构建 AI 提示词)                     │
│  - 指令分派 (执行交易决策)                       │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│      ExecutionInterface (抽象接口)               │
│        src/execution/interface.py               │
│                                                 │
│  定义标准方法:                                   │
│  - get_open_positions()                         │
│  - get_account_balance()                        │
│  - execute_order()                              │
│  - close_position()                             │
│  - update_position_pnl()                        │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│          API Adapters (适配器层)                 │
│        src/execution/adapters.py                │
│                                                 │
│  具体实现:                                       │
│  ├─ BinanceMockAdapter (模拟合约)               │
│  ├─ BinanceAdapter (真实交易)                   │
│  ├─ HypeAdapter (Hype 平台)                     │
│  └─ AsterAdapter (Aster 平台)                   │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│       Platform Implementation (平台实现)         │
│                                                 │
│  - BinanceMockExecution (完整模拟交易引擎)       │
│  - Binance API (真实币安 API)                   │
│  - Hype API / Aster API (其他平台)              │
└─────────────────────────────────────────────────┘
```

## 核心组件

### 1. ExecutionInterface (抽象接口)

**位置**: `src/execution/interface.py`

定义所有执行适配器必须实现的标准方法：

- `get_open_positions()` - 获取持仓
- `get_account_balance()` - 获取账户余额  
- `execute_order(decision, current_price)` - 执行订单
- `close_position(symbol, exit_price)` - 平仓
- `update_position_pnl(symbol, current_price)` - 更新盈亏

### 2. ExecutionManager (执行管理器)

**位置**: `src/execution/manager.py`

执行层的总协调器，职责包括：

1. **状态查询**: 在每个决策周期开始时获取账户状态
2. **数据反馈**: 将账户信息反馈给上层，用于构建 AI 提示词
3. **指令分派**: 将 AI 决策传递给适配器执行

**关键方法**:
- `get_account_state()` - 获取完整账户状态
- `refresh_account_state()` - 刷新账户状态缓存（在周期开始时调用）
- `update_positions_pnl(prices)` - 更新所有持仓盈亏（Mock模式使用）
- `execute_decision(decision, price)` - 执行交易决策

### 3. API Adapters (适配器层)

**位置**: `src/execution/adapters.py`

将标准接口适配到具体平台：

#### BinanceMockAdapter
- 模拟币安永续合约交易
- 完整的账户管理和盈亏计算
- **默认配置** (不再需要用户手动设置):
  - 初始余额: 10,000 USDT
  - 杠杆倍数: 10x
  - Taker 手续费: 0.04%
  - Maker 手续费: 0.02%

#### BinanceAdapter
- 真实币安 API 集成（支持 testnet 和主网）
- 完整的合约交易执行逻辑
- 账户数据缓存机制（避免重复API调用）
- 开仓、平仓、查询账户状态等完整功能
- ⚠️ 主网模式需谨慎使用

#### HypeAdapter / AsterAdapter
- 其他平台的适配器 (存根实现)

## 配置简化

### 移除的配置项

以下配置项已从 `env.example` 和 `config.py` 中移除：

```python
# ❌ 不再需要
MOCK_INITIAL_BALANCE
MOCK_LEVERAGE  
MOCK_TAKER_FEE
MOCK_MAKER_FEE
```

这些参数现在在 `BinanceMockAdapter` 中硬编码为合理的默认值。

### 保留的配置项

```bash
# 仅需配置交易模式
PAPER_TRADING=true  # true=模拟交易, false=实盘交易
```

## 使用示例

### 创建执行管理器

```python
from src.execution.manager import create_execution_manager

# 自动根据配置创建合适的执行管理器
manager = create_execution_manager(binance_client=None)
```

### 获取账户状态

```python
# 获取完整账户状态 (用于构建 AI 提示词)
account_state = manager.get_account_state()

# 返回字典包含:
# - balance: 余额信息
# - positions: 持仓列表  
# - total_equity: 总权益
# - available_balance: 可用余额
# - unrealized_pnl: 未实现盈亏
```

### 执行交易决策

```python
# 执行 AI 决策
result = manager.execute_decision(
    decision=ai_decision,  # TradingDecision 对象
    current_price=50000.0   # 当前市场价格
)

# 检查结果
if result['status'] == 'SUCCESS':
    print("交易成功!")
    if 'position' in result:
        print(f"持仓: {result['position']}")
```

## 数据流

### 完整的决策-执行周期

1. **数据摄取** → 获取市场数据
2. **数据处理** → 计算技术指标
3. **状态刷新** → `manager.refresh_account_state()` 刷新账户数据缓存（仅一次API调用）
4. **状态查询** → `manager.get_account_state()` 获取账户信息（使用缓存）
5. **AI 决策** → 使用账户状态构建提示词，生成决策
6. **风险检查** → 验证决策安全性
7. **执行交易** → `manager.execute_decision()` 执行订单（自动刷新缓存）
8. **状态保存** → `manager.save_state()` 持久化状态

## 优势

### 1. 模块化与解耦
- 核心交易逻辑与具体平台完全分离
- 可以独立开发、测试和维护各个模块

### 2. 易于测试
- 通过切换适配器轻松在模拟/实盘间切换
- 支持回测和策略评估

### 3. 灵活扩展
- 添加新平台只需实现新的适配器
- 无需修改上层业务逻辑

### 4. 简化配置
- 移除了繁琐的模拟交易参数配置
- 使用合理的默认值，开箱即用

### 5. 性能优化
- 账户数据缓存机制，避免重复API调用
- 在同一决策周期内复用账户数据（1秒缓存）
- 减少API请求次数，提高响应速度

## 文件结构

```
src/execution/
├── __init__.py          # 模块导出
├── interface.py         # ExecutionInterface 抽象接口
├── manager.py           # ExecutionManager 管理器
├── adapters.py          # 各平台适配器实现
└── binance_mock.py      # Binance 模拟交易引擎 (底层实现)
```

## 测试验证

所有核心功能已通过测试：

✅ 执行管理器初始化  
✅ 账户状态获取  
✅ 持仓盈亏更新  
✅ 模拟交易执行  
✅ 账户状态同步  

## 参考

详细设计理念请参考: `docs/vibe-trader-arti.md` 第 V 章 - 抽象执行层

