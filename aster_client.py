"""
Aster DEX API Client
Handles all interactions with the Aster Perpetual Futures API (v3)
"""
import hmac
import hashlib
import time
import json
from typing import Dict, List, Optional, Any
import requests
from config import Config


class AsterClient:
    """Client for interacting with Aster DEX Futures API v3."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        passphrase: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the Aster client.
        
        Args:
            api_key: Aster API key (defaults to config)
            api_secret: Aster API secret (defaults to config)
            passphrase: Aster API passphrase (defaults to config)
            base_url: Base URL for Aster API (defaults to config)
        """
        self.api_key = api_key or Config.ASTER_API_KEY
        self.api_secret = api_secret or Config.ASTER_API_SECRET
        self.passphrase = passphrase or Config.ASTER_API_PASSPHRASE
        self.base_url = base_url or Config.ASTER_BASE_URL
        self.session = requests.Session()
    
    def _sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """
        Generate signature for signed API requests.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            path: API endpoint path
            body: Request body as JSON string
            
        Returns:
            Headers dict with signature
        """
        timestamp = str(int(time.time() * 1000))
        prehash_string = f"{timestamp}{method.upper()}{path}{body}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            prehash_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'API-KEY': self.api_key,
            'API-SIGN': signature,
            'API-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
        
        if self.passphrase:
            headers['API-PASSPHRASE'] = self.passphrase
        
        return headers
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Aster API.
        
        Args:
            method: HTTP method
            path: API endpoint path
            params: Query parameters
            data: Request body data
            signed: Whether request requires signature
            
        Returns:
            API response as dict
        """
        url = f"{self.base_url}{path}"
        
        body = ""
        if data:
            body = json.dumps(data)
        
        headers = {}
        if signed:
            headers = self._sign_request(method, path, body)
        else:
            headers = {'Content-Type': 'application/json'}
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=body if data else None,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Aster API request failed: {e}")
    
    # ========== Public Endpoints ==========
    
    def get_all_markets(self) -> List[Dict]:
        """Get all available markets/contracts."""
        return self._request("GET", "/api/v3/contracts")
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker information for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-PERP")
        """
        return self._request("GET", "/api/v3/ticker", params={"symbol": symbol})
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book depth.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of price levels to return
        """
        return self._request("GET", "/api/v3/depth", params={"symbol": symbol, "limit": limit})
    
    def get_klines(
        self,
        symbol: str,
        interval: str = "1m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[List]:
        """
        Get K-line/candlestick data.
        
        Args:
            symbol: Trading pair symbol
            interval: Interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w)
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Number of candles to return
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        return self._request("GET", "/api/v3/klines", params=params)
    
    def get_funding_rate(self, symbol: str) -> Dict:
        """
        Get current funding rate.
        
        Args:
            symbol: Trading pair symbol
        """
        return self._request("GET", "/api/v3/fundingRate", params={"symbol": symbol})
    
    # ========== Signed/Private Endpoints ==========
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        size: float,
        price: Optional[float] = None,
        leverage: Optional[int] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair symbol
            side: "BUY" or "SELL"
            order_type: "MARKET" or "LIMIT"
            size: Order size/quantity
            price: Order price (required for LIMIT orders)
            leverage: Leverage multiplier
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        data = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "size": size
        }
        
        if price is not None:
            data["price"] = price
        if leverage is not None:
            data["leverage"] = leverage
        if stop_loss is not None:
            data["stopLoss"] = stop_loss
        if take_profit is not None:
            data["takeProfit"] = take_profit
        
        return self._request("POST", "/api/v3/orders", data=data, signed=True)
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an open order.
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol
        """
        path = f"/api/v3/orders/{order_id}"
        return self._request("DELETE", path, params={"symbol": symbol}, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders.
        
        Args:
            symbol: Filter by symbol (optional)
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return self._request("GET", "/api/v3/openOrders", params=params, signed=True)
    
    def get_account_balances(self) -> Dict:
        """Get account balance information."""
        return self._request("GET", "/api/v3/accounts", signed=True)
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get current positions.
        
        Args:
            symbol: Filter by symbol (optional)
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return self._request("GET", "/api/v3/positions", params=params, signed=True)
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage multiplier (1-100)
        """
        data = {
            "symbol": symbol,
            "leverage": leverage
        }
        return self._request("POST", "/api/v3/leverage", data=data, signed=True)
    
    def set_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """
        Set margin type for a symbol.
        
        Args:
            symbol: Trading pair symbol
            margin_type: "ISOLATED" or "CROSSED"
        """
        data = {
            "symbol": symbol,
            "marginType": margin_type.upper()
        }
        return self._request("POST", "/api/v3/marginType", data=data, signed=True)

