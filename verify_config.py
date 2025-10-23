"""
配置验证脚本
检查 Aster API 配置是否正确，以及数据获取是否正常工作
"""
import sys
from config import Config
from aster_client import AsterClient


def verify_symbol_format():
    """验证交易对符号格式"""
    print("="*80)
    print("🔍 验证交易对符号格式")
    print("="*80)
    
    correct_formats = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    wrong_formats = ["BTC-PERP", "BTC-USDT", "BTCUSD", "btcusdt"]
    
    print("\n✅ 正确格式示例:")
    for symbol in correct_formats:
        print(f"   • {symbol}")
    
    print("\n❌ 错误格式示例:")
    for symbol in wrong_formats:
        print(f"   • {symbol}")
    
    print(f"\n📊 当前配置的交易对:")
    all_valid = True
    for symbol in Config.TRADING_SYMBOLS:
        symbol = symbol.strip()
        # 检查格式
        is_valid = (
            symbol.isupper() and  # 必须大写
            symbol.endswith("USDT") and  # 必须以 USDT 结尾
            "-" not in symbol and  # 不能包含连字符
            len(symbol) >= 6  # 至少 6 个字符
        )
        
        status = "✅" if is_valid else "❌"
        print(f"   {status} {symbol}")
        
        if not is_valid:
            all_valid = False
            if symbol.endswith("-PERP"):
                correct = symbol.replace("-PERP", "USDT")
                print(f"      → 建议改为: {correct}")
            elif symbol.endswith("-USDT"):
                correct = symbol.replace("-USDT", "USDT")
                print(f"      → 建议改为: {correct}")
    
    if all_valid:
        print("\n✅ 所有交易对格式正确！")
        return True
    else:
        print("\n❌ 发现格式错误，请修改 .env 文件中的 TRADING_SYMBOLS 配置")
        print("   正确示例: TRADING_SYMBOLS=BTCUSDT,ETHUSDT")
        return False


def test_api_connection():
    """测试 API 连接"""
    print("\n" + "="*80)
    print("🔌 测试 Aster API 连接")
    print("="*80)
    
    try:
        Config.validate()
        print("\n✅ API 配置验证通过")
    except ValueError as e:
        print(f"\n❌ API 配置错误: {e}")
        print("\n请检查 .env 文件，确保设置了以下变量:")
        print("   • ASTER_API_KEY")
        print("   • ASTER_API_SECRET")
        print("   • DEEPSEEK_API_KEY")
        return False
    
    print("\n正在测试 API 连接...")
    client = AsterClient()
    
    # 测试公开端点（不需要认证）
    test_symbol = Config.TRADING_SYMBOLS[0].strip()
    print(f"\n测试交易对: {test_symbol}")
    
    try:
        print(f"   ├─ 测试获取 K线数据...")
        klines = client.get_klines(test_symbol, interval="3m", limit=5)
        if klines and len(klines) > 0:
            print(f"   │  ✅ 成功获取 {len(klines)} 根K线")
            latest = klines[-1]
            close_price = float(latest[4])
            print(f"   │  最新收盘价: ${close_price:.2f}")
        else:
            print(f"   │  ❌ 未获取到数据")
            return False
    except Exception as e:
        print(f"   │  ❌ 失败: {e}")
        if "400" in str(e):
            print(f"   │  💡 提示: 符号格式可能不正确")
            print(f"   │     当前: {test_symbol}")
            if "-" in test_symbol:
                correct = test_symbol.split("-")[0] + "USDT"
                print(f"   │     建议: {correct}")
        return False
    
    try:
        print(f"   ├─ 测试获取资金费率...")
        funding = client.get_funding_rate(test_symbol)
        rate = funding.get('fundingRate', 'N/A')
        print(f"   │  ✅ 资金费率: {rate}")
    except Exception as e:
        print(f"   │  ⚠️  跳过: {e}")
    
    try:
        print(f"   └─ 测试获取订单簿...")
        order_book = client.get_order_book(test_symbol, limit=5)
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        print(f"      ✅ 买单: {len(bids)} 档, 卖单: {len(asks)} 档")
        if bids and asks:
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread = best_ask - best_bid
            print(f"      最佳买价: ${best_bid:.2f}, 最佳卖价: ${best_ask:.2f}")
            print(f"      买卖价差: ${spread:.2f}")
    except Exception as e:
        print(f"      ⚠️  跳过: {e}")
    
    print("\n✅ API 连接测试通过！")
    return True


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🛠️  VIBE TRADER 配置验证工具")
    print("="*80)
    print()
    
    # 步骤 1: 验证符号格式
    format_ok = verify_symbol_format()
    
    if not format_ok:
        print("\n" + "="*80)
        print("❌ 验证失败：请先修正交易对符号格式")
        print("="*80)
        print("\n修复步骤:")
        print("1. 打开 .env 文件")
        print("2. 找到 TRADING_SYMBOLS 配置项")
        print("3. 将格式修改为: TRADING_SYMBOLS=BTCUSDT,ETHUSDT")
        print("4. 保存文件并重新运行此脚本")
        print()
        sys.exit(1)
    
    # 步骤 2: 测试 API 连接
    api_ok = test_api_connection()
    
    if not api_ok:
        print("\n" + "="*80)
        print("❌ 验证失败：API 连接测试未通过")
        print("="*80)
        print("\n请检查:")
        print("1. API 密钥是否正确")
        print("2. 交易对符号格式是否正确")
        print("3. 网络连接是否正常")
        print()
        sys.exit(1)
    
    # 全部通过
    print("\n" + "="*80)
    print("✅ 所有验证通过！配置正确，可以开始运行 Vibe Trader")
    print("="*80)
    print("\n下一步:")
    print("• 纸上交易: python main.py")
    print("• 真实交易: python main.py --live (⚠️  风险自负)")
    print("• 测试数据: python test_data_fetch.py")
    print()


if __name__ == "__main__":
    main()

