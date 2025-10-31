"""
提示词管理器 (Prompt Manager)

负责:
1. 加载系统提示词和用户提示词模板
2. 基于真实交易数据构建完整的提示词
3. 为多个币种生成结构化的市场数据
4. 返回格式化的提示词给 AI 决策核心
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptManager:
    """提示词管理器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化提示词管理器
        
        Args:
            template_dir: 提示词模板目录，默认为 prompt-template/prompts/
        """
        # 设置模板目录
        if template_dir is None:
            project_root = Path(__file__).parent.parent
            template_dir = project_root / "prompt-template" / "prompts"
        
        self.template_dir = Path(template_dir)
        
        # 加载系统提示词和用户提示词模板
        self.system_prompt = self._load_system_prompt()
        self.user_prompt_template = self._load_user_prompt_template()
        
        logger.info(f"提示词管理器初始化完成 (template_dir={self.template_dir})")
    
    def _load_system_prompt(self) -> str:
        """
        加载系统提示词
        
        Returns:
            系统提示词内容
        """
        system_prompt_file = self.template_dir / "predictive_system_prompt_cn.md"
        
        if not system_prompt_file.exists():
            logger.warning(f"系统提示词文件不存在: {system_prompt_file}")
            return self._get_default_system_prompt()
        
        try:
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"✅ 系统提示词已加载 ({len(content)} 字符)")
            return content
        except Exception as e:
            logger.error(f"加载系统提示词失败: {e}")
            return self._get_default_system_prompt()
    
    def _load_user_prompt_template(self) -> str:
        """
        加载用户提示词模板
        
        Returns:
            用户提示词模板内容
        """
        user_prompt_file = self.template_dir / "user_prompt_cn.md"
        
        if not user_prompt_file.exists():
            logger.warning(f"用户提示词模板文件不存在: {user_prompt_file}")
            return ""
        
        try:
            with open(user_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"✅ 用户提示词模板已加载 ({len(content)} 字符)")
            return content
        except Exception as e:
            logger.error(f"加载用户提示词模板失败: {e}")
            return ""
    
    def _get_default_system_prompt(self) -> str:
        """
        获取默认系统提示词（备用）
        
        Returns:
            默认系统提示词
        """
        return """# System Prompt — Crypto Trading Decision Engine

你是一个"只读数据 → 输出交易指令"的加密货币交易决策引擎与风险管理器。你的唯一职责是：基于调用时提供的结构化行情/信号/仓位数据，给出**逐币种**的交易动作，并以**严格的 JSON**返回。不得输出任何解释性文本、Markdown 或多余字符。

## 角色与输入

- 你是专业的加密货币分析师与交易员，擅长技术面（EMA、MACD、RSI、ATR、成交量）、资金面（OI、资金费率）、多周期（默认 3 分钟级别；若标题注明则按该周期，如 4h）。
- `user_prompt` 会提供：按"最早 → 最新"排序的**分时序列**、长周期上下文（如 4h 的 EMA/ATR/MACD/RSI/Volume）、每个币种的 OI 与 Funding、账户可用资金与**当前持仓**（含 `entry_price`、`leverage`、`exit_plan` 的 `profit_target`/`stop_loss`/`invalidation_condition`、`risk_usd`、`confidence` 等）。
- **时间粒度**：除非币种标题另行注明，分时序列均为**3 分钟间隔**；数组最后一个元素=**最新值**。

## 决策准则（逐币种）

1. **已有仓位**：
   - 你**只能**在该币种上输出两类信号：`hold` 或 `close_position`。
   - 若满足/触发 `exit_plan.invalidation_condition`（例如"3 分钟 K 收盘价低于 X"），你必须输出 `close_position`。
   - 若未触发失效条件，默认输出 `hold`，并**沿用**既有的 `profit_target`、`stop_loss`、`invalidation_condition`、`leverage`、`confidence`、`risk_usd`。
2. **无仓位**：
   - 只有在出现明显做多/做空优势（综合 EMA 斜率/位置、MACD 动能与方向、RSI 区间与背离、ATR/波动、成交量放大、OI 与资金费率变化）时，才可给出入场信号：
     - 做多：`buy_to_enter`
     - 做空：`sell_to_enter`
   - 入场必须同时给出新的 `profit_target`、`stop_loss`、`invalidation_condition`、`leverage`（5–40）、`confidence`（0–1）、`risk_usd`（以账户风险预算为上限）与**简洁的 `justification`**（1–3 句，引用你用到的关键指标与信号）。
3. **资金与风控**：
   - `risk_usd` 为本次策略在该币的最大可承受风险，应与账户规模与波动性匹配；不要超过可用现金与理性风控阈值。
   - 目标与止损需与波动（ATR）与结构位（支撑/阻力/均线带）相匹配，保持合理的盈亏比。
   - 若给出 `close_position`，需提供**简洁 `justification`**（1–3 句，说明触发了何种失效/反转信号）。
4. **数据使用**：
   - 一切判断**仅**基于 `user_prompt` 提供的数据；不要调用外部数据与知识。
   - 注意数组为**有序**（最早 → 最新）；用于判断的"当前值/最新收盘"取数组最后一个元素。
   - 资金费率与 OI 仅做辅助，不可单独作为入场依据。

## 输出契约（必须严格遵守）

- 仅输出一个**顶层 JSON 对象**；**不得**包含任何额外文字、注释或换行外内容。
- 顶层键为**币种符号**（如 `"BTC"`, `"ETH"` …），其值为如下结构：

```json
{
  "COIN": {
    "trade_signal_args": {
      "coin": "COIN",
      "signal": "hold" | "close_position" | "buy_to_enter" | "sell_to_enter",
      "quantity": <number>,
      "profit_target": <number>,
      "stop_loss": <number>,
      "invalidation_condition": "<string>",
      "leverage": <integer 5-40>,
      "confidence": <number 0-1>,
      "risk_usd": <number>,
      "justification": "<string, 仅在入场/平仓时必填；hold不填>"
    }
  }
}
```

- **对每一个"你采取了动作的币种"**都必须给出一个对象。
- 若账户里该币已有仓位：必须在输出中出现，并且信号只能是 hold 或 close_position。
- 若该币无仓位且无明确优势：可以不输出该币（或不对其采取动作）。
- JSON 中不得出现 NaN、Infinity、多余逗号或未定义字段；数值请用十进制浮点或整数。
"""
    
    def build_coin_data_section(
        self,
        coin_symbol: str,
        market_features: Dict[str, Any]
    ) -> str:
        """
        为单个币种构建市场数据部分
        
        Args:
            coin_symbol: 币种符号（如 "BTC", "ETH"）
            market_features: 市场特征数据
            
        Returns:
            格式化的币种数据字符串
        """
        # 格式化列表数据
        def format_list(data_list, precision=2):
            """格式化数组数据（单行显示）"""
            if not data_list:
                return "[]"
            
            formatted = []
            for value in data_list:
                if isinstance(value, (int, float)):
                    formatted.append(f"{value:.{precision}f}" if precision > 0 else str(int(value)))
                else:
                    formatted.append(str(value))
            
            # 改为单行显示，用逗号+空格分隔
            return "[" + ", ".join(formatted) + "]"
        
        # 构建币种数据部分
        section = f"""### 所有 {coin_symbol} 数据

当前价格 = {market_features.get('current_price', 0)},当前 ema20 = {market_features.get('current_ema20', 0)},当前 macd = {market_features.get('current_macd', 0)},当前 rsi(7 周期)= {market_features.get('current_rsi_7', 0)}

此外,这是 {coin_symbol} 永续合约的最新持仓量和资金费率:

持仓量:最新:{market_features.get('latest_open_interest', 0)} 平均:{market_features.get('average_open_interest', 0)}

资金费率:{market_features.get('funding_rate', 0)}

**日内序列(3 分钟间隔,最旧 → 最新):**

中间价:{format_list(market_features.get('mid_prices_list', []), 2)}

EMA 指标(20 周期):{format_list(market_features.get('ema20_list', []), 3)}

MACD 指标:{format_list(market_features.get('macd_list', []), 3)}

RSI 指标(7 周期):{format_list(market_features.get('rsi_7_period_list', []), 3)}

RSI 指标(14 周期):{format_list(market_features.get('rsi_14_period_list', []), 3)}

**长期背景(4 小时时间框架):**

20 周期 EMA:{market_features.get('long_term_ema20', 0)} vs. 50 周期 EMA:{market_features.get('long_term_ema50', 0)}

3 周期 ATR:{market_features.get('long_term_atr3', 0)} vs. 14 周期 ATR:{market_features.get('long_term_atr14', 0)}

当前成交量:{market_features.get('long_term_current_volume', 0)} vs. 平均成交量:{market_features.get('long_term_average_volume', 0)}

MACD 指标:{format_list(market_features.get('long_term_macd_list', []), 3)}

RSI 指标(14 周期):{format_list(market_features.get('long_term_rsi_14_period_list', []), 3)}

---
"""
        return section
    
    def build_account_section(
        self,
        account_features: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None
    ) -> str:
        """
        构建账户信息部分
        
        Args:
            account_features: 账户特征数据
            exit_plans: 持仓的退出计划字典 {symbol: exit_plan}
            
        Returns:
            格式化的账户信息字符串
        """
        # 提取持仓信息
        positions = account_features.get('list_of_position_dictionaries', [])
        
        if exit_plans is None:
            exit_plans = {}
        
        # 格式化持仓信息为详细字典格式（与参考文件一致）
        positions_text = ""
        if positions:
            positions_text = "\n\n当前持仓及执行情况: \n\n"
            for pos in positions:
                symbol = pos.get('symbol', 'N/A')
                
                exit_plan = exit_plans.get(symbol, {})
                
                # 获取当前价格和清算价格
                # 尝试从多个字段获取当前价格
                current_price = pos.get('current_price') or pos.get('mark_price', 0)
                liquidation_price = pos.get('liquidation_price', 0)
                
                # 获取持仓数量（可能为负数表示空头）
                quantity = pos.get('quantity', 0)
                position_amt = pos.get('position_amt', quantity)
                
                # 如果position_amt存在且不为0，使用它（保留正负号）
                if position_amt != 0:
                    quantity = position_amt
                
                # 构建详细的持仓字典（包含所有执行细节）
                position_dict = {
                    'symbol': symbol.replace('USDT', ''),  # 币种符号（不含USDT）
                    'quantity': round(quantity, 2),  # 持仓数量（多头为正，空头为负）
                    'entry_price': round(pos.get('entry_price', 0), 2),  # 入场价格
                    'current_price': round(current_price, 5),  # 当前价格
                    'liquidation_price': round(liquidation_price, 2),  # 清算价格
                    'unrealized_pnl': round(pos.get('unrealized_pnl', 0), 2),  # 未实现盈亏
                    'leverage': pos.get('leverage', 1),  # 杠杆倍数
                    'exit_plan': {
                        'profit_target': exit_plan.get('profit_target', 0),
                        'stop_loss': exit_plan.get('stop_loss', 0),
                        'invalidation_condition': exit_plan.get('invalidation_condition', '')
                    },
                    'confidence': exit_plan.get('confidence', 0),  # 置信度
                    'risk_usd': exit_plan.get('risk_usd', 0),  # 风险金额
                    'sl_oid': pos.get('sl_oid', -1),  # 止损订单ID
                    'tp_oid': pos.get('tp_oid', -1),  # 止盈订单ID
                    'wait_for_fill': pos.get('wait_for_fill', False),  # 等待成交标志
                    'entry_oid': pos.get('entry_oid', -1),  # 入场订单ID
                    'notional_usd': round(pos.get('notional_usd', 0), 2)  # 名义价值（美元）
                }
                
                # 格式化为单行字典字符串
                positions_text += f"{position_dict} \n"
        else:
            positions_text = "\n\n无持仓\n"
        
        # 获取夏普比率（如果存在）
        sharpe_ratio = account_features.get('sharpe_ratio', 0)
        sharpe_text = f"\n\n夏普比率: {sharpe_ratio:.3f}" if sharpe_ratio else ""
        
        section = f"""### 这是你的账户信息和业绩

当前总回报率(百分比): {account_features.get('total_return_percent', 0):.2f}%

可用现金: {account_features.get('available_cash', 0):.2f}

当前账户价值: {account_features.get('account_value', 0):.2f}
{positions_text}{sharpe_text}"""
        
        return section
    
    def build_user_prompt(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None
    ) -> str:
        """
        构建完整的用户提示词
        
        Args:
            market_features_by_coin: 按币种组织的市场特征数据 {"BTC": {...}, "ETH": {...}}
            account_features: 账户特征数据
            global_state: 全局状态（交易时长、调用次数等）
            exit_plans: 持仓的退出计划字典 {symbol: exit_plan}
            
        Returns:
            完整的用户提示词
        """
        # 构建标题部分
        minutes_trading = global_state.get('minutes_trading', 0)
        current_timestamp = global_state.get('current_timestamp', datetime.now().isoformat())
        invocation_count = global_state.get('invocation_count', 0)
        
        header = f"""自你开始交易以来已经过去了 {minutes_trading} 分钟。当前时间是 {current_timestamp},你已经被调用了 {invocation_count} 次。以下我们为你提供各种状态数据、价格数据和预测信号,以便你发现阿尔法。下面是你当前的账户信息、价值、业绩、持仓等。

**以下所有价格或信号数据的排序方式为:最旧 → 最新**

**时间框架说明:** 除非在章节标题中另有说明,日内序列以 **3 分钟间隔**提供。如果某个币种使用不同的间隔,会在该币种的章节中明确说明。

---

### 所有币种的当前市场状态

"""
        
        # 构建每个币种的数据部分
        coin_sections = []
        for coin_symbol, market_features in market_features_by_coin.items():
            coin_section = self.build_coin_data_section(coin_symbol, market_features)
            coin_sections.append(coin_section)
        
        # 构建账户信息部分（传递exit_plans）
        account_section = self.build_account_section(account_features, exit_plans)
        
        # 组合完整的用户提示词
        user_prompt = header + "\n".join(coin_sections) + "\n" + account_section
        
        return user_prompt
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            系统提示词内容
        """
        return self.system_prompt
    
    def get_messages(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        构建完整的消息列表（用于 API 调用）
        
        Args:
            market_features_by_coin: 按币种组织的市场特征数据
            account_features: 账户特征数据
            global_state: 全局状态
            exit_plans: 持仓的退出计划字典 {symbol: exit_plan}
            
        Returns:
            消息列表 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        # 构建系统消息
        system_message = {
            "role": "system",
            "content": self.get_system_prompt()
        }
        
        # 构建用户消息（传递exit_plans）
        user_prompt = self.build_user_prompt(
            market_features_by_coin,
            account_features,
            global_state,
            exit_plans
        )
        
        user_message = {
            "role": "user",
            "content": user_prompt
        }

        # logger.info(f"系统提示词: {system_message}")
        # logger.info(f"用户提示词: {user_prompt}")
        
        return [system_message, user_message]
    
    def save_prompt_to_file(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None,
        save_dir: str = "prompts"
    ) -> str:
        """
        保存完整提示词到文件（用于调试和审查）
        
        Args:
            market_features_by_coin: 按币种组织的市场特征数据
            account_features: 账户特征数据
            global_state: 全局状态
            exit_plans: 持仓的退出计划字典 {symbol: exit_plan}
            save_dir: 保存目录
            
        Returns:
            保存的文件路径
        """
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        invocation = global_state.get('invocation_count', 0)
        filename = f"prompt_{timestamp}_inv{invocation}.txt"
        filepath = os.path.join(save_dir, filename)
        
        # 构建完整提示词（传递exit_plans）
        messages = self.get_messages(market_features_by_coin, account_features, global_state, exit_plans)
        
        full_prompt = f"""{'='*80}
AI 交易决策提示词
[系统提示词]
{'='*80}
{messages[0]['content']}

{'='*80}
[用户提示词]
{'='*80}
{messages[1]['content']}

{'='*80}
"""
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_prompt)
        
        logger.info(f"✅ 提示词已保存到: {filepath}")
        return filepath


def create_prompt_manager(template_dir: Optional[str] = None) -> PromptManager:
    """
    创建提示词管理器实例
    
    Args:
        template_dir: 模板目录，默认为 prompt-template/prompts/
        
    Returns:
        PromptManager 实例
    """
    return PromptManager(template_dir)

