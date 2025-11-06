#!/usr/bin/env python3
"""
获取指定日期的历史成交数据

此脚本独立运行，用于获取和保存指定日期范围内的历史成交记录。
保存的数据只包含交易记录，不包含PnL统计信息。
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_ingestion import create_binance_client
from config import Config


def fetch_trades_for_date(
    date_str: str,
    symbols: List[str],
    output_dir: str = "pnl/historical_trades"
) -> Dict[str, Any]:
    """
    获取指定日期的历史成交数据
    
    Args:
        date_str: 日期字符串，格式：YYYY-MM-DD
        symbols: 交易对列表
        output_dir: 输出目录
        
    Returns:
        包含交易记录的字典
    """
    print(f"\n{'='*80}")
    print(f"获取 {date_str} 的历史成交数据")
    print(f"{'='*80}")
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 创建Binance客户端
    print("\n连接到Binance API...")
    data_client = create_binance_client()
    
    # 解析日期
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        print(f"❌ 无效的日期格式: {date_str}，请使用 YYYY-MM-DD 格式")
        return None
    
    # 计算时间范围（当天 00:00:00 到 23:59:59）
    start_time = int(target_date.timestamp() * 1000)
    end_time = int((target_date + timedelta(days=1)).timestamp() * 1000) - 1
    
    print(f"时间范围: {target_date.strftime('%Y-%m-%d %H:%M:%S')} 到 "
          f"{(target_date + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取所有交易对的历史成交记录
    all_trades = []
    total_count = 0
    
    for symbol in symbols:
        print(f"\n正在获取 {symbol} 的成交记录...")
        
        try:
            # 获取历史成交（最多1000条）
            trades = data_client.get_my_trades(symbol, limit=1000)
            
            # 过滤出指定日期的交易
            filtered_trades = []
            for trade in trades:
                trade_time = trade.get('time', 0)
                
                # 检查是否在目标日期范围内
                if start_time <= trade_time <= end_time:
                    # 保留所有原始字段，添加可读时间
                    formatted_trade = {
                        'symbol': trade.get('symbol'),
                        'id': trade.get('id'),
                        'orderId': trade.get('orderId'),
                        'side': trade.get('side'),
                        'price': trade.get('price'),
                        'qty': trade.get('qty'),
                        'realizedPnl': trade.get('realizedPnl'),
                        'marginAsset': trade.get('marginAsset', 'USDT'),
                        'quoteQty': trade.get('quoteQty'),
                        'commission': trade.get('commission'),
                        'commissionAsset': trade.get('commissionAsset'),
                        'time': trade.get('time'),
                        'positionSide': trade.get('positionSide', 'BOTH'),
                        'buyer': trade.get('buyer', False),
                        'maker': trade.get('maker', False),
                        'time_readable': datetime.fromtimestamp(trade_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    filtered_trades.append(formatted_trade)
            
            if filtered_trades:
                all_trades.extend(filtered_trades)
                print(f"  ✅ 找到 {len(filtered_trades)} 条交易记录")
                total_count += len(filtered_trades)
            else:
                print(f"  ℹ️  没有找到交易记录")
            
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            continue
    
    if not all_trades:
        print(f"\n⚠️  {date_str} 没有找到任何交易记录")
        return None
    
    # 按时间排序（最新的在前）
    all_trades.sort(key=lambda x: x['time'], reverse=True)
    
    # 构建输出数据
    output_data = {
        'date': date_str,
        'fetch_time': datetime.now().isoformat(),
        'total_trades': len(all_trades),
        'symbols': symbols,
        'trades': all_trades
    }
    
    # 保存到文件
    filename = target_date.strftime('%Y%m%d') + '_trades.json'
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✅ 成功获取并保存 {total_count} 条交易记录")
    print(f"文件路径: {filepath}")
    print(f"{'='*80}\n")
    
    return output_data


def fetch_multiple_dates(
    start_date: str,
    days: int,
    symbols: List[str],
    output_dir: str = "pnl/historical_trades"
) -> List[Dict[str, Any]]:
    """
    获取多个日期的历史成交数据
    
    Args:
        start_date: 起始日期，格式：YYYY-MM-DD
        days: 往前追溯的天数
        symbols: 交易对列表
        output_dir: 输出目录
        
    Returns:
        所有日期的交易记录列表
    """
    results = []
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        print(f"❌ 无效的日期格式: {start_date}")
        return results
    
    print(f"\n{'='*80}")
    print(f"批量获取历史成交数据")
    print(f"起始日期: {start_date}")
    print(f"追溯天数: {days} 天")
    print(f"交易对: {', '.join(symbols)}")
    print(f"{'='*80}")
    
    for i in range(days):
        target_date = start - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        
        result = fetch_trades_for_date(date_str, symbols, output_dir)
        if result:
            results.append(result)
    
    print(f"\n{'='*80}")
    print(f"批量获取完成")
    print(f"成功: {len(results)}/{days} 天")
    print(f"{'='*80}\n")
    
    return results


def print_trades_summary(data: Dict[str, Any], limit: int = 10):
    """打印交易记录摘要"""
    if not data or 'trades' not in data:
        return
    
    trades = data['trades']
    
    print(f"\n交易记录摘要 (共 {len(trades)} 条，显示前 {min(limit, len(trades))} 条):")
    print("-" * 110)
    print(f"{'时间':<20} {'交易对':<12} {'方向':<6} {'价格':<12} {'数量':<12} {'手续费':<12} {'已实现盈亏':<12}")
    print("-" * 110)
    
    for trade in trades[:limit]:
        time_str = trade['time_readable']
        symbol = trade['symbol']
        side = "买入" if trade['side'] == "BUY" else "卖出"
        price = float(trade['price'])
        qty = float(trade['qty'])
        commission = float(trade['commission'])
        realized_pnl = float(trade['realizedPnl'])
        
        pnl_sign = "+" if realized_pnl >= 0 else ""
        
        print(f"{time_str:<20} {symbol:<12} {side:<6} "
              f"${price:<11,.2f} {qty:<12.6f} "
              f"${commission:<11.6f} {pnl_sign}${realized_pnl:<11.2f}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='获取历史成交数据')
    parser.add_argument('--date', '-d', help='指定日期 (格式: YYYY-MM-DD)，默认为今天')
    parser.add_argument('--days', '-n', type=int, default=1, help='往前追溯的天数，默认1天')
    parser.add_argument('--symbols', '-s', nargs='+', help='交易对列表，默认使用配置文件')
    parser.add_argument('--output', '-o', default='pnl/historical_trades', help='输出目录')
    parser.add_argument('--show', action='store_true', help='显示交易记录摘要')
    parser.add_argument('--limit', '-l', type=int, default=10, help='显示的记录数量')
    
    args = parser.parse_args()
    
    # 获取交易对列表
    if args.symbols:
        symbols = args.symbols
    else:
        try:
            symbols = Config.trading.SYMBOLS
        except Exception as e:
            print(f"❌ 无法从配置获取交易对: {e}")
            print("请使用 --symbols 参数指定交易对")
            return 1
    
    # 确定日期
    if args.date:
        start_date = args.date
    else:
        start_date = datetime.now().strftime('%Y-%m-%d')
    
    # 获取数据
    if args.days == 1:
        # 单个日期
        result = fetch_trades_for_date(start_date, symbols, args.output)
        
        if result and args.show:
            print_trades_summary(result, args.limit)
    else:
        # 多个日期
        results = fetch_multiple_dates(start_date, args.days, symbols, args.output)
        
        if results and args.show:
            for result in results:
                print(f"\n{'='*80}")
                print(f"日期: {result['date']}")
                print(f"{'='*80}")
                print_trades_summary(result, args.limit)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

