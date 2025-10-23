"""
Vibe Trader - Main Entry Point
AI-Powered Perpetual Futures Trading Bot using DeepSeek + Aster DEX
"""
import time
import sys
import argparse
from typing import Optional
from datetime import datetime

from config import Config
from aster_client import AsterClient
from data_aggregator import DataAggregator
from signal_generator import SignalGenerator
from execution_engine import ExecutionEngine
from risk_manager import RiskManager


class VibeTrader:
    """Main trading bot orchestrator."""
    
    def __init__(self, paper_trading: Optional[bool] = None):
        """
        Initialize the Vibe Trader bot.
        
        Args:
            paper_trading: Override paper trading mode from config
        """
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            print("Please check your .env file and ensure all required fields are set.")
            sys.exit(1)
        
        # Initialize components
        print("🤖 Initializing Vibe Trader...")
        
        self.aster_client = AsterClient()
        self.data_aggregator = DataAggregator(self.aster_client)
        self.signal_generator = SignalGenerator()
        self.execution_engine = ExecutionEngine(self.aster_client, paper_trading)
        self.risk_manager = RiskManager(self.aster_client)
        
        self.paper_trading = paper_trading if paper_trading is not None else Config.PAPER_TRADING_MODE
        self.running = False
        
        print(f"✅ Initialization complete")
        print(f"Mode: {'PAPER TRADING' if self.paper_trading else 'LIVE TRADING'}")
        print(f"Symbols: {', '.join(Config.TRADING_SYMBOLS)}")
        print(f"Loop Interval: {Config.LOOP_INTERVAL_SECONDS}s")
        print()
    
    def main_loop(self):
        """Main trading loop."""
        self.running = True
        iteration = 0
        
        print("="*80)
        print("🚀 VIBE TRADER STARTED")
        print("="*80)
        print()
        
        while self.running:
            try:
                iteration += 1
                print(f"\n{'='*80}")
                print(f"ITERATION #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*80}\n")
                
                # Step 1: Data Aggregation
                print("📊 Step 1: Fetching market data...")
                market_data = self.data_aggregator.fetch_all_data()
                
                if not market_data.get('coins_data'):
                    print("⚠️  No market data available, skipping iteration")
                    time.sleep(Config.LOOP_INTERVAL_SECONDS)
                    continue
                
                print(f"✅ Fetched data for {len(market_data['coins_data'])} symbols")
                
                # Step 2: Signal Generation
                print("\n🧠 Step 2: Generating trading signal with DeepSeek...")
                signal = self.signal_generator.get_signal(market_data)
                
                print(f"\n📋 Signal Generated:")
                print(f"  Action: {signal.get('action')}")
                print(f"  Symbol: {signal.get('symbol')}")
                print(f"  Confidence: {signal.get('confidence', 0):.2%}")
                print(f"  Entry: {signal.get('entry_price')}")
                print(f"  Stop Loss: {signal.get('stop_loss')}")
                print(f"  Take Profit: {signal.get('take_profit')}")
                
                # Step 3: Risk Management Pre-Check
                print("\n🛡️  Step 3: Risk management validation...")
                is_permissible = self.risk_manager.is_trade_permissible(signal)
                
                if is_permissible:
                    # Step 4: Trade Execution
                    print("\n⚡ Step 4: Executing trade...")
                    execution_result = self.execution_engine.execute(signal)
                    
                    if execution_result.get('status') == 'success':
                        print(f"✅ Execution successful")
                    else:
                        print(f"❌ Execution failed: {execution_result.get('message')}")
                else:
                    print("❌ Trade rejected by risk manager")
                
                # Step 5: Position Monitoring
                print("\n👀 Step 5: Monitoring positions...")
                monitoring_result = self.risk_manager.monitor_positions()
                
                if monitoring_result.get('actions_taken'):
                    print(f"⚠️  Risk manager took {len(monitoring_result['actions_taken'])} action(s)")
                
                # Sleep until next iteration
                print(f"\n⏸️  Sleeping for {Config.LOOP_INTERVAL_SECONDS} seconds...")
                print(f"{'='*80}\n")
                
                time.sleep(Config.LOOP_INTERVAL_SECONDS)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Keyboard interrupt received")
                self.shutdown()
                break
            except Exception as e:
                print(f"\n❌ Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                
                # Continue after error, but sleep a bit longer
                print(f"Sleeping for 60 seconds before retry...")
                time.sleep(60)
    
    def shutdown(self):
        """Gracefully shutdown the bot."""
        print("\n" + "="*80)
        print("🛑 SHUTTING DOWN VIBE TRADER")
        print("="*80)
        
        self.running = False
        
        # Print final statistics
        print("\n📊 Final Statistics:")
        try:
            monitoring = self.risk_manager.monitor_positions()
            print(f"  Account Equity: ${monitoring.get('equity', 0):.2f}")
            print(f"  Total Return: {monitoring.get('return_percent', 0):+.2f}%")
            print(f"  Max Drawdown: {monitoring.get('drawdown_percent', 0):.2f}%")
            print(f"  Open Positions: {monitoring.get('open_positions', 0)}")
        except:
            pass
        
        print(f"\n  Total Iterations: {self.data_aggregator.invocation_count}")
        print(f"  Total Trades: {len(self.execution_engine.trade_history)}")
        
        print("\n✅ Shutdown complete")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Vibe Trader - AI-Powered Perpetual Futures Trading Bot'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run in live trading mode (default: paper trading)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom .env file'
    )
    
    args = parser.parse_args()
    
    # Override paper trading mode if --live flag is set
    paper_trading = not args.live
    
    if args.live:
        print("\n" + "="*80)
        print("⚠️  WARNING: LIVE TRADING MODE ENABLED")
        print("="*80)
        print("\nYou are about to run the bot in LIVE mode with real money.")
        print("This involves substantial risk of loss.")
        print("\nType 'I ACCEPT THE RISK' to continue: ")
        
        confirmation = input().strip()
        if confirmation != "I ACCEPT THE RISK":
            print("\n❌ Live trading cancelled")
            sys.exit(0)
        print()
    
    # Create and run bot
    try:
        bot = VibeTrader(paper_trading=paper_trading)
        bot.main_loop()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

