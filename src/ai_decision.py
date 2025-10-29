"""
AI 决策核心 (AI Decision Core)

负责:
1. 构建结构化提示词
2. 调用 Deepseek LLM API
3. 解析和验证返回的JSON决策
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import requests
import logging

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
    
    # 静态指令 (第一条user消息,用于缓存优化)
    STATIC_INSTRUCTIONS = """You are a professional quantitative trader specializing in cryptocurrency perpetual futures trading. Your task is to analyze the provided market data and make informed trading decisions.

CRITICAL RULES:
1. You MUST respond ONLY in valid JSON format - no other text is allowed
2. Always consider risk management - never risk more than the specified limits
3. Provide clear, data-driven rationale for every decision
4. Set realistic stop-loss levels to protect capital
5. Consider both short-term (3-minute) and long-term (4-hour) timeframes
6. Pay attention to funding rates and open interest trends

REQUIRED OUTPUT JSON SCHEMA:
{
    "rationale": "Brief explanation of the trading decision (2-3 sentences)",
    "confidence": 0.85,  // Float between 0.0 and 1.0
    "action": "BUY",  // Must be one of: BUY, SELL, HOLD, CLOSE_POSITION
    "symbol": "BTCUSDT",  // Required if action is not HOLD
    "quantity_pct": 0.25,  // Float between 0.0 and 1.0, percentage of available margin to use
    "exit_plan": {
        "take_profit": 70000.0,  // Optional
        "stop_loss": 65000.0,  // Required
        "invalidation_conditions": "If 4h close breaks below EMA50, this bullish plan is invalidated"
    }
}

ANALYSIS GUIDELINES:
- EMA crossovers indicate trend changes
- RSI below 30 suggests oversold (potential buy), above 70 suggests overbought (potential sell)
- MACD crossovers and divergences signal momentum shifts
- High/increasing open interest with price movement confirms trend strength
- Positive funding rate indicates long bias, negative indicates short bias
- ATR indicates volatility - use for stop-loss placement
- Always set invalidation_conditions that would prove your analysis wrong

Now analyze the market data and respond with your decision in JSON format.
"""
    
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
        
        logger.info(f"AI决策核心初始化完成 (model={model})")
    
    def build_market_prompt(
        self,
        market_features: Dict[str, Any],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> str:
        """
        构建市场数据提示词 (第二条user消息,动态内容)
        
        Args:
            market_features: 市场特征数据
            account_features: 账户特征数据
            global_state: 全局状态 (交易时长、调用次数等)
            
        Returns:
            格式化的提示词字符串
        """
        symbol = market_features.get('symbol', 'UNKNOWN')
        
        prompt = f"""It has been {global_state.get('minutes_trading', 0)} minutes since you started trading. The current time is {global_state.get('current_timestamp', 'UNKNOWN')} and you've been invoked {global_state.get('invocation_count', 0)} times.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST
Timeframes: Intraday series are at 3-minute intervals. Long-term context is at 4-hour intervals.

CURRENT MARKET STATE FOR {symbol}

Current State:
- Current Price: {market_features.get('current_price')}
- Current EMA20: {market_features.get('current_ema20')}
- Current MACD: {market_features.get('current_macd')}
- Current RSI (7-period): {market_features.get('current_rsi_7')}

Derivatives Market Data:
- Open Interest - Latest: {market_features.get('latest_open_interest')}, Average: {market_features.get('average_open_interest')}
- Funding Rate: {market_features.get('funding_rate')}

Intraday Series (3-minute, oldest → newest):
- Mid Prices: {market_features.get('mid_prices_list', [])}
- EMA20 Indicators: {market_features.get('ema20_list', [])}
- MACD Indicators: {market_features.get('macd_list', [])}
- RSI Indicators (7-Period): {market_features.get('rsi_7_period_list', [])}
- RSI Indicators (14-Period): {market_features.get('rsi_14_period_list', [])}

Long-term Context (4-hour):
- 20-Period EMA: {market_features.get('long_term_ema20')} vs. 50-Period EMA: {market_features.get('long_term_ema50')}
- 3-Period ATR: {market_features.get('long_term_atr3')} vs. 14-Period ATR: {market_features.get('long_term_atr14')}
- Current Volume: {market_features.get('long_term_current_volume')} vs. Average Volume: {market_features.get('long_term_average_volume')}
- MACD Indicators: {market_features.get('long_term_macd_list', [])}
- RSI Indicators (14-Period): {market_features.get('long_term_rsi_14_period_list', [])}

YOUR ACCOUNT INFORMATION & PERFORMANCE:
- Current Total Return: {account_features.get('total_return_percent', 0):.2f}%
- Available Cash: {account_features.get('available_cash', 0)}
- Current Account Value: {account_features.get('account_value', 0)}
- Current Live Positions: {json.dumps(account_features.get('list_of_position_dictionaries', []), indent=2)}

Based on this data, provide your trading decision in JSON format.
"""
        
        return prompt
    
    def save_prompt_to_file(
        self,
        market_features: Dict[str, Any],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        save_dir: str = "prompts"
    ) -> str:
        """
        保存提示词到本地文件
        
        Args:
            market_features: 市场特征
            account_features: 账户特征
            global_state: 全局状态
            save_dir: 保存目录
            
        Returns:
            保存的文件路径
        """
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        invocation = global_state.get('invocation_count', 0)
        filename = f"prompt_{timestamp}_inv{invocation}.txt"
        filepath = os.path.join(save_dir, filename)
        
        # 构建完整提示词
        market_prompt = self.build_market_prompt(market_features, account_features, global_state)
        
        full_prompt = f"""{'='*80}
AI 交易决策提示词
{'='*80}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
调用次数: {invocation}
{'='*80}

[系统指令]
{self.STATIC_INSTRUCTIONS}

{'='*80}
[市场数据]
{'='*80}
{market_prompt}

{'='*80}
"""
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_prompt)
        
        logger.info(f"✅ 提示词已保存到: {filepath}")
        return filepath
    
    def call_llm(
        self,
        market_features: Dict[str, Any],
        account_features: Dict[str, Any],
        global_state: Dict[str, Any],
        max_tokens: int = 4000,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        调用Deepseek LLM API
        
        Args:
            market_features: 市场特征
            account_features: 账户特征
            global_state: 全局状态
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            LLM的原始响应
        """
        # 保存提示词到本地
        try:
            self.save_prompt_to_file(market_features, account_features, global_state)
        except Exception as e:
            logger.warning(f"保存提示词失败: {e}")
        
        # 构建双user消息结构 (优化缓存)
        messages = [
            {
                "role": "user",
                "content": self.STATIC_INSTRUCTIONS
            },
            {
                "role": "user",
                "content": self.build_market_prompt(market_features, account_features, global_state)
            }
        ]
        
        # 构建API请求
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"}  # 强制JSON输出
        }
        
        logger.info(f"调用 Deepseek API (model={self.model})")
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"LLM响应: {json.dumps(result, indent=2)}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API调用失败: {e}")
            raise
    
    def parse_and_validate_decision(self, llm_response: Dict[str, Any]) -> TradingDecision:
        """
        解析和验证LLM响应
        
        Args:
            llm_response: LLM的原始响应
            
        Returns:
            验证后的TradingDecision对象
            
        Raises:
            ValueError: 如果响应格式无效
        """
        try:
            # 提取响应内容
            content = llm_response['choices'][0]['message']['content']
            
            # 解析JSON
            decision_dict = json.loads(content)
            
            # 使用Pydantic验证
            decision = TradingDecision(**decision_dict)
            
            logger.info(f"决策验证通过: action={decision.action}, symbol={decision.symbol}, confidence={decision.confidence}")
            
            return decision
            
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"决策解析失败: {e}")
            logger.error(f"原始响应: {llm_response}")
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
            market_features: 市场特征
            account_features: 账户特征
            global_state: 全局状态
            
        Returns:
            验证后的交易决策
        """
        logger.info("开始生成交易决策")
        
        # 调用LLM
        llm_response = self.call_llm(market_features, account_features, global_state)
        
        # 解析和验证
        decision = self.parse_and_validate_decision(llm_response)
        
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
    
    return AIDecisionCore(
        DeepseekConfig.API_KEY,
        DeepseekConfig.BASE_URL,
        DeepseekConfig.MODEL
    )

