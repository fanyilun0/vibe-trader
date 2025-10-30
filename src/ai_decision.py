"""
AI 决策核心 (AI Decision Core)

负责:
1. 使用 PromptManager 构建提示词
2. 调用 Deepseek LLM API
3. 解析和验证返回的JSON决策
"""

import json
from typing import Dict, Any, Optional
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
        
        logger.info(f"AI决策核心初始化完成 (model={model})")
    
    
    def call_llm(
        self,
        market_features_by_coin: Dict[str, Dict[str, Any]],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        调用Deepseek LLM API
        
        Args:
            market_features_by_coin: 按币种组织的市场特征数据
            account_features: 账户特征
            global_state: 全局状态
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
        
        # 使用 PromptManager 构建消息
        messages = self.prompt_manager.get_messages(
            market_features_by_coin,
            account_features,
            global_state
        )
        
        # 保存提示词到本地（用于调试）
        try:
            self.prompt_manager.save_prompt_to_file(
                market_features_by_coin,
                account_features,
                global_state
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
            ValueError: 如果响应格式无效
        """
        try:
            # 提取响应内容
            content = llm_response['choices'][0]['message']['content']
            
            # 解析JSON（新格式是多币种结构）
            decisions_by_coin = json.loads(content)
            
            logger.info(f"收到 {len(decisions_by_coin)} 个币种的决策")
            
            # 提取目标币种的决策
            if target_symbol not in decisions_by_coin:
                # 如果目标币种没有决策，返回 HOLD
                logger.warning(f"LLM未对 {target_symbol} 给出决策，默认为 HOLD")
                return TradingDecision(
                    rationale=f"LLM未给出明确决策，保持观望",
                    confidence=0.5,
                    action="HOLD",
                    symbol=None,
                    quantity_pct=None,
                    exit_plan=None
                )
            
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
            exit_plan = None
            if action in ['BUY', 'SELL']:
                exit_plan = ExitPlan(
                    take_profit=trade_signal_args.get('profit_target'),
                    stop_loss=trade_signal_args.get('stop_loss'),
                    invalidation_conditions=trade_signal_args.get('invalidation_condition', '')
                )
            
            # 构建决策对象
            decision = TradingDecision(
                rationale=trade_signal_args.get('justification', '无理由'),
                confidence=trade_signal_args.get('confidence', 0.5),
                action=action,
                symbol=f"{target_symbol}USDT" if action != 'HOLD' else None,
                quantity_pct=trade_signal_args.get('risk_usd', 0) / 10000 if action in ['BUY', 'SELL'] else None,  # 简单估算
                exit_plan=exit_plan
            )
            
            logger.info(f"决策验证通过: action={decision.action}, symbol={decision.symbol}, confidence={decision.confidence}")
            
            return decision
            
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"决策解析失败: {e}")
            logger.error(f"原始响应内容: {content if 'content' in locals() else '无法获取'}")
            raise ValueError(f"无法解析LLM响应: {e}")
    
    def make_decision(
        self,
        market_features: Dict[str, Any],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> TradingDecision:
        """
        生成交易决策 (完整流程)
        
        Args:
            market_features: 单个币种的市场特征（保持向后兼容）
            account_features: 账户特征
            global_state: 全局状态
            
        Returns:
            验证后的交易决策
        """
        logger.info("开始生成交易决策")
        
        # 将单币种市场特征转换为多币种格式
        symbol = market_features.get('symbol', 'BTC')
        # 提取币种符号（去除USDT后缀）
        coin_symbol = symbol.replace('USDT', '')
        
        market_features_by_coin = {
            coin_symbol: market_features
        }
        
        # 调用LLM
        llm_response = self.call_llm(market_features_by_coin, account_features, global_state)
        
        # 解析和验证（传入目标币种）
        decision = self.parse_and_validate_decision(llm_response, coin_symbol)
        
        return decision


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

