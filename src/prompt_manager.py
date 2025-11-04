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

# 导入配置
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from config import Config

logger = logging.getLogger(__name__)


class PromptManager:
    """提示词管理器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化提示词管理器
        
        Args:
            template_dir: 提示词模板目录，默认使用 config.py 中的配置
        """
        # 设置模板目录（如果未指定，使用配置文件中的路径）
        if template_dir is None:
            self.template_dir = Config.prompt.TEMPLATE_DIR
        else:
            self.template_dir = Path(template_dir)
        
        # 加载系统提示词和用户提示词模板
        self.system_prompt = self._load_system_prompt()
        self.user_prompt_template = self._load_user_prompt_template()
        
        logger.info(f"提示词管理器初始化完成 (template_dir={self.template_dir})")
    
    def _load_system_prompt(self) -> str:
        """
        加载系统提示词（使用配置文件中的路径）
        
        Returns:
            系统提示词内容
        
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
    
    def _load_user_prompt_template(self) -> str:
        """
        加载用户提示词模板（使用配置文件中的路径）
        
        Returns:
            用户提示词模板内容
        """
        try:
            # 使用配置文件中的用户提示词模板路径
            user_prompt_file = Config.prompt.get_user_prompt_template_path()
            
            if not user_prompt_file.exists():
                logger.warning(f"用户提示词模板文件不存在: {user_prompt_file}")
                logger.info("将使用动态生成的用户提示词（不依赖模板文件）")
                return ""
            
            with open(user_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"✅ 用户提示词模板已加载: {user_prompt_file.name} ({len(content)} 字符)")
            return content
        except Exception as e:
            logger.warning(f"加载用户提示词模板失败: {e}")
            logger.info("将使用动态生成的用户提示词（不依赖模板文件）")
            return ""
    
    
    def _interpret_fear_greed(self, value: int) -> str:
        """
        解读恐惧贪婪指数
        
        Args:
            value: 恐惧贪婪指数值（0-100）
            
        Returns:
            解读文本
        """
        if value <= 24:
            return "**市场情绪解读**: 极度恐惧状态。市场可能过度悲观，历史上这通常是买入机会。考虑寻找技术支撑位做多，但要谨慎确认底部信号。"
        elif value <= 44:
            return "**市场情绪解读**: 恐惧状态。投资者较为谨慎，可以寻找质量好的资产在支撑位建仓，风险回报比较为有利。"
        elif value <= 55:
            return "**市场情绪解读**: 中性状态。市场情绪平衡，需要结合技术指标和趋势分析来做决策，避免盲目跟风。"
        elif value <= 74:
            return "**市场情绪解读**: 贪婪状态。市场情绪乐观，适合持有盈利仓位，但要注意及时获利了结，避免贪婪导致利润回吐。"
        else:
            return "**市场情绪解读**: 极度贪婪状态。市场可能过热，要警惕回调风险。建议收紧止损，考虑部分获利或寻找做空机会。"
    
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
        positions_without_exit_plan = []  # 记录缺少退出计划的持仓
        
        if positions:
            positions_text = "\n\n当前持仓及执行情况: \n\n"
            for pos in positions:
                symbol = pos.get('symbol', 'N/A')
                
                exit_plan = exit_plans.get(symbol, {})
                
                # 检查是否缺少退出计划
                has_exit_plan = bool(exit_plan and exit_plan.get('profit_target') and exit_plan.get('stop_loss'))
                if not has_exit_plan:
                    positions_without_exit_plan.append(symbol.replace('USDT', ''))
                
                # 获取当前价格和清算价格
                # 尝试从多个字段获取当前价格
                current_price = pos.get('current_price') or pos.get('mark_price', 0)
                liquidation_price = pos.get('liquidation_price', 0)
                
                # 持仓数量（多头为正，空头为负）
                # 注意：这里显示的数量用于AI决策，会进行适当的精度格式化以便阅读
                # 实际交易时会使用API返回的原始精度数量，确保完全平仓
                quantity = pos.get('quantity')
                side = pos.get('side', '').upper()
                
                # 格式化显示数量（保留足够精度，但去除不必要的尾部零）
                # 例如: 3.299000 -> 3.299, 1.100000 -> 1.1
                display_quantity = float(f"{quantity:.6f}".rstrip('0').rstrip('.'))
                quantity = display_quantity if side == 'LONG' else -display_quantity
                
                # 构建详细的持仓字典（包含所有执行细节）
                position_dict = {
                    'confidence': exit_plan.get('confidence', 0),  # 置信度
                    'current_price': round(current_price, 5),  # 当前价格
                    'entry_oid': pos.get('entry_oid', -1),  # 入场订单ID
                    'entry_price': round(pos.get('entry_price', 0), 2),  # 入场价格
                    'exit_plan': {
                        'profit_target': exit_plan.get('profit_target', 0),
                        'stop_loss': exit_plan.get('stop_loss', 0),
                        'invalidation_condition': exit_plan.get('invalidation_condition', '')
                    },
                    'leverage': pos.get('leverage', 1),  # 杠杆倍数
                    'liquidation_price': round(liquidation_price, 2),  # 清算价格
                    'notional_usd': round(pos.get('notional_usd', 0), 2),  # 名义价值（美元）
                    'quantity': quantity,  # 持仓数量（多头为正，空头为负）
                    'risk_usd': exit_plan.get('risk_usd', 0),  # 风险金额
                    'sl_oid': pos.get('sl_oid', -1),  # 止损订单ID
                    'symbol': symbol.replace('USDT', ''),  # 币种符号（不含USDT）
                    'tp_oid': pos.get('tp_oid', -1),  # 止盈订单ID
                    'unrealized_pnl': round(pos.get('unrealized_pnl', 0), 2),  # 未实现盈亏
                    'wait_for_fill': pos.get('wait_for_fill', False),  # 等待成交标志
                }
                
                # 格式化为单行字典字符串
                positions_text += f"{position_dict} \n"
            
            # 如果有持仓缺少退出计划，添加特别提示
            if positions_without_exit_plan:
                positions_text += f"注意：以下持仓缺少退出计划（profit_target 和 stop_loss 为0或未设置）：{', '.join(positions_without_exit_plan)}\n"
                positions_text += "请在本次决策中为这些持仓补充合理的退出计划（包括 profit_target、stop_loss 和 invalidation_condition）。\n"
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
        
        # 提取恐惧贪婪指数数据
        fear_greed_value = global_state.get('fear_greed_value', 50)
        fear_greed_classification = global_state.get('fear_greed_classification', 'Neutral')
        
        # 恐惧贪婪指数解读
        fear_greed_interpretation = self._interpret_fear_greed(fear_greed_value)
        
        header = f"""自你开始交易以来已经过去了 {minutes_trading} 分钟。当前时间是 {current_timestamp},你已经被调用了 {invocation_count} 次。以下我们为你提供各种状态数据、价格数据和预测信号,以便你发现阿尔法。下面是你当前的账户信息、价值、业绩、持仓等。

**以下所有价格或信号数据的排序方式为:最旧 → 最新**

**时间框架说明:** 除非在章节标题中另有说明,日内序列以 **3 分钟间隔**提供。如果某个币种使用不同的间隔,会在该币种的章节中明确说明。

---

### 市场情绪指标

**恐惧贪婪指数**: {fear_greed_value} ({fear_greed_classification})

{fear_greed_interpretation}

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
        template_dir: 模板目录，默认为 prompt-template/
        
    Returns:
        PromptManager 实例
    """
    return PromptManager(template_dir)

