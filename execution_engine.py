"""
Trade Execution Engine
Executes trades on Aster DEX based on signals from the LLM.
"""
from typing import Dict, Optional, Any
from aster_client import AsterClient
from config import Config


class ExecutionEngine:
    """Handles trade execution and order management."""
    
    def __init__(self, aster_client: Optional[AsterClient] = None, paper_trading: bool = None):
        """
        Initialize the execution engine.
        
        Args:
            aster_client: AsterClient instance
            paper_trading: Whether to run in paper trading mode (defaults to config)
        """
        self.client = aster_client or AsterClient()
        self.paper_trading = paper_trading if paper_trading is not None else Config.PAPER_TRADING_MODE
        self.trade_history = []
    
    def execute(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal from SignalGenerator
            
        Returns:
            Execution result dict
        """
        action = signal.get('action', 'HOLD').upper()
        symbol = signal.get('symbol')
        
        print(f"\n{'='*60}")
        print(f"EXECUTING SIGNAL: {action} {symbol if symbol else ''}")
        print(f"Reasoning: {signal.get('reasoning', 'N/A')[:200]}...")
        print(f"Confidence: {signal.get('confidence', 0.0):.2f}")
        print(f"{'='*60}\n")
        
        if action == 'HOLD':
            return self._handle_hold(signal)
        elif action == 'CLOSE':
            return self._handle_close(signal)
        elif action in ['LONG', 'SHORT']:
            return self._handle_open_position(signal)
        else:
            print(f"Unknown action: {action}")
            return {'status': 'error', 'message': f'Unknown action: {action}'}
    
    def _handle_hold(self, signal: Dict) -> Dict:
        """Handle HOLD signal."""
        print("Action: HOLD - No trade executed")
        return {
            'status': 'success',
            'action': 'HOLD',
            'message': 'No action taken'
        }
    
    def _handle_close(self, signal: Dict) -> Dict:
        """Handle CLOSE signal - close all positions for a symbol."""
        symbol = signal.get('symbol')
        
        if not symbol:
            print("CLOSE signal requires a symbol")
            return {'status': 'error', 'message': 'Symbol required for CLOSE action'}
        
        try:
            # Get current positions for this symbol
            positions = self.client.get_positions(symbol=symbol)
            
            if not positions:
                print(f"No open positions found for {symbol}")
                return {'status': 'success', 'action': 'CLOSE', 'message': 'No positions to close'}
            
            # Close each position
            results = []
            for position in positions:
                pos_size = float(position.get('size', 0))
                pos_side = position.get('side', '').upper()
                
                if pos_size == 0:
                    continue
                
                # Determine closing side (opposite of position)
                close_side = 'SELL' if pos_side == 'LONG' else 'BUY'
                
                if self.paper_trading:
                    print(f"[PAPER] Closing {pos_side} position: {close_side} {pos_size} {symbol}")
                    results.append({
                        'symbol': symbol,
                        'side': close_side,
                        'size': pos_size,
                        'type': 'MARKET',
                        'paper': True
                    })
                else:
                    # Execute market close order
                    order = self.client.place_order(
                        symbol=symbol,
                        side=close_side,
                        order_type='MARKET',
                        size=pos_size
                    )
                    results.append(order)
                    print(f"Closed {pos_side} position: {order}")
            
            return {
                'status': 'success',
                'action': 'CLOSE',
                'symbol': symbol,
                'orders': results
            }
            
        except Exception as e:
            print(f"Error closing positions: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_open_position(self, signal: Dict) -> Dict:
        """Handle LONG or SHORT signal - open a new position."""
        action = signal.get('action')
        symbol = signal.get('symbol')
        entry_price = signal.get('entry_price')
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        leverage = signal.get('leverage', Config.DEFAULT_LEVERAGE)
        confidence = signal.get('confidence', 0.0)
        
        # Validation
        if not symbol:
            return {'status': 'error', 'message': 'Symbol required'}
        
        if not stop_loss and Config.ENABLE_STOP_LOSS:
            print("WARNING: No stop-loss provided, rejecting trade")
            return {'status': 'error', 'message': 'Stop-loss required but not provided'}
        
        if confidence < 0.7:
            print(f"WARNING: Low confidence ({confidence:.2f}), rejecting trade")
            return {'status': 'error', 'message': f'Confidence too low: {confidence:.2f}'}
        
        try:
            # Get account info to calculate position size
            account = self.client.get_account_balances()
            total_equity = float(account.get('totalEquity', 0.0))
            
            if total_equity < Config.MIN_ACCOUNT_EQUITY:
                return {'status': 'error', 'message': f'Account equity too low: ${total_equity:.2f}'}
            
            # Calculate position size based on risk management
            position_size = self._calculate_position_size(
                total_equity=total_equity,
                entry_price=entry_price or 0,
                stop_loss=stop_loss or 0,
                leverage=leverage
            )
            
            if position_size <= 0:
                return {'status': 'error', 'message': 'Calculated position size is zero or negative'}
            
            # Determine order side
            side = 'BUY' if action == 'LONG' else 'SELL'
            
            # Set leverage first
            if not self.paper_trading:
                try:
                    self.client.set_leverage(symbol, leverage)
                    print(f"Set leverage to {leverage}x for {symbol}")
                except Exception as e:
                    print(f"Warning: Could not set leverage: {e}")
            
            # Place entry order
            if self.paper_trading:
                print(f"\n[PAPER TRADE]")
                print(f"Symbol: {symbol}")
                print(f"Side: {side} ({action})")
                print(f"Size: {position_size}")
                print(f"Entry Price: ~{entry_price}")
                print(f"Stop Loss: {stop_loss}")
                print(f"Take Profit: {take_profit}")
                print(f"Leverage: {leverage}x")
                print(f"Risk: ${total_equity * Config.RISK_PER_TRADE_PERCENT / 100:.2f}")
                
                entry_order = {
                    'orderId': f'PAPER_{symbol}_{int(time.time())}',
                    'symbol': symbol,
                    'side': side,
                    'size': position_size,
                    'type': 'MARKET',
                    'paper': True
                }
            else:
                # Place market order with stop-loss and take-profit
                entry_order = self.client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='MARKET',
                    size=position_size,
                    leverage=leverage,
                    stop_loss=stop_loss if Config.ENABLE_STOP_LOSS else None,
                    take_profit=take_profit if Config.ENABLE_TAKE_PROFIT else None
                )
                print(f"Order executed: {entry_order}")
            
            # Record trade
            trade_record = {
                'timestamp': time.time(),
                'signal': signal,
                'order': entry_order,
                'account_equity': total_equity,
                'position_size': position_size
            }
            self.trade_history.append(trade_record)
            
            return {
                'status': 'success',
                'action': action,
                'symbol': symbol,
                'order': entry_order,
                'position_size': position_size
            }
            
        except Exception as e:
            print(f"Error executing trade: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _calculate_position_size(
        self,
        total_equity: float,
        entry_price: float,
        stop_loss: float,
        leverage: int
    ) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            total_equity: Total account equity
            entry_price: Entry price for the position
            stop_loss: Stop loss price
            leverage: Leverage multiplier
            
        Returns:
            Position size in base currency
        """
        if entry_price <= 0 or stop_loss <= 0:
            print("Invalid entry or stop-loss price")
            return 0.0
        
        # Calculate risk per trade in USD
        risk_usd = total_equity * (Config.RISK_PER_TRADE_PERCENT / 100)
        
        # Calculate price risk (distance to stop-loss)
        price_risk = abs(entry_price - stop_loss)
        price_risk_percent = price_risk / entry_price
        
        # Calculate position size
        # Position notional value = risk_usd / price_risk_percent
        notional_value = risk_usd / price_risk_percent
        
        # Check against maximum position size
        max_notional = total_equity * (Config.MAX_POSITION_SIZE_PERCENT / 100) * leverage
        notional_value = min(notional_value, max_notional)
        
        # Convert to position size (in base currency)
        position_size = notional_value / entry_price
        
        print(f"Position Sizing: Equity=${total_equity:.2f}, Risk=${risk_usd:.2f}, "
              f"Notional=${notional_value:.2f}, Size={position_size:.6f}")
        
        return position_size


# Import time for paper trading IDs
import time

