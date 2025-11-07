"""
通知模块 (Notification Module)

负责:
1. 发送交易推送通知到 ntfy.sh
2. 支持不同级别的通知
3. 格式化通知内容
"""

import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, enabled: bool = False, topic_url: str = "", level: str = "trades_only"):
        """
        初始化通知管理器
        
        Args:
            enabled: 是否启用通知
            topic_url: ntfy.sh topic 完整 URL
            level: 通知级别 (all, trades_only, important)
        """
        self.enabled = enabled
        self.topic_url = topic_url
        self.level = level
        
        if self.enabled:
            if not self.topic_url:
                logger.warning("⚠️  通知已启用但未配置 topic URL，通知功能将被禁用")
                self.enabled = False
            else:
                logger.info(f"✅ 通知管理器已启用 (级别: {self.level})")
                logger.info(f"   Topic URL: {self.topic_url}")
        else:
            logger.debug("通知管理器未启用")
    
    def _send_notification(
        self,
        title: str,
        message: str,
        priority: int = 3,
        tags: Optional[list] = None
    ) -> bool:
        """
        发送通知到 ntfy.sh
        
        Args:
            title: 通知标题
            message: 通知内容
            priority: 优先级 (1=min, 3=default, 5=max)
            tags: 标签列表（用于显示图标）
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False
        
        try:
            headers = {
                "Title": title.encode(encoding='utf-8'),
                "Priority": str(priority),
            }
            
            if tags:
                headers["Tags"] = ",".join(tags)
            
            response = requests.post(
                self.topic_url,
                data=message.encode(encoding='utf-8'),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"✅ 通知发送成功: {title}")
                return True
            else:
                logger.warning(f"⚠️  通知发送失败 (状态码: {response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送通知时发生错误: {e}")
            return False
    
    def notify_decision(
        self,
        decision: Dict[str, Any],
        account_state: Dict[str, Any],
        market_price: float
    ) -> bool:
        """
        发送AI决策通知
        
        Args:
            decision: 交易决策
            account_state: 账户状态
            market_price: 当前市场价格
            
        Returns:
            是否发送成功
        """
        action = decision.get('action', 'UNKNOWN')
        
        # 根据通知级别判断是否发送
        if self.level == 'trades_only' and action == 'HOLD':
            return False
        elif self.level == 'important':
            # important 级别只在执行结果时发送，这里不发送
            return False
        
        # 构建通知内容
        symbol = decision.get('symbol', 'N/A')
        confidence = decision.get('confidence', 0)
        rationale = decision.get('rationale', '')
        
        # 标题
        if action == 'BUY':
            title = f"🟢 开多仓 {symbol}"
            tags = ["chart_with_upwards_trend"]
            priority = 4
        elif action == 'SELL':
            title = f"🔴 开空仓 {symbol}"
            tags = ["chart_with_downwards_trend"]
            priority = 4
        elif action == 'CLOSE_POSITION':
            title = f"⚪️ 平仓 {symbol}"
            tags = ["white_circle"]
            priority = 4
        else:  # HOLD
            title = f"💤 保持观望"
            tags = ["zzz"]
            priority = 2
        
        # 消息内容
        message_lines = [
            f"操作: {action}",
            f"置信度: {confidence:.1%}",
        ]
        
        if action != 'HOLD':
            message_lines.append(f"价格: ${market_price:,.2f}")
            
            quantity = decision.get('quantity')
            if quantity:
                message_lines.append(f"数量: {quantity:.4f}")
            
            leverage = decision.get('leverage')
            if leverage:
                message_lines.append(f"杠杆: {leverage}x")
            
            exit_plan = decision.get('exit_plan')
            if exit_plan:
                stop_loss = exit_plan.get('stop_loss')
                take_profit = exit_plan.get('take_profit')
                if stop_loss:
                    message_lines.append(f"止损: ${stop_loss:,.2f}")
                if take_profit:
                    message_lines.append(f"止盈: ${take_profit:,.2f}")
        
        message_lines.append("")
        message_lines.append(f"账户权益: ${account_state.get('total_equity', 0):,.2f}")
        message_lines.append(f"可用余额: ${account_state.get('available_balance', 0):,.2f}")
        
        # 截断理由（避免过长）
        if rationale:
            short_rationale = rationale[:100] + "..." if len(rationale) > 100 else rationale
            message_lines.append("")
            message_lines.append(f"理由: {short_rationale}")
        
        message = "\n".join(message_lines)
        
        return self._send_notification(title, message, priority, tags)
    
    def notify_execution_result(
        self,
        decision: Dict[str, Any],
        execution_result: Dict[str, Any],
        account_state: Dict[str, Any]
    ) -> bool:
        """
        发送交易执行结果通知
        
        Args:
            decision: 交易决策
            execution_result: 执行结果
            account_state: 账户状态
            
        Returns:
            是否发送成功
        """
        action = decision.get('action', 'UNKNOWN')
        status = execution_result.get('status', 'UNKNOWN')
        
        # 根据通知级别判断是否发送
        if self.level == 'trades_only' and action == 'HOLD':
            return False
        
        symbol = decision.get('symbol', 'N/A')
        
        # 标题和标签
        if status == 'SUCCESS':
            if action == 'BUY':
                title = f"✅ 开多仓成功 {symbol}"
                tags = ["white_check_mark", "chart_with_upwards_trend"]
                priority = 4
            elif action == 'SELL':
                title = f"✅ 开空仓成功 {symbol}"
                tags = ["white_check_mark", "chart_with_downwards_trend"]
                priority = 4
            elif action == 'CLOSE_POSITION':
                title = f"✅ 平仓成功 {symbol}"
                tags = ["white_check_mark"]
                priority = 4
            else:
                title = f"✅ 执行成功"
                tags = ["white_check_mark"]
                priority = 3
        elif status == 'SKIPPED':
            title = f"⏭️ 跳过执行 {symbol}"
            tags = ["next_track_button"]
            priority = 2
        else:  # ERROR
            title = f"❌ 执行失败 {symbol}"
            tags = ["x", "warning"]
            priority = 5
        
        # 消息内容
        message_lines = []
        
        if status == 'SUCCESS':
            position = execution_result.get('position', {})
            if position:
                side = position.get('side', 'N/A')
                quantity = position.get('quantity', 0)
                entry_price = position.get('entry_price', 0)
                leverage = position.get('leverage', 1)
                
                message_lines.append(f"方向: {side}")
                message_lines.append(f"数量: {quantity:.4f}")
                message_lines.append(f"开仓价: ${entry_price:,.2f}")
                message_lines.append(f"杠杆: {leverage}x")
            
            # 显示止损止盈订单
            orders = execution_result.get('orders', {})
            if orders:
                sl_order = orders.get('stop_loss')
                tp_order = orders.get('take_profit')
                
                if sl_order:
                    message_lines.append(f"止损: ${sl_order.get('stop_price', 0):,.2f}")
                if tp_order:
                    message_lines.append(f"止盈: ${tp_order.get('stop_price', 0):,.2f}")
            
        elif status == 'SKIPPED':
            message_lines.append(execution_result.get('message', '跳过执行'))
        else:  # ERROR
            error = execution_result.get('error', '未知错误')
            message_lines.append(f"错误: {error}")
        
        message_lines.append("")
        message_lines.append(f"账户权益: ${account_state.get('total_equity', 0):,.2f}")
        message_lines.append(f"可用余额: ${account_state.get('available_balance', 0):,.2f}")
        message_lines.append(f"持仓数量: {account_state.get('position_count', 0)}")
        
        # 显示未实现盈亏
        unrealized_pnl = account_state.get('unrealized_pnl', 0)
        if unrealized_pnl != 0:
            pnl_sign = "+" if unrealized_pnl >= 0 else ""
            message_lines.append(f"未实现盈亏: {pnl_sign}${unrealized_pnl:.2f}")
        
        message = "\n".join(message_lines)
        
        return self._send_notification(title, message, priority, tags)
    
    def notify_error(self, error_message: str, context: str = "") -> bool:
        """
        发送错误通知
        
        Args:
            error_message: 错误消息
            context: 错误上下文
            
        Returns:
            是否发送成功
        """
        title = "❌ 系统错误"
        tags = ["x", "warning"]
        priority = 5
        
        message_lines = [
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"错误: {error_message}",
        ]
        
        if context:
            message_lines.append(f"上下文: {context}")
        
        message = "\n".join(message_lines)
        
        return self._send_notification(title, message, priority, tags)
    
    def notify_cycle_start(self, invocation_count: int) -> bool:
        """
        发送周期开始通知（仅在 all 级别）
        
        Args:
            invocation_count: 调用次数
            
        Returns:
            是否发送成功
        """
        if self.level != 'all':
            return False
        
        title = f"🔄 交易周期 #{invocation_count}"
        message = f"开始第 {invocation_count} 次交易周期"
        tags = ["arrows_counterclockwise"]
        priority = 1
        
        return self._send_notification(title, message, priority, tags)


def create_notification_manager() -> NotificationManager:
    """
    根据配置创建通知管理器
    
    Returns:
        NotificationManager实例
    """
    from config import NotificationConfig
    
    if not NotificationConfig.validate():
        logger.warning("⚠️  通知配置验证失败，通知功能将被禁用")
        return NotificationManager(enabled=False)
    
    return NotificationManager(
        enabled=NotificationConfig.NTFY_ENABLED,
        topic_url=NotificationConfig.get_topic_url(),
        level=NotificationConfig.NTFY_LEVEL
    )

