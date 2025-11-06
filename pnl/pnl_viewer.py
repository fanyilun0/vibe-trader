#!/usr/bin/env python3
"""
PnL数据查看器

用于查看和分析每日盈亏数据的变化情况
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_pnl_data(date_str: str) -> Dict[str, Any]:
    """
    加载指定日期的PnL数据
    
    Args:
        date_str: 日期字符串，格式：YYYYMMDD
        
    Returns:
        PnL数据字典
    """
    pnl_dir = Path(__file__).parent
    filepath = pnl_dir / f"{date_str}.json"
    
    if not filepath.exists():
        print(f"❌ 文件不存在: {filepath}")
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_currency(value: float) -> str:
    """格式化货币"""
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


def print_summary(data: Dict[str, Any]):
    """打印每日摘要"""
    print("\n" + "=" * 80)
    print(f"📅 日期: {data['date']}")
    print("=" * 80)
    
    print(f"\n💰 账户变化:")
    print(f"  起始权益: ${data['start_equity']:,.2f}")
    print(f"  结束权益: ${data['end_equity']:,.2f}")
    equity_change = data['end_equity'] - data['start_equity']
    print(f"  权益变化: {format_currency(equity_change)} ({data['return_pct']:.2f}%)")
    
    print(f"\n📊 交易统计:")
    print(f"  已实现盈亏: {format_currency(data['realized_pnl'])}")
    print(f"  未实现盈亏: {format_currency(data['unrealized_pnl'])}")
    print(f"  累计手续费: ${data['commission']:.2f}")
    print(f"  净盈亏: {format_currency(data['net_pnl'])}")
    print(f"  总盈亏: {format_currency(data['total_pnl'])}")
    
    print(f"\n📈 操作统计:")
    print(f"  交易次数: {data['trades_count']}")
    print(f"  周期数: {data['cycles_count']}")
    print(f"  开仓次数: {data['positions_opened']}")
    print(f"  平仓次数: {data['positions_closed']}")
    print(f"  最后更新: {data['last_update']}")


def print_trade_snapshots(data: Dict[str, Any], limit: int = 10):
    """打印交易统计快照"""
    snapshots = data.get('trade_snapshots', [])
    
    if not snapshots:
        print("\n⚠️  没有交易统计快照")
        return
    
    print(f"\n📸 交易统计快照 (共 {len(snapshots)} 条，显示最近 {min(limit, len(snapshots))} 条):")
    print("-" * 80)
    
    # 显示最近的快照
    for snapshot in snapshots[-limit:]:
        timestamp = snapshot['timestamp']
        cycle = snapshot['cycle']
        realized_pnl = snapshot['realized_pnl']
        commission = snapshot['commission']
        net_pnl = snapshot['net_pnl']
        trades = snapshot['trades_count']
        total_pnl = snapshot['total_pnl']
        
        print(f"\n⏰ {timestamp} (周期 #{cycle})")
        print(f"  已实现盈亏: {format_currency(realized_pnl)}")
        print(f"  手续费: ${commission:.2f}")
        print(f"  净盈亏: {format_currency(net_pnl)}")
        print(f"  交易次数: {trades}")
        print(f"  总盈亏: {format_currency(total_pnl)}")


def print_historical_trades(data: Dict[str, Any], limit: int = 20):
    """打印历史成交记录"""
    trades = data.get('historical_trades', [])
    
    if not trades:
        print("\n⚠️  没有历史成交记录")
        return
    
    print(f"\n📋 历史成交记录 (共 {len(trades)} 条，显示最近 {min(limit, len(trades))} 条):")
    print("-" * 130)
    print(f"{'时间':<20} {'订单ID':<12} {'交易对':<12} {'方向':<6} {'价格':<12} {'数量':<12} {'手续费':<12} {'角色':<8} {'已实现盈亏':<12}")
    print("-" * 130)
    
    # 显示最近的成交记录
    for trade in trades[:limit]:
        # 支持两种格式：新格式（完整原始数据）和旧格式（格式化数据）
        time_str = trade.get('time_readable', '')
        if not time_str and 'time' in trade:
            # 如果没有 time_readable，尝试从 time 转换
            from datetime import datetime
            try:
                time_str = datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = str(trade.get('time', ''))
        
        order_id = trade.get('orderId', trade.get('order_id', 'N/A'))
        symbol = trade.get('symbol', 'N/A')
        side = trade.get('side', 'N/A')
        
        # 价格和数量可能是字符串或浮点数
        price_str = trade.get('price', '0')
        qty_str = trade.get('qty', trade.get('quantity', '0'))
        commission_str = trade.get('commission', '0')
        realized_pnl_str = trade.get('realizedPnl', trade.get('realized_pnl', '0'))
        
        try:
            price = float(price_str)
            quantity = float(qty_str)
            commission = float(commission_str)
            realized_pnl = float(realized_pnl_str)
        except (ValueError, TypeError):
            continue
        
        # 判断角色
        is_maker = trade.get('maker', trade.get('is_maker', False))
        role = "挂单方" if is_maker else "吃单方"
        
        # 方向显示
        side_display = "买入" if side == "BUY" else "卖出"
        
        print(f"{time_str:<20} {str(order_id):<12} {symbol:<12} {side_display:<6} "
              f"${price:<11,.2f} {quantity:<12.6f} "
              f"${commission:<11.6f} {role:<8} {format_currency(realized_pnl):<12}")


def compare_snapshots(data: Dict[str, Any]):
    """比较交易快照的变化"""
    snapshots = data.get('trade_snapshots', [])
    
    if len(snapshots) < 2:
        print("\n⚠️  快照数量不足，无法进行对比")
        return
    
    print(f"\n📈 交易快照变化趋势:")
    print("-" * 80)
    
    # 计算变化率
    first = snapshots[0]
    last = snapshots[-1]
    
    realized_pnl_change = last['realized_pnl'] - first['realized_pnl']
    commission_change = last['commission'] - first['commission']
    net_pnl_change = last['net_pnl'] - first['net_pnl']
    trades_change = last['trades_count'] - first['trades_count']
    
    print(f"  首次快照: {first['timestamp']} (周期 #{first['cycle']})")
    print(f"  最新快照: {last['timestamp']} (周期 #{last['cycle']})")
    print(f"  周期跨度: {last['cycle'] - first['cycle']} 个周期")
    print(f"\n  变化:")
    print(f"    已实现盈亏: {format_currency(realized_pnl_change)}")
    print(f"    累计手续费: {format_currency(commission_change)}")
    print(f"    净盈亏: {format_currency(net_pnl_change)}")
    print(f"    交易增加: {trades_change} 笔")
    
    # 计算平均每笔交易的盈亏
    if trades_change > 0:
        avg_pnl_per_trade = net_pnl_change / trades_change
        avg_commission_per_trade = commission_change / trades_change
        print(f"\n  平均每笔交易:")
        print(f"    净盈亏: {format_currency(avg_pnl_per_trade)}")
        print(f"    手续费: ${avg_commission_per_trade:.2f}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PnL数据查看器')
    parser.add_argument('date', nargs='?', help='日期 (格式: YYYYMMDD)，默认为今天')
    parser.add_argument('--trades', '-t', action='store_true', help='显示历史成交记录')
    parser.add_argument('--snapshots', '-s', action='store_true', help='显示交易统计快照')
    parser.add_argument('--compare', '-c', action='store_true', help='比较快照变化')
    parser.add_argument('--limit', '-l', type=int, default=20, help='显示的记录数量限制')
    parser.add_argument('--all', '-a', action='store_true', help='显示所有信息')
    
    args = parser.parse_args()
    
    # 默认使用今天的日期
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%Y%m%d')
    
    # 加载数据
    data = load_pnl_data(date_str)
    if data is None:
        return
    
    # 打印摘要（总是显示）
    print_summary(data)
    
    # 根据参数显示详细信息
    if args.all or args.snapshots:
        print_trade_snapshots(data, limit=args.limit)
    
    if args.all or args.compare:
        compare_snapshots(data)
    
    if args.all or args.trades:
        print_historical_trades(data, limit=args.limit)
    
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()

