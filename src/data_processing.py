"""
数据处理与特征工程管道 (Data Processing & Feature Engineering Pipeline)

负责将原始市场数据转换为结构化特征,包括:
1. 清洗和转换原始数据
2. 计算技术分析指标 (EMA, MACD, RSI, ATR)
3. 格式化数据为提示词所需格式
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import ta
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理与特征工程处理器"""
    
    @staticmethod
    def klines_to_dataframe(klines: List[List]) -> pd.DataFrame:
        """
        将K线数据转换为Pandas DataFrame
        
        Args:
            klines: 原始K线数据列表
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        if not klines:
            raise ValueError("K线数据为空")
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # 设置时间戳为索引
        df.set_index('timestamp', inplace=True)
        
        # 按时间升序排序 (关键!)
        df.sort_index(ascending=True, inplace=True)
        
        return df
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, window: int, column: str = 'close') -> pd.Series:
        """
        计算指数移动平均线 (EMA)
        
        Args:
            df: 数据DataFrame
            window: EMA周期
            column: 计算列名
            
        Returns:
            EMA序列
        """
        return ta.trend.EMAIndicator(close=df[column], window=window).ema_indicator()
    
    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        window_fast: int = 12,
        window_slow: int = 26,
        window_sign: int = 9
    ) -> Dict[str, pd.Series]:
        """
        计算MACD指标
        
        Args:
            df: 数据DataFrame
            window_fast: 快线周期
            window_slow: 慢线周期
            window_sign: 信号线周期
            
        Returns:
            包含macd, signal, diff的字典
        """
        macd = ta.trend.MACD(
            close=df['close'],
            window_slow=window_slow,
            window_fast=window_fast,
            window_sign=window_sign
        )
        
        return {
            'macd': macd.macd(),
            'signal': macd.macd_signal(),
            'diff': macd.macd_diff()
        }
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, window: int) -> pd.Series:
        """
        计算相对强弱指数 (RSI)
        
        Args:
            df: 数据DataFrame
            window: RSI周期
            
        Returns:
            RSI序列
        """
        return ta.momentum.RSIIndicator(close=df['close'], window=window).rsi()
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, window: int) -> pd.Series:
        """
        计算平均真实波幅 (ATR)
        
        Args:
            df: 数据DataFrame
            window: ATR周期
            
        Returns:
            ATR序列
        """
        return ta.volatility.AverageTrueRange(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=window
        ).average_true_range()
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame, timeframe: str = 'short') -> pd.DataFrame:
        """
        为DataFrame添加所有技术指标
        
        Args:
            df: 数据DataFrame
            timeframe: 时间框架 ('short' 或 'long')
            
        Returns:
            添加了指标的DataFrame
        """
        df = df.copy()
        
        # 计算中间价
        df['mid_price'] = (df['high'] + df['low']) / 2
        
        if timeframe == 'short':
            # 短期指标 (3分钟)
            df['ema_20'] = DataProcessor.calculate_ema(df, 20)
            
            macd_data = DataProcessor.calculate_macd(df)
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_diff'] = macd_data['diff']
            
            df['rsi_7'] = DataProcessor.calculate_rsi(df, 7)
            df['rsi_14'] = DataProcessor.calculate_rsi(df, 14)
            
        else:  # long
            # 长期指标 (4小时)
            df['ema_20'] = DataProcessor.calculate_ema(df, 20)
            df['ema_50'] = DataProcessor.calculate_ema(df, 50)
            
            df['atr_3'] = DataProcessor.calculate_atr(df, 3)
            df['atr_14'] = DataProcessor.calculate_atr(df, 14)
            
            macd_data = DataProcessor.calculate_macd(df)
            df['macd'] = macd_data['macd']
            
            df['rsi_14'] = DataProcessor.calculate_rsi(df, 14)
        
        # 删除NaN值
        df.dropna(inplace=True)
        
        return df
    
    @staticmethod
    def process_fear_and_greed_index(
        fear_greed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理恐惧贪婪指数数据
        
        Args:
            fear_greed_data: 原始恐惧贪婪指数数据
            
        Returns:
            处理后的恐惧贪婪指数特征字典
        """
        if not fear_greed_data:
            logger.warning("恐惧贪婪指数数据为空，使用默认中性值")
            return {
                'fear_greed_value': 50,
                'fear_greed_classification': 'Neutral'
            }
        
        return {
            'fear_greed_value': int(fear_greed_data.get('value', 50)),
            'fear_greed_classification': fear_greed_data.get('value_classification', 'Neutral')
        }
    
    @staticmethod
    def process_market_data(
        raw_data: Dict[str, Any],
        symbol: str
    ) -> Dict[str, Any]:
        """
        处理单个币种的市场数据并计算所有特征
        
        Args:
            raw_data: 原始市场数据
            symbol: 交易对符号
            
        Returns:
            处理后的特征字典
        """
        logger.info(f"处理 {symbol} 的市场数据")
        
        features = {'symbol': symbol}
        
        # 处理短期数据 (3分钟)
        short_df = DataProcessor.klines_to_dataframe(raw_data['short_term_klines'])
        short_df = DataProcessor.add_all_indicators(short_df, 'short')
        
        # 提取短期特征
        features['current_price'] = float(short_df['close'].iloc[-1])
        features['current_ema20'] = float(short_df['ema_20'].iloc[-1])
        features['current_macd'] = float(short_df['macd'].iloc[-1])
        features['current_rsi_7'] = float(short_df['rsi_7'].iloc[-1])
        
        # 短期时间序列 (列表形式)
        features['mid_prices_list'] = short_df['mid_price'].tolist()
        features['ema20_list'] = short_df['ema_20'].tolist()
        features['macd_list'] = short_df['macd'].tolist()
        features['rsi_7_period_list'] = short_df['rsi_7'].tolist()
        features['rsi_14_period_list'] = short_df['rsi_14'].tolist()
        
        # 处理长期数据 (4小时)
        long_df = DataProcessor.klines_to_dataframe(raw_data['long_term_klines'])
        long_df = DataProcessor.add_all_indicators(long_df, 'long')
        
        # 提取长期特征
        features['long_term_ema20'] = float(long_df['ema_20'].iloc[-1])
        features['long_term_ema50'] = float(long_df['ema_50'].iloc[-1])
        features['long_term_atr3'] = float(long_df['atr_3'].iloc[-1])
        features['long_term_atr14'] = float(long_df['atr_14'].iloc[-1])
        features['long_term_current_volume'] = float(long_df['volume'].iloc[-1])
        
        # 计算长期平均成交量
        features['long_term_average_volume'] = float(long_df['volume'].mean())
        
        # 长期时间序列
        features['long_term_macd_list'] = long_df['macd'].tolist()
        features['long_term_rsi_14_period_list'] = long_df['rsi_14'].tolist()
        
        # 处理持仓量数据
        if raw_data.get('open_interest') and isinstance(raw_data['open_interest'], dict):
            features['latest_open_interest'] = float(raw_data['open_interest'].get('openInterest', 0))
        else:
            features['latest_open_interest'] = 0.0
        
        # 计算平均持仓量
        if raw_data.get('open_interest_hist') and isinstance(raw_data['open_interest_hist'], list) and len(raw_data['open_interest_hist']) > 0:
            oi_values = [float(item.get('sumOpenInterest', 0)) for item in raw_data['open_interest_hist'] if isinstance(item, dict)]
            if oi_values:
                features['average_open_interest'] = float(np.mean(oi_values))
            else:
                features['average_open_interest'] = features['latest_open_interest']
        else:
            features['average_open_interest'] = features['latest_open_interest']
        
        # 处理资金费率
        if raw_data.get('funding_rate') and isinstance(raw_data['funding_rate'], list) and len(raw_data['funding_rate']) > 0:
            features['funding_rate'] = float(raw_data['funding_rate'][0].get('fundingRate', 0))
        else:
            features['funding_rate'] = 0.0
        
        # 数据验证
        DataProcessor.validate_features(features)
        
        return features
    
    @staticmethod
    def validate_features(features: Dict[str, Any]) -> None:
        """
        验证特征数据的完整性和有效性
        
        Args:
            features: 特征字典
            
        Raises:
            ValueError: 如果数据无效
        """
        # 检查关键字段是否存在
        required_fields = [
            'current_price', 'current_ema20', 'current_macd', 'current_rsi_7',
            'mid_prices_list', 'ema20_list', 'macd_list',
            'long_term_ema20', 'long_term_ema50'
        ]
        
        for field in required_fields:
            if field not in features:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 检查数值字段是否包含NaN或Infinity
        numeric_fields = [
            'current_price', 'current_ema20', 'current_macd', 'current_rsi_7',
            'long_term_ema20', 'long_term_ema50', 'latest_open_interest', 'funding_rate'
        ]
        
        for field in numeric_fields:
            value = features.get(field)
            if value is not None and (np.isnan(value) or np.isinf(value)):
                raise ValueError(f"字段 {field} 包含无效值: {value}")
        
        # 检查列表字段是否为空
        list_fields = ['mid_prices_list', 'ema20_list', 'macd_list']
        
        for field in list_fields:
            if not features.get(field):
                raise ValueError(f"列表字段 {field} 为空")
        
        logger.debug(f"特征验证通过,共 {len(features)} 个字段")
    
    @staticmethod
    def process_account_data(
        account_data: Dict[str, Any],
        start_balance: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        处理账户数据并计算表现指标
        
        Args:
            account_data: 原始账户数据
            start_balance: 起始余额 (用于计算收益率)
            
        Returns:
            处理后的账户特征
        """
        logger.info("处理账户数据")
        
        features = {}
        
        # 基本账户信息
        features['available_cash'] = account_data.get('available_balance', 0)
        features['account_value'] = account_data.get('total_wallet_balance', 0)
        
        # 计算总收益率
        if start_balance and start_balance > 0:
            total_return = (features['account_value'] - start_balance) / start_balance
            features['total_return_percent'] = total_return * 100
        else:
            features['total_return_percent'] = 0.0
        
        # 处理持仓信息
        positions = []
        for pos in account_data.get('positions', []):
            # 获取清算价格（如果API返回为0则计算）
            liquidation_price = pos.get('liquidation_price', 0)
            
            # 如果API返回的清算价格为0或无效，使用简化公式计算
            if liquidation_price == 0 and pos['entry_price'] > 0 and pos['leverage'] > 0:
                entry_price = pos['entry_price']
                leverage = pos['leverage']
                position_amt = pos['position_amt']
                
                # 判断持仓方向：正数为多头，负数为空头
                if position_amt > 0:  # 多头
                    # 多仓: 强平价 = 开仓价 * (1 - 0.9 / 杠杆)
                    liquidation_price = entry_price * (1 - 0.9 / leverage)
                elif position_amt < 0:  # 空头
                    # 空仓: 强平价 = 开仓价 * (1 + 0.9 / 杠杆)
                    liquidation_price = entry_price * (1 + 0.9 / leverage)
                
                logger.debug(f"计算 {pos['symbol']} 清算价格: {liquidation_price:.2f} (入场价={entry_price}, 杠杆={leverage}x)")
            
            position_dict = {
                'symbol': pos['symbol'],
                'quantity': abs(pos['position_amt']),  # 转换为绝对值
                'position_amt': pos['position_amt'],  # 保留原始值（多头为正，空头为负）
                'entry_price': pos['entry_price'],
                'current_price': pos['mark_price'],
                'mark_price': pos['mark_price'],  # 添加mark_price字段
                'liquidation_price': liquidation_price,  # 清算价格（计算或API返回）
                'unrealized_pnl': pos['unrealized_profit'],
                'leverage': pos['leverage'],
                'position_side': pos['position_side'],
                # 订单相关字段（从持仓元数据或状态管理器获取）
                'sl_oid': pos.get('sl_oid', -1),  # 止损订单ID
                'tp_oid': pos.get('tp_oid', -1),  # 止盈订单ID
                'entry_oid': pos.get('entry_oid', -1),  # 入场订单ID
                'wait_for_fill': pos.get('wait_for_fill', False),  # 等待成交标志
            }
            
            # 计算名义价值和风险
            notional_value = abs(pos['position_amt']) * pos['mark_price']
            position_dict['notional_usd'] = notional_value
            position_dict['risk_usd'] = notional_value / pos['leverage'] if pos['leverage'] > 0 else 0
            
            positions.append(position_dict)
        
        features['list_of_position_dictionaries'] = positions
        
        return features


def create_data_processor() -> DataProcessor:
    """
    创建数据处理器实例
    
    Returns:
        DataProcessor实例
    """
    return DataProcessor()

