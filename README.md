# Vibe Trader - AI-Powered Perpetual Futures Trading Bot

An autonomous trading bot powered by DeepSeek LLM for trading perpetual futures on Aster DEX.

## 🌟 Features

- **AI-Powered Strategy**: Uses DeepSeek's `deepseek-reasoner` model for intelligent trade signal generation
- **Modular Architecture**: Clean separation of concerns (Data Aggregation, Signal Generation, Execution, Risk Management)
- **Comprehensive Risk Management**: Position sizing, dynamic leverage, mandatory stop-loss, drawdown protection
- **Multi-Asset Support**: Trade multiple perpetual futures simultaneously (BTC, ETH, SOL, etc.)
- **Paper Trading Mode**: Test strategies without risking real capital
- **Advanced Technical Analysis**: RSI, MACD, EMA, ATR, Bollinger Bands, and more

## 📋 Architecture

Based on the academic blueprint in "Architecting an LLM-Powered Agent for Automated Perpetuals Trading on the Aster DEX", this bot implements:

1. **Data Aggregator**: Fetches and normalizes market data from Aster DEX
2. **Signal Generation Core**: DeepSeek LLM analyzes data and generates trading signals
3. **Trade Execution Engine**: Executes trades with proper order management
4. **Risk Management Module**: Monitors positions and enforces risk controls

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- DeepSeek API key
- Aster DEX API credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/vibe-trader.git
cd vibe-trader

# Install dependencies
pip install -r requirements.txt

# Note: TA-Lib requires system libraries
# On macOS: brew install ta-lib
# On Ubuntu: sudo apt-get install libta-lib-dev
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Running the Bot

```bash
# Start in paper trading mode (recommended for testing)
python main.py

# Start in live trading mode (set PAPER_TRADING_MODE=false in .env)
python main.py --live
```

## 📊 Data Flow

```
Aster DEX API → Data Aggregator → Technical Indicators
                                          ↓
                                   Structured Prompt
                                          ↓
                                   DeepSeek LLM
                                          ↓
                                   Trading Signal (JSON)
                                          ↓
                               Risk Management Check
                                          ↓
                                   Execution Engine
                                          ↓
                                    Aster DEX API
```

## ⚠️ Risk Disclosure

This is an experimental trading bot powered by AI. Trading perpetual futures involves substantial risk of loss. Key considerations:

- **Model Risk**: LLMs can exhibit unpredictable behavior
- **Market Risk**: Crypto markets are highly volatile
- **Leverage Risk**: Perpetual futures amplify both gains and losses
- **Liquidation Risk**: Positions can be forcibly closed

**Only trade with capital you can afford to lose.**

## 🔧 Configuration Options

See `.env.example` for all configuration options. Key settings:

- `TRADING_SYMBOLS`: Comma-separated list of perpetual contracts
- `MAX_POSITION_SIZE_PERCENT`: Maximum position size as % of equity (default: 2%)
- `RISK_PER_TRADE_PERCENT`: Risk per trade as % of equity (default: 1%)
- `MAX_DRAWDOWN_PERCENT`: Maximum allowed drawdown (default: 10%)
- `LOOP_INTERVAL_SECONDS`: Strategy evaluation interval (default: 300s)

## 📝 Prompt Engineering

The bot's intelligence comes from its prompt structure (see `signal_generator.py`). The prompt includes:

- Role definition for the LLM
- Structured market data (prices, indicators, funding rates)
- Current portfolio state
- Chain-of-Thought reasoning instructions
- Enforced JSON output schema

## 🛠️ Development

### Project Structure

```
vibe-trader/
├── config.py              # Configuration management
├── main.py                # Main entry point
├── aster_client.py        # Aster DEX API client
├── data_aggregator.py     # Market data collection
├── signal_generator.py    # DeepSeek LLM integration
├── execution_engine.py    # Order execution
├── risk_manager.py        # Risk controls
├── indicators.py          # Technical indicators
└── utils/
    └── logger.py          # Logging utilities
```

## 📚 References

This implementation is based on research and best practices from:

- Academic paper: "Architecting an LLM-Powered Agent for Automated Perpetuals Trading"
- DeepSeek MoE Architecture & Reasoning capabilities
- Aster DEX API documentation
- Established trading bot frameworks (freqtrade, LLM_trader)

## 📄 License

MIT License - See LICENSE file for details

## ⚖️ Disclaimer

This software is provided "as is" without warranty of any kind. The authors are not responsible for any losses incurred through the use of this bot. Always conduct thorough testing and use proper risk management.

