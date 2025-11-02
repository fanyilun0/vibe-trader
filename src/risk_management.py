"""
风险管理与安全检查模块

这是系统的最后一道防线,在执行任何交易指令之前进行严格的安全检查。
该模块采用"不信任但验证"的哲学,假设AI可能会失败,需要限制潜在损害。
"""

from typing import Dict, Any, Optional, Tuple
import logging

from src.ai_decision import TradingDecision

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化风险管理器
        
        Args:
            config: 风险管理配置
        """
        self.config = config
        
        # 提取配置参数
        self.max_position_size_pct = config.get('max_position_size_pct', 0.20)
        self.max_open_positions = config.get('max_open_positions', 3)
        self.min_confidence = config.get('min_confidence', 0.75)
        self.allowed_symbols = set(config.get('allowed_symbols', ['BTCUSDT']))
        self.max_price_slippage_pct = config.get('max_price_slippage_pct', 0.02)
        
        logger.info(f"风险管理器初始化完成:")
        logger.info(f"  - 最大仓位: {self.max_position_size_pct*100}%")
        logger.info(f"  - 最大持仓数: {self.max_open_positions}")
        logger.info(f"  - 最低置信度: {self.min_confidence}")
        logger.info(f"  - 允许交易: {self.allowed_symbols}")
    
    def validate_decision(
        self,
        decision: TradingDecision,
        account_value: float,
        current_positions: int,
        current_price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        验证交易决策是否通过所有安全检查
        
        Args:
            decision: AI生成的交易决策
            account_value: 当前账户总价值
            current_positions: 当前持仓数量
            current_price: 当前市场价格 (用于滑点检查)
            
        Returns:
            (是否通过, 拒绝原因或"OK")
        """
        logger.info(f"开始风险检查: {decision.action} {decision.symbol}")
        
        # 如果是HOLD,直接通过
        if decision.action == 'HOLD':
            logger.info("决策为HOLD,跳过风险检查")
            return True, "OK"
        

        # 检查1: 置信度阈值
        if decision.confidence < self.min_confidence:
            reason = f"置信度过低: {decision.confidence} < {self.min_confidence}"
            logger.warning(f"❌ 风险检查失败: {reason}")
            return False, reason
        
        # 检查2: 订单规模 (仅对BUY/SELL)
        if decision.action in ['BUY', 'SELL']:
            if decision.quantity_pct is None:
                reason = "quantity_pct 未设置"
                logger.warning(f"❌ 风险检查失败: {reason}")
                return False, reason
            
            if decision.quantity_pct > self.max_position_size_pct:
                reason = f"订单规模过大: {decision.quantity_pct*100}% > {self.max_position_size_pct*100}%"
                logger.warning(f"❌ 风险检查失败: {reason}")
                return False, reason
            
            # 计算名义价值
            if current_price and account_value > 0:
                notional_value = decision.quantity_pct * account_value
                logger.info(f"  订单名义价值: ${notional_value:,.2f}")
        
        # 检查3: 最大持仓数量 (仅对BUY)
        if decision.action == 'BUY':
            if current_positions >= self.max_open_positions:
                reason = f"已达最大持仓数: {current_positions} >= {self.max_open_positions}"
                logger.warning(f"❌ 风险检查失败: {reason}")
                return False, reason
        
        # 检查4: 止损价格必须设置 (对BUY/SELL)
        if decision.action in ['BUY', 'SELL']:
            if not decision.exit_plan or decision.exit_plan.stop_loss is None:
                reason = "未设置止损价格"
                logger.warning(f"❌ 风险检查失败: {reason}")
                return False, reason
            
            # 验证止损价格合理性 (对BUY而言,止损应该低于当前价)
            if current_price:
                if decision.action == 'BUY' and decision.exit_plan.stop_loss >= current_price:
                    reason = f"BUY订单止损价格不合理: {decision.exit_plan.stop_loss} >= {current_price}"
                    logger.warning(f"❌ 风险检查失败: {reason}")
                    return False, reason
                
                if decision.action == 'SELL' and decision.exit_plan.stop_loss <= current_price:
                    reason = f"SELL订单止损价格不合理: {decision.exit_plan.stop_loss} <= {current_price}"
                    logger.warning(f"❌ 风险检查失败: {reason}")
                    return False, reason
        
        # 检查5: 失效条件必须设置
        if decision.action in ['BUY', 'SELL']:
            if not decision.exit_plan or not decision.exit_plan.invalidation_conditions:
                reason = "未设置失效条件"
                logger.warning(f"❌ 风险检查失败: {reason}")
                return False, reason
        
        # 所有检查通过
        logger.info("✅ 风险检查全部通过")
        return True, "OK"
    
    def adjust_position_size(
        self,
        decision: TradingDecision,
        account_value: float,
        volatility: Optional[float] = None
    ) -> TradingDecision:
        """
        根据风险参数调整仓位大小
        
        Args:
            decision: 原始决策
            account_value: 账户价值
            volatility: 市场波动率 (可选,可用于动态调整)
            
        Returns:
            调整后的决策
        """
        if decision.action not in ['BUY', 'SELL'] or decision.quantity_pct is None:
            return decision
        
        original_pct = decision.quantity_pct
        adjusted_pct = min(decision.quantity_pct, self.max_position_size_pct)
        
        # 如果提供了波动率,可以根据波动率动态调整
        if volatility and volatility > 0.05:  # 高波动
            adjusted_pct *= 0.8  # 减少20%仓位
            logger.info(f"高波动环境,仓位缩减20%")
        
        if adjusted_pct != original_pct:
            logger.warning(f"仓位已调整: {original_pct*100}% -> {adjusted_pct*100}%")
            decision.quantity_pct = adjusted_pct
        
        return decision
    
    def get_risk_metrics(
        self,
        positions: list,
        account_value: float
    ) -> Dict[str, Any]:
        """
        计算当前风险指标
        
        Args:
            positions: 持仓列表
            account_value: 账户价值
            
        Returns:
            风险指标字典
        """
        total_exposure = sum(abs(p.get('notional_usd', 0)) for p in positions)
        total_unrealized_pnl = sum(p.get('unrealized_pnl', 0) for p in positions)
        
        metrics = {
            'total_positions': len(positions),
            'total_exposure': total_exposure,
            'exposure_pct': total_exposure / account_value if account_value > 0 else 0,
            'total_unrealized_pnl': total_unrealized_pnl,
            'unrealized_pnl_pct': total_unrealized_pnl / account_value if account_value > 0 else 0,
        }
        
        return metrics


def create_risk_manager() -> RiskManager:
    """
    根据配置创建风险管理器
    
    Returns:
        RiskManager实例
    """
    from config import RiskManagementConfig
    return RiskManager(RiskManagementConfig.to_dict())

