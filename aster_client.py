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
    
    def _sign_request(self, method: str, path: str, params: str = "") -> Dict[str, str]:
        """
        Generate signature for signed API requests (Binance-style).
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            path: API endpoint path
            params: Query string parameters
            
        Returns:
            Headers dict with signature
        """
        timestamp = str(int(time.time() * 1000))
        
        # Build query string with timestamp
        query_string = f"timestamp={timestamp}"
        if params:
            query_string = f"{params}&{query_string}"
        
        # Sign the query string
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        return headers, f"{query_string}&signature={signature}"
    
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
        
        headers = {}
        query_string = ""
        
        if signed:
            # Build params string
            if params:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            else:
                param_str = ""
            
            if data:
                data_str = "&".join([f"{k}={v}" for k, v in data.items()])
                param_str = f"{param_str}&{data_str}" if param_str else data_str
            
            headers, query_string = self._sign_request(method, path, param_str)
            url = f"{url}?{query_string}"
        else:
            headers = {'Content-Type': 'application/json'}
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=None if signed else params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Aster API request failed: {e}")
    
    # ========== Public Endpoints ==========
    
    def get_all_markets(self) -> List[Dict]:
        """Get all available markets/contracts."""
        return self._request("GET", "/fapi/v1/exchangeInfo")
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker information for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
        """
        return self._request("GET", "/fapi/v1/ticker/24hr", params={"symbol": symbol})
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book depth.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of price levels to return
        """
        return self._request("GET", "/fapi/v1/depth", params={"symbol": symbol, "limit": limit})
    
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
        
        return self._request("GET", "/fapi/v1/klines", params=params)
    
    def get_funding_rate(self, symbol: str) -> Dict:
        """
        Get current funding rate.
        
        Args:
            symbol: Trading pair symbol
        """
        return self._request("GET", "/fapi/v1/fundingRate", params={"symbol": symbol})
    
    # ========== Signed/Private Endpoints ==========
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        position_side: str = "BOTH"
    ) -> Dict:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair symbol
            side: "BUY" or "SELL"
            order_type: "MARKET" or "LIMIT"
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            position_side: Position side (BOTH, LONG, SHORT)
        """
        data = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "positionSide": position_side
        }
        
        if price is not None:
            data["price"] = price
            data["timeInForce"] = time_in_force
        
        return self._request("POST", "/fapi/v1/order", data=data, signed=True)
    
    def cancel_order(self, symbol: str, order_id: Optional[int] = None, orig_client_order_id: Optional[str] = None) -> Dict:
        """
        Cancel an open order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            orig_client_order_id: Client order ID to cancel
        """
        params = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        if orig_client_order_id:
            params["origClientOrderId"] = orig_client_order_id
        
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders.
        
        Args:
            symbol: Filter by symbol (optional)
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)
    
    def get_account_balances(self) -> List[Dict]:
        """Get account balance information."""
        return self._request("GET", "/fapi/v2/balance", signed=True)
    
    def get_account_info(self) -> Dict:
        """Get account information including positions."""
        return self._request("GET", "/fapi/v2/account", signed=True)
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get current positions.
        
        Args:
            symbol: Filter by symbol (optional)
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return self._request("GET", "/fapi/v2/positionRisk", params=params, signed=True)
    
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
        return self._request("POST", "/fapi/v1/leverage", data=data, signed=True)
    
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
        return self._request("POST", "/fapi/v1/marginType", data=data, signed=True)

