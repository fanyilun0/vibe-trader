"""
Mock Aster Client for Testing
Provides simulated data without making real API calls.
"""
import time
import random
from typing import Dict, List, Optional


class MockAsterClient:
    """Mock client for testing without real API calls."""
    
    def __init__(self):
        """Initialize mock client."""
        self.base_price = {
            'BTCUSDT': 65000.0,
            'ETHUSDT': 3200.0,
            'SOLUSDT': 140.0
        }
    
    def get_klines(
        self,
        symbol: str,
        interval: str = "1m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[List]:
        """Generate mock k-line data."""
        base = self.base_price.get(symbol, 1000.0)
        current_time = int(time.time() * 1000)
        
        # Determine interval in milliseconds
        interval_ms = {
            '1m': 60000,
            '3m': 180000,
            '5m': 300000,
            '15m': 900000,
            '30m': 1800000,
            '1h': 3600000,
            '2h': 7200000,
            '4h': 14400000,
            '6h': 21600000,
            '12h': 43200000,
            '1d': 86400000
        }.get(interval, 60000)
        
        klines = []
        for i in range(limit):
            timestamp = current_time - (limit - i) * interval_ms
            
            # Simulate price movement
            variation = random.uniform(-0.02, 0.02)
            open_price = base * (1 + variation)
            high_price = open_price * (1 + random.uniform(0, 0.01))
            low_price = open_price * (1 - random.uniform(0, 0.01))
            close_price = open_price * (1 + random.uniform(-0.01, 0.01))
            volume = random.uniform(100, 1000)
            
            klines.append([
                timestamp,
                str(open_price),
                str(high_price),
                str(low_price),
                str(close_price),
                str(volume),
                timestamp + interval_ms - 1,
                str(volume * open_price),
                random.randint(100, 500),
                str(volume * 0.6),
                str(volume * 0.6 * open_price),
                "0"
            ])
            
            base = close_price
        
        return klines
    
    def get_funding_rate(self, symbol: str) -> Dict:
        """Get mock funding rate."""
        return {
            'symbol': symbol,
            'fundingRate': random.uniform(-0.0001, 0.0001),
            'fundingTime': int(time.time() * 1000)
        }
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """Get mock order book."""
        base = self.base_price.get(symbol, 1000.0)
        
        bids = []
        asks = []
        
        for i in range(limit):
            bid_price = base * (1 - (i + 1) * 0.0001)
            ask_price = base * (1 + (i + 1) * 0.0001)
            bid_qty = random.uniform(0.1, 10.0)
            ask_qty = random.uniform(0.1, 10.0)
            
            bids.append([str(bid_price), str(bid_qty)])
            asks.append([str(ask_price), str(ask_qty)])
        
        return {
            'lastUpdateId': int(time.time() * 1000),
            'bids': bids,
            'asks': asks
        }
    
    def get_account_info(self) -> Dict:
        """Get mock account information."""
        return {
            'feeTier': 0,
            'canTrade': True,
            'canDeposit': True,
            'canWithdraw': True,
            'updateTime': 0,
            'totalInitialMargin': '0.00000000',
            'totalMaintMargin': '0.00000000',
            'totalWalletBalance': '10000.00000000',
            'totalUnrealizedProfit': '0.00000000',
            'totalMarginBalance': '10000.00000000',
            'totalPositionInitialMargin': '0.00000000',
            'totalOpenOrderInitialMargin': '0.00000000',
            'totalCrossWalletBalance': '10000.00000000',
            'totalCrossUnPnl': '0.00000000',
            'availableBalance': '10000.00000000',
            'maxWithdrawAmount': '10000.00000000',
            'assets': [
                {
                    'asset': 'USDT',
                    'walletBalance': '10000.00000000',
                    'unrealizedProfit': '0.00000000',
                    'marginBalance': '10000.00000000',
                    'maintMargin': '0.00000000',
                    'initialMargin': '0.00000000',
                    'positionInitialMargin': '0.00000000',
                    'openOrderInitialMargin': '0.00000000',
                    'crossWalletBalance': '10000.00000000',
                    'crossUnPnl': '0.00000000',
                    'availableBalance': '10000.00000000',
                    'maxWithdrawAmount': '10000.00000000'
                }
            ],
            'positions': []
        }
    
    def get_account_balances(self) -> List[Dict]:
        """Get mock balance information."""
        return [
            {
                'accountAlias': 'test',
                'asset': 'USDT',
                'balance': '10000.00000000',
                'crossWalletBalance': '10000.00000000',
                'crossUnPnl': '0.00000000',
                'availableBalance': '10000.00000000',
                'maxWithdrawAmount': '10000.00000000'
            }
        ]
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get mock positions."""
        return []
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get mock ticker."""
        base = self.base_price.get(symbol, 1000.0)
        return {
            'symbol': symbol,
            'priceChange': str(random.uniform(-100, 100)),
            'priceChangePercent': str(random.uniform(-5, 5)),
            'weightedAvgPrice': str(base),
            'lastPrice': str(base),
            'lastQty': str(random.uniform(0.1, 1.0)),
            'openPrice': str(base * (1 + random.uniform(-0.02, 0.02))),
            'highPrice': str(base * 1.01),
            'lowPrice': str(base * 0.99),
            'volume': str(random.uniform(10000, 100000)),
            'quoteVolume': str(random.uniform(100000000, 1000000000)),
            'openTime': int(time.time() * 1000) - 86400000,
            'closeTime': int(time.time() * 1000),
            'firstId': 1,
            'lastId': 100000,
            'count': 100000
        }
    
    def place_order(self, **kwargs) -> Dict:
        """Mock place order."""
        return {
            'orderId': random.randint(1000000, 9999999),
            'symbol': kwargs.get('symbol', 'BTCUSDT'),
            'status': 'NEW',
            'clientOrderId': f"mock_{int(time.time())}",
            'price': str(kwargs.get('price', 0)),
            'avgPrice': '0.00',
            'origQty': str(kwargs.get('quantity', 0)),
            'executedQty': '0',
            'cumQty': '0',
            'cumQuote': '0',
            'timeInForce': kwargs.get('time_in_force', 'GTC'),
            'type': kwargs.get('order_type', 'LIMIT'),
            'reduceOnly': False,
            'closePosition': False,
            'side': kwargs.get('side', 'BUY'),
            'positionSide': kwargs.get('position_side', 'BOTH'),
            'stopPrice': '0',
            'workingType': 'CONTRACT_PRICE',
            'priceProtect': False,
            'origType': kwargs.get('order_type', 'LIMIT'),
            'updateTime': int(time.time() * 1000)
        }
    
    def cancel_order(self, **kwargs) -> Dict:
        """Mock cancel order."""
        return {
            'orderId': kwargs.get('order_id', random.randint(1000000, 9999999)),
            'symbol': kwargs.get('symbol', 'BTCUSDT'),
            'status': 'CANCELED'
        }
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get mock open orders."""
        return []
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """Mock set leverage."""
        return {
            'leverage': leverage,
            'maxNotionalValue': '1000000',
            'symbol': symbol
        }
    
    def set_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """Mock set margin type."""
        return {
            'code': 200,
            'msg': 'success'
        }
    
    def get_all_markets(self) -> Dict:
        """Get mock exchange info."""
        return {
            'timezone': 'UTC',
            'serverTime': int(time.time() * 1000),
            'symbols': [
                {
                    'symbol': 'BTCUSDT',
                    'status': 'TRADING',
                    'baseAsset': 'BTC',
                    'quoteAsset': 'USDT',
                    'pricePrecision': 2,
                    'quantityPrecision': 3
                },
                {
                    'symbol': 'ETHUSDT',
                    'status': 'TRADING',
                    'baseAsset': 'ETH',
                    'quoteAsset': 'USDT',
                    'pricePrecision': 2,
                    'quantityPrecision': 3
                }
            ]
        }

