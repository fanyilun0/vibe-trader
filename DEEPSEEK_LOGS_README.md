# DeepSeek 日志保存功能说明

## 📋 功能概述

为了方便审查和调试 DeepSeek AI 的交易决策过程，系统现在会自动将每次 API 调用的提示词和响应保存到本地文件。

## 📁 日志目录结构

所有日志文件保存在 `deepseek_logs/` 目录下：

```
deepseek_logs/
├── prompt_20251023_140530.txt      # 提示词 (发送给 DeepSeek 的市场数据)
├── response_20251023_140530.txt    # 响应 (DeepSeek 的完整分析)
├── signal_20251023_140530.json     # 交易信号 (JSON 格式)
├── signal_20251023_140530.txt      # 交易信号 (可读格式)
├── error_20251023_140530.txt       # 错误日志 (如果出错)
└── ...
```

### 文件命名规则

所有文件使用时间戳命名：`{类型}_{YYYYMMDD_HHMMSS}.{扩展名}`

例如：`prompt_20251023_140530.txt` 表示 2025年10月23日 14:05:30 生成的提示词

## 📄 文件内容说明

### 1. Prompt 文件 (`prompt_*.txt`)

包含发送给 DeepSeek 的完整提示词，包括：

```
====================================================================================================
DeepSeek Prompt - 2025-10-23 14:05:30
====================================================================================================

It has been 5 minutes since you started trading.
The current time is 2025-10-23 14:05:30 and you've been invoked 2 times.

Below, we are providing you with a variety of state data, price data, and predictive signals...

ALL BTCUSDT DATA
current_price = 65000.00, current_ema20 = 64800.00, current_macd = 120.45...

[完整的市场数据和技术指标]

HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): 2.50%
Available Cash: $9750.00
...

TRADING INSTRUCTIONS
[交易规则和输出格式要求]
```

### 2. Response 文件 (`response_*.txt`)

包含 DeepSeek 的完整响应，包括：

```
====================================================================================================
DeepSeek Response - 2025-10-23 14:05:30
====================================================================================================

Response Metadata:
  Model: deepseek-reasoner
  ID: chatcmpl-xxxxx
  Tokens - Prompt: 2847, Completion: 456, Total: 3303

----------------------------------------------------------------------------------------------------

Response Content:

Let me analyze the current market conditions step by step...

1. Trend Analysis:
   - BTC is trading at $65,000, above the 20-period EMA ($64,800)
   - The price has broken through recent resistance...

[完整的分析过程]

{
  "action": "LONG",
  "symbol": "BTCUSDT",
  "reasoning": "...",
  ...
}
```

### 3. Signal JSON 文件 (`signal_*.json`)

解析后的结构化交易信号：

```json
{
  "action": "LONG",
  "symbol": "BTCUSDT",
  "reasoning": "Based on the analysis...",
  "entry_price": 65000.0,
  "stop_loss": 64200.0,
  "take_profit": 66500.0,
  "confidence": 0.82,
  "leverage": 5
}
```

### 4. Signal TXT 文件 (`signal_*.txt`)

美化格式的交易信号（方便阅读）：

```
====================================================================================================
Trading Signal - 2025-10-23 14:05:30
====================================================================================================

🎯 Action: LONG
💰 Symbol: BTCUSDT
📊 Confidence: 82.00%
⚡ Leverage: 5x

📈 Entry Price: $65000.00
🛑 Stop Loss: $64200.00
🎯 Take Profit: $66500.00

💡 Reasoning:
----------------------------------------------------------------------------------------------------
Based on the current market analysis, BTC is showing strong bullish momentum...
[详细的决策理由]
```

### 5. Error 文件 (`error_*.txt`)

如果 API 调用失败，错误信息会保存到此文件：

```
====================================================================================================
DeepSeek Error - 2025-10-23 14:05:30
====================================================================================================

Error: API rate limit exceeded. Please try again later.
```

## 🔧 使用方法

### 1. 默认启用

日志保存功能默认启用。当你运行交易机器人时，每次生成信号都会自动保存：

```bash
uv run main.py
```

### 2. 在代码中控制

你可以在创建 `SignalGenerator` 时控制是否保存日志：

```python
from signal_generator import SignalGenerator

# 启用日志保存（默认）
signal_gen = SignalGenerator(save_logs=True)

# 禁用日志保存
signal_gen = SignalGenerator(save_logs=False)
```

### 3. 测试日志功能

运行测试脚本来验证日志保存功能：

```bash
uv run test_deepseek_logs.py
```

## 📊 日志文件的用途

### 1. 审查交易决策

通过查看提示词和响应，你可以：
- 了解 AI 接收到了哪些市场数据
- 查看 AI 的分析思路和推理过程
- 验证交易信号的合理性

### 2. 调试和优化

日志文件帮助你：
- 发现提示词中的数据问题
- 分析 AI 的决策模式
- 优化提示词模板
- 改进交易策略

### 3. 回测和分析

保存的历史日志可用于：
- 回顾历史决策
- 分析成功/失败的交易
- 改进 AI 提示词
- 训练和优化模型

### 4. 合规和审计

在监管环境中：
- 提供完整的决策记录
- 追溯每个交易的依据
- 满足审计要求

## 🔍 查看日志示例

### 查看最新的提示词

```bash
# macOS/Linux
ls -lt deepseek_logs/prompt_*.txt | head -1 | xargs cat

# Windows
dir /o-d deepseek_logs\prompt_*.txt | select -first 1 | Get-Content
```

### 查看最新的信号

```bash
# macOS/Linux
ls -lt deepseek_logs/signal_*.txt | head -1 | xargs cat

# 或使用 jq 查看 JSON
ls -lt deepseek_logs/signal_*.json | head -1 | xargs cat | jq .
```

### 统计日志文件

```bash
# 查看总共生成了多少次信号
ls deepseek_logs/signal_*.json | wc -l

# 查看最近的 5 个信号
ls -lt deepseek_logs/signal_*.txt | head -5
```

## 📏 日志管理

### 自动清理

日志文件会随时间累积。你可以定期清理旧日志：

```bash
# 删除 7 天前的日志
find deepseek_logs/ -name "*.txt" -mtime +7 -delete
find deepseek_logs/ -name "*.json" -mtime +7 -delete

# 只保留最新的 100 个文件
ls -t deepseek_logs/* | tail -n +101 | xargs rm
```

### 备份日志

建议定期备份重要的日志：

```bash
# 创建日期归档
tar -czf deepseek_logs_backup_$(date +%Y%m%d).tar.gz deepseek_logs/

# 移动到备份目录
mv deepseek_logs_backup_*.tar.gz ~/backups/
```

### 日志大小估算

每次 API 调用大约产生：
- Prompt: ~10-50 KB
- Response: ~5-20 KB
- Signal JSON: ~1 KB
- Signal TXT: ~2 KB
- **总计**: ~20-75 KB/次

如果每 5 分钟生成一次信号：
- 每天: ~288 次 × 50 KB = ~14 MB
- 每月: ~30 天 × 14 MB = ~420 MB

## ⚙️ 配置选项

在 `signal_generator.py` 中，你可以自定义：

```python
class SignalGenerator:
    def __init__(self, save_logs: bool = True):
        self.save_logs = save_logs
        
        if self.save_logs:
            # 自定义日志目录
            self.logs_dir = Path("deepseek_logs")  # 可修改为其他路径
            self.logs_dir.mkdir(exist_ok=True)
```

## 🔒 隐私和安全

### 重要提示

1. **不要提交日志到 Git**
   - `deepseek_logs/` 已添加到 `.gitignore`
   - 日志可能包含敏感的交易数据

2. **保护 API 密钥**
   - 响应文件不包含 API 密钥
   - 但仍需妥善保管日志文件

3. **数据脱敏**
   - 如需分享日志，请先移除敏感信息
   - 可以使用工具脱敏账户余额等数据

## 📚 相关文档

- [signal_generator.py](./signal_generator.py) - 信号生成器源代码
- [test_deepseek_logs.py](./test_deepseek_logs.py) - 日志功能测试脚本
- [QUICKSTART_CN.md](./QUICKSTART_CN.md) - 快速开始指南

## ❓ 常见问题

### Q1: 日志文件占用太多空间怎么办？

**A**: 可以：
1. 定期清理旧日志（见上文"自动清理"）
2. 压缩历史日志文件
3. 只在必要时启用日志：`SignalGenerator(save_logs=False)`

### Q2: 如何禁用日志保存？

**A**: 在创建 SignalGenerator 时传入 `save_logs=False`：
```python
signal_gen = SignalGenerator(save_logs=False)
```

### Q3: 日志保存失败怎么办？

**A**: 检查：
1. 是否有写入权限
2. 磁盘空间是否充足
3. 日志目录是否存在且可访问
4. 错误信息会打印到控制台

### Q4: 可以修改日志保存位置吗？

**A**: 可以，在 `signal_generator.py` 中修改：
```python
self.logs_dir = Path("your/custom/path")
```

### Q5: 日志文件编码是什么？

**A**: 所有日志文件使用 UTF-8 编码，支持中文和特殊字符。

## 🎯 最佳实践

1. **定期审查日志**
   - 每周查看一次交易信号的合理性
   - 分析 AI 的决策模式

2. **保留关键日志**
   - 重要交易的日志单独备份
   - 成功/失败案例作为学习材料

3. **优化提示词**
   - 根据日志反馈改进 prompt
   - 调整市场数据的呈现方式

4. **监控日志质量**
   - 检查是否有解析错误
   - 确认数据完整性

## ✅ 总结

DeepSeek 日志保存功能提供了：
- ✅ 自动保存提示词和响应
- ✅ 结构化的交易信号记录
- ✅ 详细的错误日志
- ✅ 易于阅读的文本格式
- ✅ 可编程的 JSON 格式
- ✅ 完整的审计追踪

这些日志是优化交易策略和理解 AI 决策的宝贵资源！

