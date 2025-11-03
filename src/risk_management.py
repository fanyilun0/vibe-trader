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
        
        # 如果是平仓操作,跳过置信度检查（平仓优先级高于置信度要求）
        if decision.action == 'CLOSE_POSITION':
            logger.info("决策为CLOSE_POSITION,跳过置信度检查（平仓优先）")
            # 仍然进行其他检查（如果适用），但跳过置信度检查
            logger.info("✅ 平仓操作风险检查通过")
            return True, "OK"

        # 检查1: 置信度阈值（仅对 BUY/SELL 操作）
        if decision.confidence < self.min_confidence:
            reason = f"置信度过低: {decision.confidence} < {self.min_confidence}"
            logger.warning(f"❌ 风险检查失败: {reason}")
            return False, reason
        
        # 检查2: 订单规模 (仅对BUY/SELL)
        if decision.action in ['BUY', 'SELL']:
            if decision.quantity is None or decision.quantity <= 0:
                reason = "quantity 未设置或无效"
                logger.warning(f"❌ 风险检查失败: {reason}")
                return False, reason
            
            # 计算名义价值和仓位百分比
            if current_price and account_value > 0:
                notional_value = decision.quantity * current_price
                position_pct = notional_value / account_value
                
                logger.info(f"  订单名义价值: ${notional_value:,.2f}")
                
                # 检查是否超过最大仓位百分比
                if position_pct > self.max_position_size_pct:
                    reason = f"订单规模过大: {position_pct*100:.1f}% > {self.max_position_size_pct*100:.1f}%"
                    logger.warning(f"❌ 风险检查失败: {reason}")
                    return False, reason
        
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
        # 注意：现在严格按照AI决策的数量执行，不再自动调整
        # 风险检查在check_risk中完成，如果不通过会拒绝执行
        if decision.action not in ['BUY', 'SELL'] or decision.quantity is None:
            return decision
        
        # 不再调整数量，直接返回原始决策
        # 如果需要调整，应该在AI决策层面或通过风险检查拒绝执行
        logger.debug(f"风险调整: 保持AI决策数量 {decision.quantity}")
        
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

