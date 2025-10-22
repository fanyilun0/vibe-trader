It has been {minutes_trading} minutes since you started trading. The current time is {current_timestamp} and you've been invoked {invocation_count} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.
ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST
Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3‑minute intervals. If a coin uses a different interval, it is explicitly stated in that coin’s section.

CURRENT MARKET STATE FOR ALL COINS

ALL {COIN_SYMBOL_1} DATA
current_price = {current_price_1}, current_ema20 = {current_ema20_1}, current_macd = {current_macd_1}, current_rsi (7 period) = {current_rsi_7_period_1}
In addition, here is the latest {COIN_SYMBOL_1} open interest and funding rate for perps (the instrument you are trading):
Open Interest: Latest: {latest_open_interest_1} Average: {average_open_interest_1}
Funding Rate: {funding_rate_1}
Intraday series (by minute, oldest → latest):
Mid prices: [{mid_prices_list_1}]
EMA indicators (20‑period): [{ema20_list_1}]
MACD indicators: [{macd_list_1}]
RSI indicators (7‑Period): [{rsi_7_period_list_1}]
RSI indicators (14‑Period): [{rsi_14_period_list_1}]
Longer‑term context (4‑hour timeframe):
20‑Period EMA: {long_term_ema20_1} vs. 50‑Period EMA: {long_term_ema50_1}
3‑Period ATR: {long_term_atr3_1} vs. 14‑Period ATR: {long_term_atr14_1}
Current Volume: {long_term_current_volume_1} vs. Average Volume: {long_term_average_volume_1}
MACD indicators: [{long_term_macd_list_1}]
RSI indicators (14‑Period): [{long_term_rsi_14_period_list_1}]

... (为其他币种重复以上 {COIN_SYMBOL_N} 数据块) ...

HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {total_return_percent}%
Available Cash: {available_cash}
Current Account Value: {account_value}
Current live positions & performance: {list_of_position_dictionaries}
Sharpe Ratio: {sharpe_ratio}