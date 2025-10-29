# Vibe Trader 快速启动指南

⚡ 5分钟快速上手 Vibe Trader

## 🎯 最小化设置步骤

### 1. 安装依赖 (1分钟)

```bash
cd vibe-trader
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置 API 密钥 (2分钟)

创建 `.env` 文件:

```bash
cat > .env << 'EOF'
BINANCE_API_KEY=你的币安API密钥
BINANCE_API_SECRET=你的币安密钥
DEEPSEEK_API_KEY=你的DeepseekAPI密钥
EOF
```

**获取 API 密钥**:
- 币安: https://www.binance.com/en/my/settings/api-management
- Deepseek: https://platform.deepseek.com/api_keys

### 3. 运行测试 (1分钟)

```bash
# 运行单次测试
./run.sh --once

# 或
python3 -m src.main --once
```

### 4. 查看结果 (1分钟)

```bash
# 查看日志
cat logs/vibe_trader.log

# 查看状态
cat data/state.json
```

## ✅ 成功运行的标志

你应该看到:

```
✓ 币安数据摄取客户端初始化完成
✓ AI决策核心初始化完成
✓ 系统初始化完成!
✓ 开始新的交易周期
✓ [步骤 1/6] 数据摄取...
✓ [步骤 2/6] 数据处理与特征工程...
✓ [步骤 3/6] AI 决策生成...
✓ [步骤 4/6] 风险管理检查...
✓ 风险检查通过 或 决策被拒绝 (都是正常的)
✓ 交易周期完成
```

## 🚀 下一步

### 继续模拟交易

```bash
# 在后台持续运行
nohup python3 -m src.main > output.log 2>&1 &

# 或使用 screen
screen -S vibe-trader
python3 -m src.main
# Ctrl+A, D 退出但保持运行
```

### 监控运行

```bash
# 实时查看日志
tail -f logs/vibe_trader.log

# 查看决策历史
grep "AI 决策结果" logs/vibe_trader.log

# 查看账户表现
grep "账户价值" logs/vibe_trader.log
```

## ⚙️ 关键配置

在 `config.yaml` 中调整:

```yaml
execution:
  paper_trading: true  # ⚠️ 保持 true 进行模拟交易

risk_management:
  max_position_size_pct: 0.20  # 最大仓位 20%
  min_confidence: 0.75         # 最低置信度 75%
```

## 🐛 遇到问题?

### API 连接失败
```bash
# 检查环境变量
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('BINANCE_API_KEY')[:10])"
```

### 依赖问题
```bash
pip install --upgrade -r requirements.txt
```

### 查看完整日志
```bash
cat logs/vibe_trader.log | grep ERROR
```

## 📚 更多资源

- 📖 [完整 README](README.md)
- 🔧 [详细设置指南](docs/SETUP_GUIDE.md)
- 🏗️ [系统架构文档](docs/vibe-trader-arti.md)
- 💻 [示例代码](examples/example_usage.py)

## ⚠️ 重要提醒

1. **默认是模拟交易** - 不会真实下单
2. **从小资金开始** - 如果切换到实盘
3. **先充分测试** - 至少运行 1 周模拟交易
4. **监控系统** - 定期查看日志和决策质量

---

**准备好了吗? 开始你的 AI 交易之旅! 🚀**

```bash
./run.sh
```

