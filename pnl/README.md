# PnL 追踪系统

## 简介

每日盈亏追踪系统负责记录和统计交易账户的盈亏数据。所有数据按日期保存在 `pnl/` 目录中。

## 数据结构

每个日期的数据保存为独立的JSON文件，格式为 `YYYYMMDD.json`，包含以下信息：

### 基础数据
- `date`: 日期
- `start_balance`: 当日起始余额
- `end_balance`: 当日结束余额
- `start_equity`: 当日起始权益
- `end_equity`: 当日结束权益
- `realized_pnl`: 已实现盈亏
- `unrealized_pnl`: 未实现盈亏
- `commission`: 累计手续费
- `net_pnl`: 净盈亏（已实现盈亏 - 手续费）
- `total_pnl`: 总盈亏（净盈亏 + 未实现盈亏）
- `return_pct`: 当日收益率（%）

### 操作统计
- `trades_count`: 交易次数（成交次数）
- `cycles_count`: 交易周期数
- `positions_opened`: 开仓次数
- `positions_closed`: 平仓次数
- `last_update`: 最后更新时间

### 详细记录

#### 1. 周期快照 (`snapshots`)
每个交易周期的状态快照：
```json
{
  "timestamp": "2025-11-06T12:34:56",
  "cycle": 1,
  "equity": 4801.76,
  "unrealized_pnl": 8.67,
  "action": "CLOSE_POSITION"
}
```

#### 2. 交易统计快照 (`trade_snapshots`)
**新功能** - 每次执行交易后的统计快照：
```json
{
  "timestamp": "2025-11-06T12:34:56",
  "cycle": 1,
  "realized_pnl": 125.63,
  "commission": 163.81,
  "net_pnl": -38.18,
  "trades_count": 129,
  "total_pnl": -39.61
}
```

用途：追踪交易统计数据的变化趋势，了解每次交易后的盈亏变化。

#### 3. 历史成交记录 (`historical_trades`)
**新功能** - 从Binance API获取的所有历史成交记录（完整原始数据）：
```json
{
  "symbol": "BNBUSDT",
  "id": 70172155,
  "orderId": 878208798,
  "side": "BUY",
  "price": "945.350",
  "qty": "0.98",
  "realizedPnl": "0",
  "marginAsset": "USDT",
  "quoteQty": "926.44300",
  "commission": "0.37057720",
  "commissionAsset": "USDT",
  "time": 1762433574102,
  "positionSide": "BOTH",
  "buyer": true,
  "maker": false,
  "time_readable": "2025-11-06 20:52:54"
}
```

**字段说明：**
- `symbol`: 交易对符号
- `id`: 交易ID（唯一标识）
- `orderId`: 订单ID
- `side`: 方向（BUY/SELL）
- `price`: 成交价格（字符串格式，保持精度）
- `qty`: 成交数量（字符串格式）
- `realizedPnl`: 已实现盈亏
- `marginAsset`: 保证金资产
- `quoteQty`: 成交金额
- `commission`: 手续费
- `commissionAsset`: 手续费资产
- `time`: 时间戳（毫秒）
- `positionSide`: 持仓方向（BOTH/LONG/SHORT）
- `buyer`: 是否为买方
- `maker`: 是否为挂单方（Maker）
- `time_readable`: 可读时间格式

**用途：**
- 保存完整的Binance API原始数据
- 支持详细的交易分析和审计
- 保持数据精度（价格和数量使用字符串格式）

## 使用方法

### 工具1: PnL数据查看器 (`pnl_viewer.py`)

用于查看每日PnL数据文件（包含统计信息和历史成交记录）

### 1. 查看每日盈亏摘要

```bash
# 查看今天的数据
python3 pnl/pnl_viewer.py

# 查看指定日期的数据
python3 pnl/pnl_viewer.py 20251106
```

### 2. 查看交易统计快照

查看每次交易后的统计变化：

```bash
python3 pnl/pnl_viewer.py 20251106 --snapshots

# 或使用简写
python3 pnl/pnl_viewer.py 20251106 -s
```

### 3. 查看历史成交记录

查看从Binance获取的所有成交记录：

```bash
python3 pnl/pnl_viewer.py 20251106 --trades

# 或使用简写
python3 pnl/pnl_viewer.py 20251106 -t
```

### 4. 比较快照变化

分析交易快照的变化趋势：

```bash
python3 pnl/pnl_viewer.py 20251106 --compare

# 或使用简写
python3 pnl/pnl_viewer.py 20251106 -c
```

### 5. 查看所有信息

```bash
python3 pnl/pnl_viewer.py 20251106 --all

# 或使用简写
python3 pnl/pnl_viewer.py 20251106 -a
```

### 6. 限制显示数量

```bash
# 只显示最近10条记录
python3 pnl/pnl_viewer.py 20251106 --all --limit 10

# 或使用简写
python3 pnl/pnl_viewer.py 20251106 -a -l 10
```

## 完整命令参数

```bash
usage: pnl_viewer.py [-h] [--trades] [--snapshots] [--compare] [--limit LIMIT] [--all] [date]

PnL数据查看器

positional arguments:
  date                  日期 (格式: YYYYMMDD)，默认为今天

optional arguments:
  -h, --help            显示帮助信息
  -t, --trades          显示历史成交记录
  -s, --snapshots       显示交易统计快照
  -c, --compare         比较快照变化
  -l, --limit LIMIT     显示的记录数量限制 (默认: 20)
  -a, --all             显示所有信息
```

### 工具2: 历史成交数据获取器 (`fetch_historical_trades.py`)

**新增功能** - 独立获取指定日期的历史成交数据

此工具用于单独获取和保存历史成交记录，保存的数据只包含交易信息，不含PnL统计。

#### 基本用法

```bash
# 获取今天的历史成交数据
python3 pnl/fetch_historical_trades.py

# 获取指定日期的数据
python3 pnl/fetch_historical_trades.py --date 2025-11-06

# 获取前5天的数据
python3 pnl/fetch_historical_trades.py --days 5

# 获取并显示摘要
python3 pnl/fetch_historical_trades.py --days 5 --show
```

#### 高级用法

```bash
# 指定交易对
python3 pnl/fetch_historical_trades.py --symbols BTCUSDT ETHUSDT

# 指定输出目录
python3 pnl/fetch_historical_trades.py --output my_trades

# 显示前20条记录
python3 pnl/fetch_historical_trades.py --show --limit 20
```

#### 命令参数

```bash
usage: fetch_historical_trades.py [-h] [--date DATE] [--days DAYS] 
                                   [--symbols SYMBOLS [SYMBOLS ...]] 
                                   [--output OUTPUT] [--show] [--limit LIMIT]

获取历史成交数据

optional arguments:
  -h, --help            显示帮助信息
  -d, --date DATE       指定日期 (格式: YYYY-MM-DD)，默认为今天
  -n, --days DAYS       往前追溯的天数，默认1天
  -s, --symbols SYMBOLS [SYMBOLS ...]
                        交易对列表，默认使用配置文件
  -o, --output OUTPUT   输出目录 (默认: pnl/historical_trades)
  --show                显示交易记录摘要
  -l, --limit LIMIT     显示的记录数量 (默认: 10)
```

#### 输出文件格式

文件保存在 `pnl/historical_trades/` 目录，格式为 `YYYYMMDD_trades.json`：

```json
{
  "date": "2025-11-06",
  "fetch_time": "2025-11-06T21:16:09.031012",
  "total_trades": 180,
  "symbols": ["BTCUSDT", "ETHUSDT", ...],
  "trades": [
    {
      "symbol": "BNBUSDT",
      "id": 70172155,
      "orderId": 878208798,
      "side": "BUY",
      "price": "945.350",
      ...
    }
  ]
}
```

**注意：** 此工具保存的是纯交易数据，不包含PnL统计快照。

## 数据更新机制

### 自动更新

1. **周期快照**：每个交易周期都会自动记录
2. **交易统计快照**：每次执行交易（非HOLD）后自动记录
3. **历史成交记录**：每10个交易周期自动更新一次

### 更新频率

- 周期快照：实时更新（每个周期）
- 交易统计快照：执行交易时更新
- 历史成交记录：每10个周期更新（可在 `main.py` 中调整）

## 示例输出

### 基础摘要

```
================================================================================
📅 日期: 2025-11-06
================================================================================

💰 账户变化:
  起始权益: $4,801.76
  结束权益: $4,653.77
  权益变化: $-147.99 (-3.08%)

📊 交易统计:
  已实现盈亏: +$125.63
  未实现盈亏: $-1.42
  累计手续费: $163.81
  净盈亏: $-38.18
  总盈亏: $-39.61

📈 操作统计:
  交易次数: 129
  周期数: 118
  开仓次数: 41
  平仓次数: 38
  最后更新: 2025-11-06T20:17:23.822780
```

### 交易统计快照

```
📸 交易统计快照 (共 10 条，显示最近 10 条):
--------------------------------------------------------------------------------

⏰ 2025-11-06T12:34:56 (周期 #1)
  已实现盈亏: +$125.63
  手续费: $163.81
  净盈亏: $-38.18
  交易次数: 129
  总盈亏: $-39.61
```

### 快照变化对比

```
📈 交易快照变化趋势:
--------------------------------------------------------------------------------
  首次快照: 2025-11-06T00:04:15 (周期 #1)
  最新快照: 2025-11-06T20:17:23 (周期 #118)
  周期跨度: 117 个周期

  变化:
    已实现盈亏: +$125.63
    累计手续费: $163.81
    净盈亏: $-38.18
    交易增加: 129 笔

  平均每笔交易:
    净盈亏: $-0.30
    手续费: $1.27
```

### 历史成交记录

```
📋 历史成交记录 (共 129 条，显示最近 20 条):
--------------------------------------------------------------------------------------------------------------
时间                 交易对       方向   价格         数量         手续费       已实现盈亏
--------------------------------------------------------------------------------------------------------------
2025-11-06 20:17:23  BNBUSDT      卖出   $952.02      0.950000     $0.361768    $-4.57
2025-11-06 20:15:10  BNBUSDT      买入   $950.50      0.950000     $0.360191    $0.00
...
```

## 技术实现

### 核心模块

- `src/daily_pnl_tracker.py`: 主要的追踪逻辑
- `pnl/pnl_viewer.py`: 数据查看工具
- `src/main.py`: 集成到主交易循环

### 关键方法

1. `record_cycle()`: 记录每个交易周期的数据
2. `_record_trade_snapshot()`: 记录交易统计快照
3. `update_historical_trades()`: 更新历史成交记录
4. `get_today_summary()`: 获取当日摘要
5. `get_history()`: 获取历史N天的数据
6. `get_today_trades()`: 获取当日成交记录

## 注意事项

1. 历史成交记录较大时会增加文件大小，建议定期归档
2. 每10个周期更新一次历史记录是为了平衡实时性和API调用频率
3. 所有金额单位为USDT
4. 时间戳为ISO 8601格式
5. 快照按时间顺序保存，最新的在列表末尾

## 故障排除

### 数据文件不存在

如果提示文件不存在，确认：
1. 日期格式正确（YYYYMMDD）
2. 系统在该日期有运行记录
3. `pnl/` 目录权限正常

### 交易统计快照为空

这是正常现象，如果：
1. 系统在该日期没有执行交易（全是HOLD）
2. 使用的是旧版本数据文件（升级前）

### 历史成交记录为空

这是正常现象，如果：
1. 还没有到达更新周期（每10个周期）
2. 执行适配器未正确配置
3. Binance API调用失败

解决方法：
- 等待下一个更新周期
- 检查执行适配器配置
- 查看日志中的错误信息
