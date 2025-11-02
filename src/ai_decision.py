"""
AI 决策核心 (AI Decision Core)

负责:
1. 使用 PromptManager 构建提示词
2. 调用 Deepseek LLM API
3. 解析和验证返回的JSON决策
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, validator
import requests
import logging

from src.prompt_manager import create_prompt_manager

logger = logging.getLogger(__name__)


class ExitPlan(BaseModel):
    """退出计划数据模型"""
    take_profit: Optional[float] = Field(None, description="止盈价格")
    stop_loss: float = Field(..., description="止损价格")
    invalidation_conditions: str = Field(..., description="失效条件")


class TradingDecision(BaseModel):
    """交易决策数据模型"""
    rationale: str = Field(..., description="决策理由")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度 (0-1)")
    action: str = Field(..., description="操作类型: BUY, SELL, HOLD, CLOSE_POSITION")
    symbol: Optional[str] = Field(None, description="交易对符号")
    quantity_pct: Optional[float] = Field(None, ge=0.0, le=1.0, description="仓位百分比 (0-1)")
    exit_plan: Optional[ExitPlan] = Field(None, description="退出计划")
    leverage: Optional[int] = Field(None, description="杠杆倍数")
    risk_usd: Optional[float] = Field(None, description="风险金额(USD)")
    
    @validator('action')
    def validate_action(cls, v):
        """验证操作类型"""
        allowed_actions = ['BUY', 'SELL', 'HOLD', 'CLOSE_POSITION']
        if v not in allowed_actions:
            raise ValueError(f"action 必须是以下之一: {allowed_actions}")
        return v
    
    @validator('symbol')
    def validate_symbol_required(cls, v, values):
        """当action不为HOLD时,symbol必填"""
        if values.get('action') != 'HOLD' and not v:
            raise ValueError("当 action 不为 HOLD 时,symbol 为必填项")
        return v
    
    @validator('quantity_pct')
    def validate_quantity_required(cls, v, values):
        """当action为BUY或SELL时,quantity_pct必填"""
        if values.get('action') in ['BUY', 'SELL'] and v is None:
            raise ValueError("当 action 为 BUY 或 SELL 时,quantity_pct 为必填项")
        return v


class AIDecisionCore:
    """AI决策核心"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-reasoner"):
        """
        初始化AI决策核心
        
        Args:
            api_key: Deepseek API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # 初始化提示词管理器
        self.prompt_manager = create_prompt_manager()
        
        # 响应保存目录
        self.responses_dir = Path("responses")
        self.responses_dir.mkdir(exist_ok=True)
        
        logger.info(f"AI决策核心初始化完成 (model={model})")
    
    def save_response_to_file(self, llm_response: Dict[str, Any], invocation_count: Optional[int] = None) -> str:
        """
        保存LLM响应到本地文件
        
        Args:
            llm_response: LLM的原始响应
            invocation_count: 调用次数（用于文件名）
            
        Returns:
            保存的文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if invocation_count is not None:
            filename = f"response_{timestamp}_inv{invocation_count}.txt"
        else:
            filename = f"response_{timestamp}.txt"
        
        filepath = self.responses_dir / filename
        
        try:
            # 提取响应内容
            content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 构建完整的响应信息
            response_text = "=" * 80 + "\n"
            response_text += f"DeepSeek API Response\n"
            response_text += f"Timestamp: {timestamp}\n"
            if invocation_count is not None:
                response_text += f"Invocation: {invocation_count}\n"
            response_text += "=" * 80 + "\n\n"
            
            # Token使用信息
            if 'usage' in llm_response:
                usage = llm_response['usage']
                response_text += "Token Usage:\n"
                response_text += f"  Prompt Tokens: {usage.get('prompt_tokens', 0)}\n"
                response_text += f"  Completion Tokens: {usage.get('completion_tokens', 0)}\n"
                response_text += f"  Total Tokens: {usage.get('total_tokens', 0)}\n"
                response_text += "\n"
            
            # 原始完整响应（JSON格式）
            response_text += "-" * 80 + "\n"
            response_text += "Raw Response (JSON):\n"
            response_text += "-" * 80 + "\n"
            response_text += json.dumps(llm_response, indent=2, ensure_ascii=False) + "\n\n"
            
            # 提取的决策内容（如果是JSON）
            response_text += "-" * 80 + "\n"
            response_text += "Parsed Decision Content:\n"
            response_text += "-" * 80 + "\n"
            try:
                # 尝试解析JSON
                decisions = json.loads(content)
                response_text += json.dumps(decisions, indent=2, ensure_ascii=False) + "\n"
            except json.JSONDecodeError:
                # 如果不是JSON，直接保存内容
                response_text += content + "\n"

            # 提取推理信息
            response_text += "-" * 80 + "\n"
            reasoning_info = llm_response.get('choices', [{}])[0].get('message', {}).get('reasoning_content', '')
            response_text += "Reasoning Info:\n"
            response_text += "-" * 80 + "\n"
            response_text += reasoning_info + "\n"
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response_text)
            
            logger.info(f"✅ 响应已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存响应失败: {e}")
            return ""
    
    def call_llm(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        调用Deepseek LLM API
        
        Args:
            market_features_by_coin: 按币种组织的市场特征数据
            account_features: 账户特征
            global_state: 全局状态
            exit_plans: 持仓的退出计划字典 {symbol: exit_plan}
            max_tokens: 最大token数（None 则使用配置）
            temperature: 温度参数（None 则使用配置）
            
        Returns:
            LLM的原始响应
        """
        from config import DeepseekConfig
        
        # 使用配置中的默认值
        if max_tokens is None:
            max_tokens = DeepseekConfig.MAX_TOKENS
        if temperature is None:
            temperature = DeepseekConfig.TEMPERATURE
        
        # 使用 PromptManager 构建消息（传递exit_plans）
        messages = self.prompt_manager.get_messages(
            market_features_by_coin,
            account_features,
            global_state,
            exit_plans
        )
        
        # 保存提示词到本地（用于调试）
        try:
            self.prompt_manager.save_prompt_to_file(
                market_features_by_coin,
                account_features,
                global_state,
                exit_plans
            )
        except Exception as e:
            logger.warning(f"保存提示词失败: {e}")
        
        # 构建API请求
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        logger.info(f"调用 Deepseek API (model={self.model}, temperature={temperature}, max_tokens={max_tokens})")
        logger.info(f"  - 币种数量: {len(market_features_by_coin)}")
        logger.info(f"  - 持仓数量: {len(account_features.get('list_of_position_dictionaries', []))}")
        
        try:
            timeout = DeepseekConfig.TIMEOUT
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 记录 token 使用情况
            if 'usage' in result:
                usage = result['usage']
                logger.info(f"📊 Token 使用: "
                          f"prompt={usage.get('prompt_tokens', 0)}, "
                          f"completion={usage.get('completion_tokens', 0)}, "
                          f"total={usage.get('total_tokens', 0)}")
            
            logger.debug(f"LLM响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 保存响应到文件
            try:
                invocation_count = global_state.get('invocation_count', None)
                self.save_response_to_file(result, invocation_count)
            except Exception as e:
                logger.warning(f"保存响应文件失败: {e}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API调用失败: {e}")
            raise
    
    def parse_and_validate_decision(self, llm_response: Dict[str, Any], target_symbol: str) -> TradingDecision:
        """
        解析和验证LLM响应（新格式：多币种JSON）
        
        Args:
            llm_response: LLM的原始响应
            target_symbol: 目标币种符号（如 "BTC"）
            
        Returns:
            验证后的TradingDecision对象
            
        Raises:
            ValueError: 如果响应格式无效或目标币种不存在
        """
        try:
            # 提取响应内容
            content = llm_response['choices'][0]['message']['content']
            
            # 解析JSON（新格式是多币种结构）
            decisions_by_coin = json.loads(content)
            
            logger.debug(f"收到 {len(decisions_by_coin)} 个币种的决策")
            
            # 提取目标币种的决策
            if target_symbol not in decisions_by_coin:
                # 如果目标币种没有决策，抛出异常（让调用方决定如何处理）
                raise ValueError(f"AI未对 {target_symbol} 给出决策")
            
            coin_decision = decisions_by_coin[target_symbol]
            trade_signal_args = coin_decision.get('trade_signal_args', {})
            
            # 转换为 TradingDecision 格式
            signal = trade_signal_args.get('signal', 'hold').upper()
            
            # 映射信号类型
            action_mapping = {
                'HOLD': 'HOLD',
                'BUY_TO_ENTER': 'BUY',
                'SELL_TO_ENTER': 'SELL',
                'CLOSE_POSITION': 'CLOSE_POSITION'
            }
            
            action = action_mapping.get(signal, 'HOLD')
            
            # 构建退出计划
            # 注意：HOLD 时也可能需要补充/更新退出计划（针对已有持仓）
            exit_plan = None
            if action in ['BUY', 'SELL', 'HOLD']:
                # 检查是否提供了止损价格（必需字段）
                stop_loss = trade_signal_args.get('stop_loss')
                if stop_loss and stop_loss > 0:
                    exit_plan = ExitPlan(
                        take_profit=trade_signal_args.get('profit_target'),
                        stop_loss=stop_loss,
                        invalidation_conditions=trade_signal_args.get('invalidation_condition', '')
                    )
            
            # 构建决策对象
            decision = TradingDecision(
                rationale=trade_signal_args.get('justification', '无理由'),
                confidence=trade_signal_args.get('confidence', 0.5),
                action=action,
                symbol=f"{target_symbol}USDT" if action != 'HOLD' else None,
                quantity_pct=trade_signal_args.get('risk_usd', 0) / 10000 if action in ['BUY', 'SELL'] else None,  # 简单估算
                exit_plan=exit_plan,
                leverage=trade_signal_args.get('leverage'),
                risk_usd=trade_signal_args.get('risk_usd')
            )
            
            logger.debug(f"✓ {target_symbol}: action={decision.action}, confidence={decision.confidence}")
            
            return decision
            
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"❌ 决策解析失败: {e}")
            logger.error(f"原始响应内容: {content if 'content' in locals() else '无法获取'}")
            raise ValueError(f"无法解析LLM响应: {e}")
    
    def make_decision(
        self,
        market_features: Dict[str, Any],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        target_coin: Optional[str] = None
    ) -> TradingDecision:
        """
        生成交易决策 (完整流程)
        
        Args:
            market_features: 单个币种的市场特征（保持向后兼容）或多币种特征字典
            account_features: 账户特征
            global_state: 全局状态
            target_coin: 目标币种（用于多币种模式）
            
        Returns:
            验证后的交易决策
        """
        logger.info("开始生成交易决策")
        
        # 判断是单币种还是多币种格式
        # 如果包含'symbol'键，说明是单币种格式
        if 'symbol' in market_features:
            # 单币种格式（向后兼容）
            symbol = market_features.get('symbol', 'BTC')
            # 提取币种符号（去除USDT后缀）
            coin_symbol = symbol.replace('USDT', '')
            
            market_features_by_coin = {
                coin_symbol: market_features
            }
            target_coin = coin_symbol
        else:
            # 多币种格式
            market_features_by_coin = market_features
            # 如果没有指定目标币种，使用第一个
            if not target_coin:
                target_coin = list(market_features_by_coin.keys())[0]
        
        # 调用LLM
        llm_response = self.call_llm(market_features_by_coin, account_features, global_state)
        
        # 解析和验证（传入目标币种）
        decision = self.parse_and_validate_decision(llm_response, target_coin)
        
        return decision
    
    def make_decisions_multi(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        exit_plans: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, TradingDecision]:
        """
        生成多个币种的交易决策
        
        Args:
            market_features_by_coin: 按币种组织的市场特征
            account_features: 账户特征
            global_state: 全局状态
            exit_plans: 持仓的退出计划字典 {symbol: exit_plan}
            
        Returns:
            币种符号 -> 交易决策的字典
            
        注意：
            只返回AI明确给出决策的币种，未提及的币种会被自动跳过
        """
        logger.info(f"开始生成 {len(market_features_by_coin)} 个币种的交易决策")
        
        # 调用LLM（一次调用处理所有币种，传递exit_plans）
        llm_response = self.call_llm(market_features_by_coin, account_features, global_state, exit_plans)
        
        # 提取LLM响应中的所有币种决策
        try:
            content = llm_response['choices'][0]['message']['content']
            decisions_by_coin = json.loads(content)
            logger.info(f"✅ AI返回了 {len(decisions_by_coin)} 个币种的决策")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"❌ 无法解析LLM响应: {e}")
            return {}
        
        # 只处理AI明确给出决策的币种
        decisions = {}
        for coin_symbol in decisions_by_coin.keys():
            # 检查该币种是否在我们请求的列表中
            if coin_symbol not in market_features_by_coin:
                logger.warning(f"⚠️  AI返回了未请求的币种决策: {coin_symbol}，跳过")
                continue
            
            try:
                decision = self.parse_and_validate_decision(llm_response, coin_symbol)
                decisions[coin_symbol] = decision
                logger.info(f"✓ {coin_symbol}: {decision.action}")
            except Exception as e:
                logger.warning(f"⚠️  解析 {coin_symbol} 决策失败: {e}，跳过该币种")
                continue
        
        # 记录被跳过的币种
        skipped_coins = set(market_features_by_coin.keys()) - set(decisions.keys())
        if skipped_coins:
            logger.info(f"ℹ️  以下币种未获得AI决策，已跳过: {', '.join(sorted(skipped_coins))}")
        
        return decisions


def create_ai_decision_core() -> AIDecisionCore:
    """
    根据配置创建AI决策核心
    
    Returns:
        AIDecisionCore实例
    """
    from config import DeepseekConfig
    
    if not DeepseekConfig.validate():
        raise ValueError("Deepseek API 密钥未正确配置,请检查 .env 文件")
    
    logger.info(f"创建 AI 决策核心:")
    logger.info(f"  - 模型: {DeepseekConfig.MODEL}")
    logger.info(f"  - Temperature: {DeepseekConfig.TEMPERATURE}")
    logger.info(f"  - Max Tokens: {DeepseekConfig.MAX_TOKENS}")
    logger.info(f"  - Timeout: {DeepseekConfig.TIMEOUT}s")
    
    return AIDecisionCore(
        DeepseekConfig.API_KEY,
        DeepseekConfig.BASE_URL,
        DeepseekConfig.MODEL
    )

