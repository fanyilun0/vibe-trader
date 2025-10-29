# Vibe Trader 详细设置指南

本指南将帮助你从零开始设置和运行 Vibe Trader 系统。

## 📋 前置要求

### 1. 系统要求
- **操作系统**: macOS, Linux, 或 Windows (推荐 WSL)
- **Python**: 3.9 或更高版本
- **网络**: 稳定的互联网连接

### 2. 账户要求
- **币安账户**: 用于获取市场数据和交易执行
  - 注册地址: https://www.binance.com
  - 需要完成身份验证 (KYC)
  
- **Deepseek API**: 用于 AI 决策
  - 注册地址: https://platform.deepseek.com
  - 需要充值获取 API 配额

## 🔧 详细安装步骤

### 步骤 1: 克隆仓库

```bash
# 克隆项目
cd ~/Desktop/github-repos
cd vibe-trader

# 查看项目结构
ls -la
```

### 步骤 2: 创建虚拟环境

强烈推荐使用虚拟环境来隔离项目依赖:

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows (PowerShell):
# venv\Scripts\Activate.ps1

# 验证虚拟环境
which python  # 应该显示 venv 目录下的 python
```

### 步骤 3: 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
pip list | grep binance
pip list | grep pandas
pip list | grep pydantic
```

### 步骤 4: 获取 API 密钥

#### 4.1 币安 API 密钥

1. 登录币安账户
2. 访问 https://www.binance.com/en/my/settings/api-management
3. 点击 "Create API"
4. 设置 API 密钥名称 (如 "Vibe Trader")
5. 完成安全验证 (2FA)
6. **重要**: 保存 `API Key` 和 `Secret Key`

**安全设置**:
- ✅ 启用 "Enable Reading" (读取权限)
- ✅ 启用 "Enable Futures" (期货交易,如果需要实盘交易)
- ⚠️ 根据需要启用 "Enable Spot & Margin Trading"
- ✅ 设置 IP 访问限制 (强烈推荐)
- ❌ **不要**启用 "Enable Withdrawals" (提现权限)

#### 4.2 Deepseek API 密钥

1. 访问 https://platform.deepseek.com
2. 注册/登录账户
3. 访问 API Keys 页面
4. 点击 "Create API Key"
5. 保存生成的 API 密钥

**充值**:
- Deepseek API 按使用量计费
- 建议初始充值 $10-20 用于测试
- 查看定价: https://platform.deepseek.com/pricing

### 步骤 5: 配置环境变量

创建 `.env` 文件:

```bash
# 在项目根目录创建 .env 文件
cat > .env << 'EOF'
# 币安 API 密钥
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_secret_key_here

# Deepseek API 密钥
DEEPSEEK_API_KEY=your_actual_deepseek_key_here
EOF
```

⚠️ **安全提醒**:
- 用实际的 API 密钥替换 `your_actual_*_here`
- 确保 `.env` 文件已在 `.gitignore` 中 (已配置)
- **永远不要**将 `.env` 提交到 Git
- **永远不要**在代码中硬编码 API 密钥

验证环境变量:

```bash
# 测试加载环境变量
python3 << 'EOF'
from dotenv import load_dotenv
import os

load_dotenv()

binance_key = os.getenv('BINANCE_API_KEY')
deepseek_key = os.getenv('DEEPSEEK_API_KEY')

print(f"Binance API Key: {binance_key[:10]}..." if binance_key else "❌ 未设置")
print(f"Deepseek API Key: {deepseek_key[:10]}..." if deepseek_key else "❌ 未设置")
EOF
```

### 步骤 6: 配置交易参数

编辑 `config.yaml` 文件:

```yaml
# 关键配置项说明

trading:
  symbols:
    - BTCUSDT          # 交易对,目前仅支持单个
  schedule_interval: 180  # 调度间隔(秒),建议 180-300

execution:
  platform: binance   # 交易平台
  paper_trading: true # ⚠️ 建议先设为 true 进行模拟交易

risk_management:
  max_position_size_pct: 0.20  # 单笔最大仓位 20%
  max_open_positions: 3        # 最大同时持仓数
  min_confidence: 0.75         # AI 最低置信度阈值
  allowed_symbols:
    - BTCUSDT
    - ETHUSDT  # 可添加其他允许交易的币种
```

**配置建议**:
- 初学者: `max_position_size_pct: 0.10`, `min_confidence: 0.80`
- 谨慎型: `max_position_size_pct: 0.15`, `min_confidence: 0.75`
- 激进型: `max_position_size_pct: 0.25`, `min_confidence: 0.70`

### 步骤 7: 测试各模块

在正式运行前,建议分别测试各个模块:

```bash
# 运行示例脚本
python3 examples/example_usage.py

# 选择测试项:
# 1. 数据摄取 - 测试币安 API 连接
# 2. 数据处理 - 测试技术指标计算
# 3. AI 决策 - 测试 Deepseek API
# 4. 风险管理 - 测试风险检查逻辑
# 5. 模拟交易 - 测试订单执行
```

### 步骤 8: 首次运行

#### 8.1 单次测试运行

```bash
# 仅运行一个周期,适合测试
python3 -m src.main --once

# 或使用快速脚本
./run.sh --once
```

检查输出:
- ✅ 所有模块初始化成功
- ✅ 数据成功获取
- ✅ AI 决策生成
- ✅ 风险检查通过/拒绝
- ✅ 状态保存成功

#### 8.2 查看日志

```bash
# 查看完整日志
cat logs/vibe_trader.log

# 实时监控日志
tail -f logs/vibe_trader.log

# 搜索错误
grep ERROR logs/vibe_trader.log
```

#### 8.3 检查状态文件

```bash
# 查看系统状态
cat data/state.json

# 应该包含:
# - start_time: 启动时间
# - invocation_count: 调用次数
# - start_balance: 起始余额
# - performance_history: 性能历史
```

## 🚀 正式运行

### 模拟交易模式 (推荐首先运行)

```bash
# 确保 config.yaml 中 paper_trading: true
python3 -m src.main

# 让系统运行至少 24 小时
# 观察决策质量和系统稳定性
```

**观察指标**:
- 决策合理性
- 风险管理是否有效
- 系统是否稳定运行
- 日志中是否有异常

### 实盘交易 (谨慎!)

⚠️ **在切换到实盘前,请确保**:
- ✅ 已在模拟模式下运行至少 1 周
- ✅ 对系统行为有充分了解
- ✅ 已仔细审查所有风险参数
- ✅ 从小资金开始 (如 $100-500)
- ✅ 设置了合理的止损

修改配置:

```yaml
execution:
  platform: binance
  paper_trading: false  # 切换到实盘

risk_management:
  max_position_size_pct: 0.10  # 降低仓位
  min_confidence: 0.80          # 提高置信度要求
```

启动:

```bash
# 实盘运行
python3 -m src.main

# 建议在 screen 或 tmux 中运行以保持后台运行
screen -S vibe-trader
python3 -m src.main
# Ctrl+A, D 退出 screen (保持运行)
# screen -r vibe-trader  # 重新连接
```

## 📊 监控与维护

### 日常监控

```bash
# 查看最近的决策
tail -100 logs/vibe_trader.log | grep "决策"

# 查看账户表现
tail -100 logs/vibe_trader.log | grep "账户价值"

# 查看风险事件
grep "风险检查失败" logs/vibe_trader.log
```

### 定期检查

- **每天**: 查看日志,确认系统正常运行
- **每周**: 审查性能指标,调整风险参数
- **每月**: 评估策略有效性,考虑优化

### 日志管理

```bash
# 日志会自动轮转 (根据 config.yaml 配置)
# 手动清理旧日志
find logs/ -name "*.log.*" -mtime +30 -delete
```

### 备份

```bash
# 备份重要文件
tar -czf backup_$(date +%Y%m%d).tar.gz \
  config.yaml \
  data/state.json \
  logs/vibe_trader.log

# 定期备份到云端或其他位置
```

## 🐛 常见问题

### 问题 1: 币安 API 连接失败

```
BinanceAPIException: Invalid API-key, IP, or permissions
```

**解决方案**:
1. 检查 API 密钥是否正确
2. 确认 API 密钥已启用期货交易权限
3. 如设置了 IP 白名单,添加当前 IP
4. 检查网络连接

### 问题 2: Deepseek API 配额不足

```
OpenAI API error: Insufficient quota
```

**解决方案**:
1. 访问 https://platform.deepseek.com 充值
2. 检查 API 密钥是否正确
3. 查看使用量统计

### 问题 3: 技术指标计算错误

```
ValueError: 缺少必需字段
```

**解决方案**:
1. 增加 K 线数据获取数量 (config.yaml 中的 limit)
2. 检查网络是否稳定
3. 查看币安 API 是否返回完整数据

### 问题 4: 所有决策都被风险管理器拒绝

**解决方案**:
1. 检查 `min_confidence` 是否设置过高
2. 确认 `allowed_symbols` 包含正在交易的币种
3. 查看具体拒绝原因 (日志中有详细说明)

## 🔒 安全最佳实践

1. **API 密钥安全**
   - 定期更换 API 密钥
   - 设置 IP 白名单
   - 使用专用 API 密钥,不与其他应用共享
   - 不要授予提现权限

2. **风险控制**
   - 从小资金开始
   - 设置合理的止损
   - 定期监控系统
   - 准备好手动干预

3. **系统安全**
   - 保持系统和依赖包更新
   - 使用防火墙保护服务器
   - 定期备份数据
   - 审查系统日志

## 📚 进一步学习

- [系统架构文档](vibe-trader-arti.md)
- [提示词模板说明](template-description.md)
- [币安 API 文档](https://www.binance.com/en/binance-api)
- [Deepseek API 文档](https://api-docs.deepseek.com/zh-cn/)

## 💡 优化建议

1. **提示词优化**
   - 根据市场情况调整提示词
   - 添加更多市场背景信息
   - 优化决策指令的清晰度

2. **风险参数调整**
   - 根据回测结果调整仓位大小
   - 动态调整置信度阈值
   - 考虑市场波动率

3. **技术指标**
   - 实验不同的指标参数
   - 添加新的技术指标
   - 结合多时间框架分析

---

**祝你交易顺利! 🚀**

如有问题,请查看日志文件或提交 Issue。

