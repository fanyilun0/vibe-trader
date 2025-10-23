"""
Risk Management Module
Monitors positions and enforces risk controls independently of the AI.
"""
from typing import Dict, List, Optional, Any
from aster_client import AsterClient
from config import Config


class RiskManager:
    """Enforces risk management rules and monitors positions."""
    
    def __init__(self, aster_client: Optional[AsterClient] = None):
        """
        Initialize the risk manager.
        
        Args:
            aster_client: AsterClient instance
        """
        self.client = aster_client or AsterClient()
        self.initial_equity = None
        self.peak_equity = None
    
    def is_trade_permissible(self, signal: Dict[str, Any]) -> bool:
        """
        Check if a trade signal should be allowed based on risk rules.
        
        Args:
            signal: Trading signal to validate
            
        Returns:
            True if trade is allowed, False otherwise
        """
        action = signal.get('action', 'HOLD').upper()
        
        # Always allow HOLD and CLOSE
        if action in ['HOLD', 'CLOSE']:
            return True
        
        # Validate trading signal
        symbol = signal.get('symbol')
        stop_loss = signal.get('stop_loss')
        confidence = signal.get('confidence', 0.0)
        
        # Check confidence threshold
        if confidence < 0.7:
            print(f"❌ Trade rejected: Low confidence ({confidence:.2f} < 0.70)")
            return False
        
        # Check stop-loss requirement
        if Config.ENABLE_STOP_LOSS and not stop_loss:
            print(f"❌ Trade rejected: No stop-loss provided")
            return False
        
        # Check reward/risk ratio
        entry_price = signal.get('entry_price')
        take_profit = signal.get('take_profit')
        
        if entry_price and stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < 1.5:
                print(f"❌ Trade rejected: Poor reward/risk ratio ({rr_ratio:.2f} < 1.5)")
                return False
        
        # Check account status
        try:
            account = self.client.get_account_balances()
            total_equity = float(account.get('totalEquity', 0.0))
            
            # Check minimum equity
            if total_equity < Config.MIN_ACCOUNT_EQUITY:
                print(f"❌ Trade rejected: Equity too low (${total_equity:.2f} < ${Config.MIN_ACCOUNT_EQUITY})")
                return False
            
            # Initialize tracking if needed
            if self.initial_equity is None:
                self.initial_equity = total_equity
                self.peak_equity = total_equity
            
            # Update peak equity
            if total_equity > self.peak_equity:
                self.peak_equity = total_equity
            
            # Check drawdown
            drawdown_percent = ((self.peak_equity - total_equity) / self.peak_equity) * 100
            if drawdown_percent > Config.MAX_DRAWDOWN_PERCENT:
                print(f"❌ Trade rejected: Maximum drawdown exceeded ({drawdown_percent:.2f}% > {Config.MAX_DRAWDOWN_PERCENT}%)")
                return False
            
            # Check position concentration
            positions = self.client.get_positions()
            if positions:
                total_notional = sum(
                    abs(float(pos.get('size', 0)) * float(pos.get('markPrice', 0)))
                    for pos in positions
                )
                concentration = (total_notional / total_equity) * 100
                
                # Allow up to 5x the max position size across all positions
                max_concentration = Config.MAX_POSITION_SIZE_PERCENT * 5
                if concentration > max_concentration:
                    print(f"❌ Trade rejected: Too many open positions ({concentration:.1f}% > {max_concentration}%)")
                    return False
            
        except Exception as e:
            print(f"⚠️  Warning: Could not verify account status: {e}")
            # Allow trade if we can't check (fail open)
            return True
        
        print(f"✅ Trade approved: {action} {symbol}")
        return True
    
    def monitor_positions(self) -> Dict[str, Any]:
        """
        Monitor all open positions and take emergency action if needed.
        
        Returns:
            Dict with monitoring results and any actions taken
        """
        try:
            # Get account and positions
            account = self.client.get_account_balances()
            positions = self.client.get_positions()
            
            total_equity = float(account.get('totalEquity', 0.0))
            
            if self.initial_equity is None:
                self.initial_equity = total_equity
                self.peak_equity = total_equity
            
            # Update peak
            if total_equity > self.peak_equity:
                self.peak_equity = total_equity
            
            # Calculate metrics
            drawdown_percent = ((self.peak_equity - total_equity) / self.peak_equity) * 100 if self.peak_equity > 0 else 0
            total_return_percent = ((total_equity - self.initial_equity) / self.initial_equity) * 100 if self.initial_equity > 0 else 0
            
            print(f"\n{'='*60}")
            print(f"RISK MONITORING")
            print(f"Account Equity: ${total_equity:.2f}")
            print(f"Total Return: {total_return_percent:+.2f}%")
            print(f"Current Drawdown: {drawdown_percent:.2f}%")
            print(f"Peak Equity: ${self.peak_equity:.2f}")
            print(f"Open Positions: {len(positions)}")
            print(f"{'='*60}\n")
            
            actions_taken = []
            
            # EMERGENCY: Maximum drawdown breached - close all positions
            if drawdown_percent > Config.MAX_DRAWDOWN_PERCENT:
                print(f"🚨 EMERGENCY: Maximum drawdown exceeded! Closing all positions.")
                
                for position in positions:
                    symbol = position.get('symbol')
                    try:
                        # Close position via execution engine would be better
                        # For now, direct API call
                        pos_size = float(position.get('size', 0))
                        pos_side = position.get('side', '').upper()
                        
                        if pos_size > 0:
                            close_side = 'SELL' if pos_side == 'LONG' else 'BUY'
                            
                            if not Config.PAPER_TRADING_MODE:
                                order = self.client.place_order(
                                    symbol=symbol,
                                    side=close_side,
                                    order_type='MARKET',
                                    size=pos_size
                                )
                                actions_taken.append({
                                    'action': 'emergency_close',
                                    'symbol': symbol,
                                    'order': order
                                })
                                print(f"Closed {symbol} position: {order}")
                            else:
                                print(f"[PAPER] Would close {symbol} position")
                                actions_taken.append({
                                    'action': 'emergency_close',
                                    'symbol': symbol,
                                    'paper': True
                                })
                    except Exception as e:
                        print(f"Error closing {symbol}: {e}")
            
            # Check individual positions for liquidation risk
            for position in positions:
                symbol = position.get('symbol')
                mark_price = float(position.get('markPrice', 0))
                liquidation_price = float(position.get('liquidationPrice', 0))
                
                if liquidation_price > 0:
                    # Calculate distance to liquidation
                    distance_percent = abs(mark_price - liquidation_price) / mark_price * 100
                    
                    if distance_percent < 5:  # Less than 5% from liquidation
                        print(f"⚠️  WARNING: {symbol} is {distance_percent:.2f}% from liquidation!")
                        actions_taken.append({
                            'action': 'liquidation_warning',
                            'symbol': symbol,
                            'distance_percent': distance_percent
                        })
            
            return {
                'status': 'success',
                'equity': total_equity,
                'drawdown_percent': drawdown_percent,
                'return_percent': total_return_percent,
                'open_positions': len(positions),
                'actions_taken': actions_taken
            }
            
        except Exception as e:
            print(f"Error monitoring positions: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

