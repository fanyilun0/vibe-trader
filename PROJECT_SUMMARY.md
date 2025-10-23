# Vibe Trader - 项目总结

## 📋 项目概述

**Vibe Trader** 是一个基于大语言模型（LLM）的自动化加密货币永续合约交易机器人，结合了 DeepSeek 的推理能力和 Aster DEX 的交易执行能力。

### 核心特性

- 🧠 **AI 驱动**: 使用 DeepSeek-Reasoner 进行市场分析和决策
- 📊 **全面的技术分析**: 15+ 种技术指标（RSI, MACD, EMA, Bollinger Bands 等）
- 🛡️ **多层风险管理**: 仓位控制、回撤保护、强制止损
- 🔄 **模块化架构**: 清晰分离数据、信号、执行和风险管理
- 📝 **纸上交易**: 先模拟测试，后真实交易
- ⚡ **自动化执行**: 24/7 监控市场和管理仓位

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         Vibe Trader                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│     Data     │      │    Signal    │     │     Risk     │
│  Aggregator  │─────▶│  Generator   │────▶│   Manager    │
│              │      │  (DeepSeek)  │     │              │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        │                     ▼                     │
        │             ┌──────────────┐              │
        │             │  Execution   │              │
        │             │    Engine    │              │
        │             └──────────────┘              │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                      ┌──────────────┐
                      │  Aster DEX   │
                      │     API      │
                      └──────────────┘
```

### 模块说明

#### 1. **Data Aggregator** (数据聚合器)
- **文件**: `data_aggregator.py`
- **职责**: 
  - 从 Aster DEX 获取市场数据（K线、订单簿、资金费率）
  - 计算技术指标
  - 获取账户和仓位信息
  - 构建结构化数据供 LLM 分析

#### 2. **Signal Generator** (信号生成核心)
- **文件**: `signal_generator.py`
- **职责**:
  - 使用 DeepSeek LLM 分析市场数据
  - 生成交易信号（LONG/SHORT/HOLD/CLOSE）
  - 提供详细的推理过程
  - 输出结构化的交易参数（入场、止损、止盈）

#### 3. **Execution Engine** (执行引擎)
- **文件**: `execution_engine.py`
- **职责**:
  - 执行交易信号（纸上或真实）
  - 计算仓位大小
  - 管理订单生命周期
  - 设置止损和止盈订单

#### 4. **Risk Manager** (风险管理器)
- **文件**: `risk_manager.py`
- **职责**:
  - 验证交易信号（置信度、盈亏比）
  - 监控账户回撤
  - 检测清算风险
  - 紧急平仓保护

#### 5. **Aster Client** (API 客户端)
- **文件**: `aster_client.py`
- **职责**:
  - 封装所有 Aster DEX API 调用
  - 处理请求签名和认证
  - 提供统一的 API 接口

#### 6. **Technical Indicators** (技术指标)
- **文件**: `indicators.py`
- **职责**:
  - 计算各种技术指标
  - 解析 K 线数据
  - 提供指标计算工具

## 📁 项目结构

```
vibe-trader/
├── config.py              # 配置管理（环境变量、参数）
├── main.py                # 主程序入口
├── aster_client.py        # Aster DEX API 客户端
├── data_aggregator.py     # 数据聚合器
├── signal_generator.py    # DeepSeek 信号生成
├── execution_engine.py    # 交易执行引擎
├── risk_manager.py        # 风险管理模块
├── indicators.py          # 技术指标计算
├── example.py             # 使用示例
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量模板
├── README.md              # 项目介绍
├── QUICKSTART.md          # 快速入门
├── PROJECT_SUMMARY.md     # 本文件
│
├── docs/
│   ├── USAGE.md           # 详细使用指南
│   ├── DATA_TEMPLATE.md   # 数据结构文档
│   └── aster-api.md       # Aster API 参考
│
└── template.md            # LLM 提示词模板
└── template-description.md # 模板说明
```

## 🔄 数据流程

### 完整执行周期

```
1. 启动 → 验证配置 → 初始化模块
                ↓
2. ┌─────── 主循环开始 ───────┐
   │                          │
   ├─ 获取市场数据            │
   │  • K 线数据              │
   │  • 技术指标              │
   │  • 账户信息              │
   │                          │
   ├─ 生成交易信号            │
   │  • 构建提示词            │
   │  • 调用 DeepSeek         │
   │  • 解析 JSON 响应        │
   │                          │
   ├─ 风险管理检查            │
   │  • 置信度验证            │
   │  • 盈亏比检查            │
   │  • 回撤检查              │
   │                          │
   ├─ 执行交易                │
   │  • 计算仓位大小          │
   │  • 下单（或模拟）        │
   │  • 设置止损/止盈         │
   │                          │
   ├─ 监控仓位                │
   │  • 检查清算风险          │
   │  • 更新账户状态          │
   │  • 紧急平仓保护          │
   │                          │
   └─ 等待 → 下一轮 ──────────┘
```

## 🎯 DeepSeek 提示词策略

### 提示词结构

机器人使用高度结构化的提示词，包含：

1. **角色定义**: "你是一个专业的量化分析师..."
2. **数据提供**: 
   - 当前市场状态（价格、指标、资金费率）
   - 历史序列数据（100+ 根 K 线）
   - 账户和仓位信息
3. **分析框架**:
   - 趋势分析（EMA 交叉、价格位置）
   - 动量分析（RSI、MACD）
   - 波动率分析（ATR、布林带）
   - 成交量分析（VWAP）
4. **风险规则**: 明确的仓位限制、止损要求
5. **输出格式**: 强制 JSON 输出

### 关键创新

- **Chain-of-Thought**: 要求 LLM 逐步推理
- **强制止损**: 拒绝没有止损的信号
- **置信度评分**: LLM 自评信号质量
- **盈亏比要求**: 最小 1.5:1

## 🛡️ 风险管理体系

### 五层防护

1. **信号级别**: LLM 生成止损和置信度
2. **验证级别**: Risk Manager 检查信号质量
3. **仓位级别**: 基于 ATR 的动态仓位计算
4. **账户级别**: 最大回撤自动平仓
5. **监控级别**: 实时清算风险检测

### 关键参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MAX_POSITION_SIZE_PERCENT` | 2.0% | 单笔最大仓位 |
| `RISK_PER_TRADE_PERCENT` | 1.0% | 单笔最大风险 |
| `MAX_DRAWDOWN_PERCENT` | 10.0% | 触发紧急平仓的回撤 |
| `MIN_CONFIDENCE` | 0.7 | 最低置信度要求 |
| `MIN_REWARD_RISK_RATIO` | 1.5 | 最小盈亏比 |

## 📊 支持的技术指标

| 指标 | 周期 | 用途 |
|------|------|------|
| EMA | 20, 50 | 趋势识别 |
| RSI | 7, 14 | 超买超卖 |
| MACD | 12, 26, 9 | 趋势动量 |
| Bollinger Bands | 20, 2σ | 波动区间 |
| ATR | 3, 14 | 波动率测量 |
| VWAP | - | 成交量加权 |
| ADX | 14 | 趋势强度 |

## 🔧 配置系统

### 环境变量

所有配置通过 `.env` 文件管理：

```bash
# API 凭证
DEEPSEEK_API_KEY=sk-xxx
ASTER_API_KEY=xxx
ASTER_API_SECRET=xxx

# 交易设置
TRADING_SYMBOLS=BTC-PERP,ETH-PERP,SOL-PERP
DEFAULT_LEVERAGE=5
MAX_LEVERAGE=10

# 风险控制
MAX_POSITION_SIZE_PERCENT=2.0
MAX_DRAWDOWN_PERCENT=10.0
RISK_PER_TRADE_PERCENT=1.0

# 运行模式
PAPER_TRADING_MODE=true
LOOP_INTERVAL_SECONDS=300
```

### 配置验证

`config.py` 在启动时验证必需的配置项，缺失则报错退出。

## 🧪 测试和验证

### 纸上交易模式

- 获取真实市场数据
- 调用真实的 DeepSeek API
- 模拟交易执行
- 记录所有交易决策
- 不消耗真实资金

### 示例脚本

`example.py` 提供 4 个独立示例：
1. Aster API 客户端使用
2. 技术指标计算
3. 数据聚合器测试
4. DeepSeek 信号生成测试

## 📈 性能考虑

### API 成本估算

**DeepSeek API**:
- 模型: `deepseek-reasoner`
- 每次调用: ~3000-5000 tokens
- 5 分钟间隔: 每天 ~288 次
- 日成本: 约 $2-4

**Aster API**:
- 公开端点: 免费
- 私有端点: 免费（仅需认证）
- 交易手续费: 见 Aster 费率

### 资源需求

- **CPU**: 低（主要是 API 调用）
- **内存**: < 200MB
- **网络**: 稳定连接即可
- **存储**: 最小（仅日志）

## 🚀 部署建议

### 云服务器

推荐使用云服务器 24/7 运行：

- **AWS EC2**: t2.micro (免费套餐)
- **Google Cloud**: e2-micro
- **DigitalOcean**: $6/月 Droplet
- **Vultr**: $5/月 VPS

### 容器化

可以创建 Docker 镜像以便部署：

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### 监控

建议设置：
- 日志收集（文件或云端）
- 崩溃重启（systemd/supervisor）
- 性能监控（Prometheus/Grafana）
- 告警通知（Telegram/Discord bot）

## 🔮 未来扩展方向

### 短期（1-3 个月）
- [ ] 数据库持久化（交易历史、性能指标）
- [ ] Web Dashboard（实时监控界面）
- [ ] Telegram Bot（远程控制和通知）
- [ ] 更多技术指标（Ichimoku、Fibonacci）
- [ ] 回测框架（模拟历史交易）

### 中期（3-6 个月）
- [ ] 多交易所支持（Hyperliquid、dYdX）
- [ ] 策略优化器（自动调参）
- [ ] 投资组合管理（多币种权重分配）
- [ ] 市场情绪分析（新闻、社交媒体）
- [ ] 高级止盈策略（追踪止盈、分批止盈）

### 长期（6-12 个月）
- [ ] 自定义策略 DSL（无代码策略编辑）
- [ ] 多 LLM 对比（Claude、GPT-4、Gemini）
- [ ] 强化学习优化（RL 模型微调）
- [ ] 去中心化部署（链上智能合约）
- [ ] 社区策略市场（分享和交易策略）

## 📚 学习资源

### 相关论文
- "Can Large Language Models Trade?" (arXiv 2024)
- "Sentiment-Aware Stock Price Prediction with LLM-Generated Alpha" (arXiv 2024)

### 参考项目
- **freqtrade**: 传统算法交易框架
- **LLM_trader**: LLM 驱动的交易机器人
- **Hyperliquid SDK**: 另一个永续合约 DEX

### 技术文档
- DeepSeek API Docs
- Aster DEX GitHub
- TA-Lib Documentation

## ⚖️ 法律和合规

- 本项目仅供教育和研究用途
- 用户需自行了解所在地区的交易法规
- 加密货币交易可能在某些司法管辖区受限
- 使用前请咨询专业的法律和财务建议

## 🤝 贡献指南

欢迎贡献！可以：
- 报告 Bug（GitHub Issues）
- 提出新功能（GitHub Discussions）
- 提交 Pull Request
- 改进文档

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 👥 作者和致谢

基于以下研究和项目开发：
- 学术论文："Architecting an LLM-Powered Agent for Automated Perpetuals Trading"
- DeepSeek Team (开源 MoE 模型)
- Aster DEX (提供 API)
- 开源社区的各种贡献

---

**免责声明**: 此软件按"原样"提供，不提供任何形式的保证。作者不对使用此软件产生的任何损失负责。加密货币交易涉及重大风险，请谨慎操作。

