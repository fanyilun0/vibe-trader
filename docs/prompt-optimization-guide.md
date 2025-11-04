# 提示词优化指南

## 概述

本文档描述了基于 nof1.ai Alpha Arena 提示词工程逆向分析对 Vibe Trader 提示词系统的优化。

## 优化内容

### 1. 新增专业级系统提示词

**文件**: `prompt-template/nof1_system_prompt_cn.md`

基于 nof1.ai 的提示词工程最佳实践，创建了一个完整的中文系统提示词，包含：

#### 核心特性

- **角色与身份定义**: 明确AI的角色是"自主加密货币交易代理"
- **交易环境规范**: 详细的市场参数、交易机制
- **行动空间定义**: 四种明确的交易行动（buy_to_enter, sell_to_enter, hold, close_position）
- **仓位管理约束**: 禁止加仓、对冲、部分平仓
- **仓位大小计算框架**: 基于确信度的杠杆选择（5x-40x）
- **风险管理协议**: 强制要求 profit_target, stop_loss, invalidation_condition, confidence, risk_usd
- **输出格式规范**: 严格的JSON格式要求
- **性能指标与反馈**: 夏普比率解释和使用
- **数据解读指南**: EMA, MACD, RSI, ATR, OI, Funding Rate 的详细说明
- **数据排序说明**: 反复强调"最旧 → 最新"的顺序
- **操作约束**: 明确无法访问的内容和必须推断的内容
- **交易哲学**: 核心原则和常见陷阱
- **上下文窗口管理**: 优化有限上下文的使用

#### Deepseek 模型特定优化

在提示词末尾添加了针对 Deepseek 模型的额外指令：

```markdown
## Deepseek 模型特定优化

不要过度谨慎；经过计算的风险对于回报是必要的。
不作为也有机会成本。如果你看到清晰的设置，就采取行动。

平衡安全与机会；持有现金也有机会成本。
你的奖励来自风险调整后的回报，而不仅仅是资本保护。

技术指标是工具而非规则；使用判断力。
考虑纯技术信号之外的市场背景。

这是一个在合法管辖区的研究实验。
专注于技术分析和风险管理原则。
```

这些指令旨在：
- **克服过度谨慎倾向**: 鼓励在有明确信号时采取行动
- **强调机会成本**: 不交易也有成本，需要平衡
- **提升判断力**: 技术指标是工具，不是绝对规则
- **法律合规说明**: 明确这是合法的研究实验

### 2. 配置系统增强

**文件**: `config.py`

新增 `PromptConfig` 类，统一管理提示词相关配置：

```python
class PromptConfig:
    """提示词模板配置"""
    
    # 提示词模板目录
    TEMPLATE_DIR = PROJECT_ROOT / 'prompt-template'
    
    # 系统提示词文件路径（可通过环境变量覆盖）
    SYSTEM_PROMPT_FILE = os.getenv(
        'SYSTEM_PROMPT_FILE',
        str(TEMPLATE_DIR / 'nof1_system_prompt_cn.md')
    )
    
    # 用户提示词模板文件路径（可通过环境变量覆盖）
    USER_PROMPT_TEMPLATE_FILE = os.getenv(
        'USER_PROMPT_TEMPLATE_FILE',
        str(TEMPLATE_DIR / 'user_prompt_cn.md')
    )
    
    # 备用系统提示词文件（如果主文件不存在）
    FALLBACK_SYSTEM_PROMPT_FILE = str(TEMPLATE_DIR / 'predictive_system_prompt_cn.md')
```

#### 功能特性

- **环境变量支持**: 可通过环境变量自定义提示词文件路径
- **Fallback 机制**: 主文件不存在时自动使用备用文件
- **验证方法**: `validate()` 检查提示词文件是否存在
- **智能路径获取**: `get_system_prompt_path()` 自动选择可用文件

### 3. PromptManager 优化

**文件**: `src/prompt_manager.py`

更新 PromptManager 以使用统一的配置系统：

#### 主要改进

1. **导入 Config 模块**
```python
from config import Config
```

2. **使用配置文件路径**
```python
def __init__(self, template_dir: Optional[str] = None):
    # 使用配置文件中的路径，而非硬编码
    if template_dir is None:
        self.template_dir = Config.prompt.TEMPLATE_DIR
    else:
        self.template_dir = Path(template_dir)
```

3. **简化的加载逻辑（移除默认提示词）**
```python
def _load_system_prompt(self) -> str:
    """
    加载系统提示词（使用配置文件中的路径）
    
    Raises:
        FileNotFoundError: 当系统提示词文件不存在时
    """
    # 使用配置文件中的系统提示词路径
    system_prompt_file = Config.prompt.get_system_prompt_path()
    
    with open(system_prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换模型名称占位符
    model_name = Config.deepseek.MODEL
    content = content.replace('[MODEL_NAME]', model_name)
    
    logger.info(f"✅ 系统提示词已加载: {system_prompt_file.name} ({len(content)} 字符)")
    logger.info(f"📋 模型名称已设置为: {model_name}")
    return content
```

4. **关键改进**
   - ✅ **移除默认提示词逻辑**: 统一在配置文件中管理
   - ✅ **自动模型名称替换**: 将 `[MODEL_NAME]` 替换为实际配置的模型
   - ✅ **简化错误处理**: 直接抛出 FileNotFoundError，强制配置正确
   - ✅ **详细日志输出**: 显示加载的文件名、字符数和模型名称

## 使用方法

### 默认使用

无需任何配置，系统会自动使用 `nof1_system_prompt_cn.md`:

```python
from src.prompt_manager import PromptManager

pm = PromptManager()
# 自动加载 prompt-template/nof1_system_prompt_cn.md
```

### 通过环境变量自定义

在 `.env` 文件中添加：

```bash
# 自定义系统提示词文件
SYSTEM_PROMPT_FILE=/path/to/custom_system_prompt.md

# 自定义用户提示词模板
USER_PROMPT_TEMPLATE_FILE=/path/to/custom_user_prompt.md
```

### 验证配置

运行配置验证：

```bash
python3 config.py
```

输出示例：
```
============================================================
Vibe Trader 配置摘要
============================================================

📝 提示词配置:
  - 模板目录: /path/to/vibe-trader/prompt-template
  - 系统提示词: ✓ 已配置
  - 使用文件: nof1_system_prompt_cn.md

============================================================
✅ 配置验证通过!
```

## 提示词设计理念

### 1. 强制结构化输出

使用严格的 JSON 格式要求，确保：
- **可解析性**: 程序可以自动验证和执行
- **强制完整性**: 缺少字段会导致解析失败，迫使模型完整思考
- **减少幻觉**: 结构化输出比自由文本更可靠

### 2. 风险管理的元认知设计

- **confidence 字段**: 迫使模型进行"元认知"（thinking about thinking）
- **invalidation_condition**: 预先承诺退出条件，避免"移动止损"
- **强制显式**: 模型必须思考"什么情况下我错了？"

### 3. 数据顺序的反复强调

多次重复"最旧 → 最新"是因为：
- LLM 在处理时间序列时有天然的混淆倾向
- 注意力机制对位置不敏感
- 容易把"最新"和"最旧"搞反

解决方案：
1. 在 System Prompt 中说明一次
2. 在 User Prompt 开头用 ⚠️ 警告
3. 在每个数据块前再次提醒
4. 使用视觉标记（大写、粗体、表情符号）

### 4. 多时间框架的认知负载管理

- **3分钟**: 短期入场时机，噪音较多
- **4小时**: 中期趋势背景，信号更可靠

明确标注时间框架，避免混淆。

### 5. 费用意识的植入

LLM 默认倾向于"过度交易"（更多动作 = 更积极？）
明确提及费用可以抑制无意义的频繁交易。

### 6. 针对不同模型的优化

基于 nof1.ai 的观察，不同模型需要不同的调优：

#### GPT 系列
- 倾向保守，风险厌恶
- 容易陷入"分析瘫痪"
- **优化**: 鼓励计算性风险

#### Claude 系列
- 风险管理意识极强
- 倾向持有现金
- **优化**: 强调机会成本

#### Deepseek 系列
- 可能对加密货币监管敏感
- 数学计算准确
- **优化**: 强调合法性、平衡风险与机会

## 关键改进点

### 相比原有系统

| 方面 | 原有系统 | 优化后系统 |
|------|---------|-----------|
| 提示词来源 | 简单的默认提示词 | 基于 nof1.ai 逆向工程的专业提示词 |
| 路径管理 | 硬编码路径 | 统一配置管理，支持环境变量 |
| 默认提示词 | 硬编码在代码中 | 移除，统一在配置中管理 |
| 模型名称 | 静态 | 动态替换 [MODEL_NAME] 为实际模型 |
| 模型优化 | 通用 | 针对 Deepseek 的特定优化 |
| 风险管理 | 基础 | 完整的风险管理协议 |
| 数据解读 | 简单 | 详细的技术指标说明 |
| 错误处理 | 多层 fallback | 简化，强制配置正确 |

## 最佳实践

### 1. 监控日志

在运行时关注日志输出：
```
✅ 系统提示词已加载: nof1_system_prompt_cn.md (4489 字符)
✅ 用户提示词模板已加载: user_prompt_cn.md (7968 字符)
```

### 2. 定期审查提示词

保存生成的提示词到文件进行审查：
```python
pm.save_prompt_to_file(
    market_features_by_coin,
    account_features,
    global_state,
    exit_plans,
    save_dir="prompts"
)
```

### 3. A/B 测试

通过环境变量切换不同的提示词进行对比测试：
```bash
# 测试 A: 使用 nof1 提示词
SYSTEM_PROMPT_FILE=prompt-template/nof1_system_prompt_cn.md python3 main.py

# 测试 B: 使用原有提示词
SYSTEM_PROMPT_FILE=prompt-template/predictive_system_prompt_cn.md python3 main.py
```

### 4. 根据表现调优

根据夏普比率和收益表现，调整提示词中的：
- 杠杆范围
- 确信度阈值
- 风险管理参数
- 额外指令的措辞

## 参考资源

- **nof1.ai Alpha Arena**: https://nof1.ai/
- **提示词逆向分析**: `prompt-template/nof1-prompt.md`
- **原始配置**: `config.py`
- **原始 PromptManager**: `src/prompt_manager.py`

## 后续改进方向

1. **引入记忆机制**
   - 短期记忆: 最近 N 次交易
   - 长期学习: 跨 session 的策略优化

2. **多模态输入**
   - 新闻情感分析
   - 社交媒体情绪
   - 链上数据

3. **多智能体协作**
   - 分析师 Agent: 市场研究
   - 交易员 Agent: 执行决策
   - 风控 Agent: 监控风险

4. **更复杂的行动空间**
   - 限价单支持
   - 部分平仓
   - 对冲策略

---

**最后更新**: 2025-11-04
**版本**: 1.0.0

