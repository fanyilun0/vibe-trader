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
from config import Config, RiskManagementConfig

logger = logging.getLogger(__name__)


class PromptManager:
    """提示词管理器"""
    
    # 数据点数量控制常量
    INTRADAY_DATA_POINTS = 10  # 日内数据点数量（3分钟间隔）
    LONGTERM_DATA_POINTS = 10  # 长期数据点数量（4小时间隔）
    
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
        logger.info(f"数据点配置: 日内={self.INTRADAY_DATA_POINTS}个, 长期={self.LONGTERM_DATA_POINTS}个")
    
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
        def format_list(data_list, precision=2, limit=None):
            """
            格式化数组数据（单行显示）
            
            Args:
                data_list: 原始数据列表
                precision: 数值精度
                limit: 限制数据点数量（None表示不限制，取最新的N个）
            """
            if not data_list:
                return "[]"
            
            # 如果设置了限制，只取最新的N个数据点
            if limit is not None and len(data_list) > limit:
                data_list = data_list[-limit:]
            
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

**日内序列:**

中间价:{format_list(market_features.get('mid_prices_list', []), 2, self.INTRADAY_DATA_POINTS)}

EMA 指标(20 周期):{format_list(market_features.get('ema20_list', []), 3, self.INTRADAY_DATA_POINTS)}

MACD 指标:{format_list(market_features.get('macd_list', []), 3, self.INTRADAY_DATA_POINTS)}

RSI 指标(7 周期):{format_list(market_features.get('rsi_7_period_list', []), 3, self.INTRADAY_DATA_POINTS)}

RSI 指标(14 周期):{format_list(market_features.get('rsi_14_period_list', []), 3, self.INTRADAY_DATA_POINTS)}

**长期背景:**

20 周期 EMA:{market_features.get('long_term_ema20', 0)} vs. 50 周期 EMA:{market_features.get('long_term_ema50', 0)}

3 周期 ATR:{market_features.get('long_term_atr3', 0)} vs. 14 周期 ATR:{market_features.get('long_term_atr14', 0)}

当前成交量:{market_features.get('long_term_current_volume', 0)} vs. 平均成交量:{market_features.get('long_term_average_volume', 0)}

MACD 指标:{format_list(market_features.get('long_term_macd_list', []), 3, self.LONGTERM_DATA_POINTS)}

RSI 指标(14 周期):{format_list(market_features.get('long_term_rsi_14_period_list', []), 3, self.LONGTERM_DATA_POINTS)}

"""
        return section
    
    def build_user_prompt(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None
    ) -> str:
        """
        构建完整的用户提示词（基于模板文件）
        
        Args:
            market_features_by_coin: 按币种组织的市场特征数据 {"BTC": {...}, "ETH": {...}}
            account_features: 账户特征数据
            global_state: 全局状态（交易时长、调用次数等）
            exit_plans: 持仓的退出计划字典 {symbol: exit_plan}
            
        Returns:
            完整的用户提示词
        """
        
        # 准备模板占位符数据
        placeholders = self._prepare_template_placeholders(
            market_features_by_coin,
            account_features,
            global_state,
            exit_plans
        )
        
        # 替换模板占位符
        user_prompt = self._replace_placeholders(self.user_prompt_template, placeholders)
        
        return user_prompt
    
    def _prepare_template_placeholders(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        准备模板占位符数据
        
        Args:
            market_features_by_coin: 市场特征数据
            account_features: 账户特征数据
            global_state: 全局状态
            exit_plans: 退出计划
            
        Returns:
            占位符字典 {placeholder_name: value}
        """
        # 基础信息
        minutes_trading = global_state.get('minutes_trading', 0)
        current_timestamp = global_state.get('current_timestamp', datetime.now().isoformat())
        invocation_count = global_state.get('invocation_count', 0)
        
        # 恐惧贪婪指数
        fear_greed_value = global_state.get('fear_greed_value', 50)
        fear_greed_classification = global_state.get('fear_greed_classification', 'Neutral')
        
        # 构建币种数据部分
        coin_sections = []
        for coin_symbol, market_features in market_features_by_coin.items():
            coin_section = self.build_coin_data_section(coin_symbol, market_features)
            coin_sections.append(coin_section)
        coin_data_sections = "\n".join(coin_sections)
        
        # 构建持仓文本
        positions_text = self._build_positions_text(account_features, exit_plans)
        
        # 风险管理参数
        max_position_size_pct = RiskManagementConfig.MAX_POSITION_SIZE_PCT * 100
        max_open_positions = RiskManagementConfig.MAX_OPEN_POSITIONS
        
        # 账户信息
        total_return_pct = account_features.get('total_return_percent', 0)
        available_cash = account_features.get('available_cash', 0)
        account_value = account_features.get('account_value', 0)
        sharpe_ratio = account_features.get('sharpe_ratio', 0)
        
        # 组装所有占位符
        placeholders = {
            'MINUTES_TRADING': str(minutes_trading),
            'CURRENT_TIMESTAMP': str(current_timestamp),
            'INVOCATION_COUNT': str(invocation_count),
            'DATA_POINTS': str(self.INTRADAY_DATA_POINTS),
            'FEAR_GREED_VALUE': str(fear_greed_value),
            'FEAR_GREED_CLASSIFICATION': str(fear_greed_classification),
            'COIN_DATA_SECTIONS': coin_data_sections,
            'MAX_POSITION_SIZE_PCT': f"{max_position_size_pct:.0f}",
            'MAX_OPEN_POSITIONS': str(max_open_positions),
            'TOTAL_RETURN_PCT': f"{total_return_pct:.2f}",
            'AVAILABLE_CASH': f"{available_cash:.2f}",
            'ACCOUNT_VALUE': f"{account_value:.2f}",
            'POSITIONS_TEXT': positions_text,
            'SHARPE_RATIO': f"{sharpe_ratio:.3f}"
        }
        
        return placeholders
    
    def _replace_placeholders(self, template: str, placeholders: Dict[str, str]) -> str:
        """
        替换模板中的占位符
        
        Args:
            template: 模板字符串
            placeholders: 占位符字典
            
        Returns:
            替换后的字符串
        """
        result = template
        for key, value in placeholders.items():
            placeholder = f"{{{{{key}}}}}"  # {{KEY}}
            result = result.replace(placeholder, str(value))
        
        return result
    
    def _build_positions_text(
        self,
        account_features: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None
    ) -> str:
        """
        构建持仓文本部分
        
        Args:
            account_features: 账户特征数据
            exit_plans: 退出计划字典
            
        Returns:
            格式化的持仓文本
        """
        # 提取持仓信息
        positions = account_features.get('list_of_position_dictionaries', [])
        
        if exit_plans is None:
            exit_plans = {}
        
        # 格式化持仓信息
        positions_text = ""
        positions_without_exit_plan = []
        
        if positions:
            positions_text = "当前持仓及执行情况: \n\n"
            for pos in positions:
                symbol = pos.get('symbol', 'N/A')
                
                exit_plan = exit_plans.get(symbol, {})
                
                # 检查是否缺少退出计划
                has_exit_plan = bool(exit_plan and exit_plan.get('profit_target') and exit_plan.get('stop_loss'))
                if not has_exit_plan:
                    positions_without_exit_plan.append(symbol.replace('USDT', ''))
                
                # 获取当前价格和清算价格
                current_price = pos.get('current_price') or pos.get('mark_price', 0)
                liquidation_price = pos.get('liquidation_price', 0)
                
                # 持仓数量
                quantity = pos.get('quantity')
                side = pos.get('side', '').upper()
                
                # 格式化显示数量
                display_quantity = float(f"{quantity:.6f}".rstrip('0').rstrip('.'))
                quantity = display_quantity if side == 'LONG' else -display_quantity
                
                # 构建详细的持仓字典
                position_dict = {
                    'confidence': exit_plan.get('confidence', 0),
                    'current_price': round(current_price, 5),
                    'entry_oid': pos.get('entry_oid', -1),
                    'entry_price': round(pos.get('entry_price', 0), 2),
                    'exit_plan': {
                        'profit_target': exit_plan.get('profit_target', 0),
                        'stop_loss': exit_plan.get('stop_loss', 0),
                        'invalidation_condition': exit_plan.get('invalidation_condition', '')
                    },
                    'leverage': pos.get('leverage', 1),
                    'liquidation_price': round(liquidation_price, 2),
                    'notional_usd': round(pos.get('notional_usd', 0), 2),
                    'quantity': quantity,
                    'risk_usd': exit_plan.get('risk_usd', 0),
                    'sl_oid': pos.get('sl_oid', -1),
                    'symbol': symbol.replace('USDT', ''),
                    'tp_oid': pos.get('tp_oid', -1),
                    'unrealized_pnl': round(pos.get('unrealized_pnl', 0), 2),
                    'wait_for_fill': pos.get('wait_for_fill', False),
                }
                
                # 格式化为单行字典字符串
                positions_text += f"{position_dict} \n"
            
            # 如果有持仓缺少退出计划，添加特别提示
            if positions_without_exit_plan:
                positions_text += f"\n注意：以下持仓缺少退出计划（profit_target 和 stop_loss 为0或未设置）：{', '.join(positions_without_exit_plan)}\n"
                positions_text += "请在本次决策中为这些持仓补充合理的退出计划（包括 profit_target、stop_loss 和 invalidation_condition）。\n"
        else:
            positions_text = "无持仓\n"
        
        return positions_text
    
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

