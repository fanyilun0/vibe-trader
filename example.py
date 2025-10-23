#!/usr/bin/env python3
"""
Vibe Trader - 使用示例
演示如何单独使用各个模块
"""
import json
from config import Config
from aster_client import AsterClient
from data_aggregator import DataAggregator
from signal_generator import SignalGenerator
from indicators import TechnicalIndicators


def example_1_aster_client():
    """示例 1: 使用 Aster API 客户端"""
    print("\n" + "="*60)
    print("示例 1: Aster API 客户端")
    print("="*60)
    
    client = AsterClient()
    
    # 获取所有市场
    print("\n1. 获取所有可用市场:")
    try:
        markets = client.get_all_markets()
        print(f"   找到 {len(markets)} 个市场")
        if markets:
            print(f"   示例: {markets[0]}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 获取 BTC-PERP 行情
    print("\n2. 获取 BTC-PERP 行情:")
    try:
        ticker = client.get_ticker("BTC-PERP")
        print(f"   {json.dumps(ticker, indent=2)}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 获取 K 线数据
    print("\n3. 获取最近 10 根 1小时 K 线:")
    try:
        klines = client.get_klines(
            symbol="BTC-PERP",
            interval="1h",
            limit=10
        )
        print(f"   获取到 {len(klines)} 根 K 线")
        if klines:
            print(f"   最新: {klines[-1]}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 获取资金费率
    print("\n4. 获取资金费率:")
    try:
        funding = client.get_funding_rate("BTC-PERP")
        print(f"   {json.dumps(funding, indent=2)}")
    except Exception as e:
        print(f"   错误: {e}")


def example_2_technical_indicators():
    """示例 2: 计算技术指标"""
    print("\n" + "="*60)
    print("示例 2: 技术指标计算")
    print("="*60)
    
    # 模拟价格数据
    prices = [
        100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
        111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
        119, 121, 123, 122, 124, 126, 125, 127, 129, 128
    ]
    
    indicators = TechnicalIndicators()
    
    # 计算 EMA
    print("\n1. 计算 20 周期 EMA:")
    ema20 = indicators.calculate_ema(prices, 20)
    print(f"   最新 EMA(20): {ema20[-1]:.2f}")
    
    # 计算 RSI
    print("\n2. 计算 14 周期 RSI:")
    rsi14 = indicators.calculate_rsi(prices, 14)
    print(f"   最新 RSI(14): {rsi14[-1]:.2f}")
    
    # 计算 MACD
    print("\n3. 计算 MACD:")
    macd, signal, histogram = indicators.calculate_macd(prices)
    print(f"   MACD: {macd[-1]:.2f}")
    print(f"   Signal: {signal[-1]:.2f}")
    print(f"   Histogram: {histogram[-1]:.2f}")
    
    # 计算布林带
    print("\n4. 计算布林带:")
    upper, middle, lower = indicators.calculate_bollinger_bands(prices, 20, 2.0)
    print(f"   Upper: {upper[-1]:.2f}")
    print(f"   Middle: {middle[-1]:.2f}")
    print(f"   Lower: {lower[-1]:.2f}")


def example_3_data_aggregator():
    """示例 3: 数据聚合器"""
    print("\n" + "="*60)
    print("示例 3: 数据聚合器（获取完整市场数据）")
    print("="*60)
    
    aggregator = DataAggregator()
    
    print("\n获取市场数据...")
    try:
        # 只获取 BTC-PERP 数据
        market_data = aggregator.fetch_all_data(symbols=["BTC-PERP"])
        
        # 显示元数据
        metadata = market_data.get('metadata', {})
        print(f"\n元数据:")
        print(f"  运行时长: {metadata.get('minutes_trading', 0)} 分钟")
        print(f"  当前时间: {metadata.get('current_timestamp', 'N/A')}")
        print(f"  调用次数: {metadata.get('invocation_count', 0)}")
        
        # 显示 BTC 数据
        btc_data = market_data.get('coins_data', {}).get('BTC-PERP', {})
        if btc_data:
            print(f"\nBTC-PERP 数据:")
            print(f"  当前价格: {btc_data.get('current_price', 0):.2f}")
            print(f"  资金费率: {btc_data.get('funding_rate', 0):.6f}")
            
            intraday = btc_data.get('intraday', {})
            indicators = intraday.get('indicators', {})
            current = indicators.get('current', {})
            
            print(f"\n  短期指标:")
            print(f"    EMA(20): {current.get('ema20', 0):.2f}")
            print(f"    RSI(14): {current.get('rsi14', 0):.2f}")
            print(f"    MACD: {current.get('macd', 0):.2f}")
            print(f"    ADX: {current.get('adx', 0):.2f}")
        
        # 显示账户信息
        account = market_data.get('account_info', {})
        print(f"\n账户信息:")
        print(f"  账户价值: ${account.get('account_value', 0):.2f}")
        print(f"  可用余额: ${account.get('available_cash', 0):.2f}")
        print(f"  持仓数量: {len(account.get('positions', []))}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


def example_4_signal_generator():
    """示例 4: 信号生成（需要有效的 DeepSeek API 密钥）"""
    print("\n" + "="*60)
    print("示例 4: DeepSeek 信号生成")
    print("="*60)
    
    if not Config.DEEPSEEK_API_KEY or Config.DEEPSEEK_API_KEY == "":
        print("\n⚠️  需要设置 DEEPSEEK_API_KEY 环境变量")
        return
    
    print("\n正在获取市场数据...")
    aggregator = DataAggregator()
    market_data = aggregator.fetch_all_data(symbols=["BTC-PERP"])
    
    print("正在调用 DeepSeek 生成交易信号...")
    generator = SignalGenerator()
    
    try:
        signal = generator.get_signal(market_data)
        
        print(f"\n生成的信号:")
        print(f"  动作: {signal.get('action')}")
        print(f"  币种: {signal.get('symbol')}")
        print(f"  置信度: {signal.get('confidence', 0):.2%}")
        print(f"  入场价: {signal.get('entry_price')}")
        print(f"  止损价: {signal.get('stop_loss')}")
        print(f"  止盈价: {signal.get('take_profit')}")
        print(f"  杠杆: {signal.get('leverage')}x")
        print(f"\n分析理由:")
        print(f"  {signal.get('reasoning', 'N/A')[:300]}...")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """运行所有示例"""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + " " * 15 + "VIBE TRADER 使用示例" + " " * 22 + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    
    # 检查配置
    print("\n配置检查:")
    print(f"  DeepSeek API Key: {'已设置 ✓' if Config.DEEPSEEK_API_KEY else '未设置 ✗'}")
    print(f"  Aster API Key: {'已设置 ✓' if Config.ASTER_API_KEY else '未设置 ✗'}")
    print(f"  Aster API Secret: {'已设置 ✓' if Config.ASTER_API_SECRET else '未设置 ✗'}")
    
    # 运行示例
    try:
        # 示例 1: Aster 客户端（需要 API 密钥）
        if Config.ASTER_API_KEY:
            example_1_aster_client()
        else:
            print("\n⚠️  跳过示例 1: 需要 Aster API 密钥")
        
        # 示例 2: 技术指标（不需要 API）
        example_2_technical_indicators()
        
        # 示例 3: 数据聚合器（需要 Aster API）
        if Config.ASTER_API_KEY:
            example_3_data_aggregator()
        else:
            print("\n⚠️  跳过示例 3: 需要 Aster API 密钥")
        
        # 示例 4: 信号生成（需要两个 API）
        if Config.DEEPSEEK_API_KEY and Config.ASTER_API_KEY:
            user_input = input("\n是否运行示例 4 (DeepSeek 信号生成，会消耗 API 额度)? [y/N]: ")
            if user_input.lower() == 'y':
                example_4_signal_generator()
        else:
            print("\n⚠️  跳过示例 4: 需要 DeepSeek 和 Aster API 密钥")
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("示例运行完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

