

# **Architecting an LLM-Powered Agent for Automated Perpetuals Trading on the Aster DEX**

## **Introduction: The Emergence of Generative AI as a Core Trading Engine**

The landscape of automated trading is undergoing a fundamental transformation, shifting from rigid, rule-based algorithms to dynamic, reasoning-based autonomous agents. This evolution is catalyzed by the maturation of Large Language Models (LLMs), which serve as the cognitive core for these new systems. Models such as DeepSeek are capable of processing heterogeneous data streams—spanning structured market data to unstructured news and sentiment—to generate complex, context-aware trading strategies.1 This represents a paradigm shift from algorithmic to "agentic" trading, where the system's primary directive is not to follow a predefined set of if-then statements, but to analyze, reason, and act based on a holistic understanding of the market environment.  
This technological advance finds a powerful synergy with the world of Decentralized Finance (DeFi). The open, permissionless, and programmatically accessible nature of platforms like the Aster Decentralized Exchange (DEX) provides an ideal execution venue for these AI-driven agents.3 The availability of public, albeit sometimes raw, Application Programming Interfaces (APIs) forms the critical bridge, enabling the LLM's strategic output to be translated into tangible market actions.  
This report provides a comprehensive architectural and implementation blueprint for constructing an automated trading agent designed to operate on the Aster DEX. It begins with a technical dissection of the DeepSeek model family, justifying its selection as the reasoning engine. It then offers a deep-dive analysis of the Aster DEX API for perpetual futures, consolidating fragmented documentation into an actionable guide. Subsequently, a modular software architecture is proposed, integrating the AI core with the execution venue. Finally, the report concludes with a critical examination of the novel risk management challenges inherent in deploying such an autonomous system. The intended audience for this document is a developer or quantitative analyst with a strong programming and financial background.

## **Part I: The Reasoning Engine \- A Technical Dissection of the DeepSeek Model**

### **Architectural Foundations: Why DeepSeek is Suited for High-Frequency Analysis**

The selection of an LLM for a trading agent is predicated not only on its reasoning capabilities but also on its operational efficiency. The economic viability of a system that must frequently re-evaluate market conditions is a direct consequence of the model's underlying architecture. A high volume of API calls is necessary, and the computational cost per query can quickly become prohibitive with traditional dense LLM architectures.6 DeepSeek's design directly addresses this challenge, making it uniquely suitable for this application.

#### **Mixture-of-Experts (MoE) Framework**

The cornerstone of DeepSeek's efficiency is its Mixture-of-Experts (MoE) architecture.6 Unlike dense models that activate all parameters for every inference task, an MoE model routes a given input to a small, specialized subset of its parameters, or "experts".7 This sparse activation means that for any single query, only a fraction of the model's total parameters are engaged. For example, one of DeepSeek's large models may have over 600 billion total parameters but only activate around 37 billion for a specific task.8 This architectural choice drastically reduces the computational load and associated costs during inference, a critical factor for a trading bot that may query the LLM at regular intervals.6 The reported operational cost savings, potentially as high as 95% compared to competitors for certain tasks, are not merely an incremental improvement; they are the enabling factor that makes a continuously-running LLM-based trading agent economically feasible for individuals and small firms.8

#### **Multi-Head Latent Attention (MLA)**

DeepSeek further enhances its efficiency through Multi-Head Latent Attention (MLA), an optimization of the standard transformer attention mechanism.6 MLA is designed to reduce memory overhead and computational demands during inference, allowing the model to process longer contexts and more complex data relationships without significant performance degradation.6 For a trading agent, this is crucial for analyzing extensive historical market data or incorporating a wide array of technical indicators and sentiment signals into a single prompt.

#### **Open-Weight Philosophy**

DeepSeek's "open-weight" approach, where model parameters are publicly shared, fosters a more transparent and collaborative ecosystem compared to closed-source alternatives.10 While usage conditions may differ from typical open-source software, the availability of model weights allows for deeper community analysis, enables more sophisticated local deployments, and builds trust in the model's capabilities.11

### **Model Selection for Quantitative Tasks: deepseek-reasoner vs. deepseek-chat**

DeepSeek provides two primary models via its API: deepseek-chat, a generalist model, and deepseek-reasoner, a specialist model designed for advanced logical tasks.12 The deepseek-chat model corresponds to the non-thinking mode of the latest DeepSeek versions, while deepseek-reasoner activates the "thinking" mode, which is optimized for complex problem-solving.13  
The training data and methodology behind these models underscore their distinct purposes. The development of advanced versions like DeepSeek-V3 involved extensive pre-training on multilingual corpora with a high ratio of mathematical and programming content.10 This foundation was then refined through Supervised Finetuning (SFT) on millions of reasoning samples (math, coding, logic) and Reinforcement Learning (RL) phases to align the model's output with human preferences for accuracy and logical consistency.6  
For the task of generating trading strategies—a process that is fundamentally a data-driven, logical reasoning challenge—the deepseek-reasoner model is the unequivocally superior choice. Its architecture and training are explicitly tailored for the kind of complex analysis required to interpret market data, weigh multiple factors, and formulate a coherent trade plan.12

| Table 1: DeepSeek Model Comparison for Quantitative Trading |  |  |  |  |  |  |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Model Name** | **Primary Use Case** | **Key Architectural Feature** | **Training Data Focus** | **Cost per Million Tokens (Input/Output)** | **Recommended Temperature** | **Justification for Trading Agent** |
| deepseek-chat | General conversational tasks, creative writing, simple Q\&A 12 | Non-thinking mode of V3.2-Exp 13 | Broad, general-purpose text and dialogue | Lower | $1.0 \- 1.5$ | Unsuitable; lacks the specialized reasoning capabilities required for complex financial analysis. |
| deepseek-reasoner | Advanced reasoning, math, coding, and logical problem-solving 12 | Thinking mode of V3.2-Exp, optimized for CoT 13 | Math, programming, logic, and reasoning data 10 | Higher | $0.0 \- 0.5$ | **Optimal Choice.** Specifically trained and architected for the logical, data-driven analysis needed to generate robust trading signals. The use of a low temperature ensures more deterministic and repeatable outputs. |

### **Generative Capabilities for "Formulaic Alphas"**

The application of LLMs to financial market analysis is a well-established field of research and practice.16 These models excel at processing vast quantities of both unstructured data (news articles, social media sentiment, corporate filings) and structured data (price, volume, technical indicators) to extract actionable insights.16  
Recent academic work has demonstrated a framework where a prompt-based LLM is used to automate the generation of "formulaic alphas"—mathematical expressions or logical rules that identify trading signals within financial data.20 In this approach, the LLM is provided with historical stock features, technical indicators, and sentiment scores, and is prompted to generate novel alpha factors. These LLM-generated alphas are then used as inputs for predictive models, significantly improving forecasting accuracy.20 This proves that a model like DeepSeek can be prompted not merely for a binary "buy" or "sell" recommendation, but for a complete, reasoned trading hypothesis with defined parameters, forming the basis of a sophisticated trading strategy.

## **Part II: The Execution Venue \- A Developer's Guide to the Aster Perpetual DEX API**

### **Platform Mechanics for Algorithmic Traders**

Aster has emerged as a next-generation decentralized exchange for perpetual futures and spot markets, built on the BNB Chain and supported by prominent entities including YZi Labs, which is linked to Binance's founder.3 The platform's core value proposition is to merge the efficiency and feature set of a centralized exchange (CEX) with the non-custodial principles of DeFi.25  
For algorithmic traders, Aster offers several critical features:

* **Pro Mode:** An advanced trading interface with a professional, CEX-like order book, providing the granular control necessary for automated strategies.3  
* **Low Fees:** The platform boasts a competitive fee structure, which is a significant consideration for high-frequency strategies.3  
* **Expanded Asset Offerings:** Aster supports 24/7 trading of stock perpetuals, allowing traders to gain exposure to traditional equity markets within the crypto ecosystem.4  
* **Multi-Chain Liquidity:** The DEX aggregates liquidity across multiple major blockchains, including BNB Chain, Ethereum, Solana, and Arbitrum, which can lead to reduced slippage and better execution.4  
* **Capital Efficiency:** A standout feature is the ability to use yield-bearing assets, such as liquid staking tokens (asBNB) and yield-generating stablecoins (USDF), as collateral.3 This allows capital locked as margin to continue earning yield, a significant advantage for any trading bot.

### **Navigating the Aster API Landscape**

A notable challenge for developers is the state of Aster's API documentation. Unlike platforms with polished developer portals, Aster's primary source of technical truth resides in its asterdex/api-docs GitHub repository.29 This repository contains raw markdown files that outline the API endpoints and their parameters.  
This documentation-light approach, combined with the platform's positioning as a direct competitor to Hyperliquid (a known hub for algorithmic traders), suggests a deliberate focus.3 The platform's infrastructure and developer ecosystem appear to be engineered to attract professional and semi-professional algorithmic traders who are comfortable working with raw technical specifications and building their own integrations. While this presents a steeper initial learning curve, it implies that the underlying API is likely robust and designed for the kind of high-performance, automated trading this report outlines.  
To bridge the documentation gap, community-built implementations serve as invaluable resources. Projects such as asteraiagent and kukapay-mcp-servers provide working code examples that reveal the structure of both public and signed API calls, effectively acting as de-facto documentation and practical implementation guides.31

### **Interfacing with the Aster Futures API (v3)**

Analysis of community projects and the official GitHub repository provides a clear path for interfacing with the Aster Futures API.

#### **Base URL and Authentication**

The base URL for the futures API is https://fapi.asterdex.com.31 Interaction with private endpoints requires signed requests. The authentication mechanism involves an API Key, an API Secret, and an optional passphrase. The asteraiagent project details the credential resolution logic, which forms the basis for a custom implementation.31 The signing process typically involves creating an HMAC-SHA256 signature of a prehash string composed of the request timestamp, HTTP method, request path, and request body, a common pattern among crypto exchanges.33

#### **Public and Signed Endpoints**

The following table consolidates information from the asterdex/api-docs repository and the asteraiagent project to provide a quick-reference guide to the most essential API endpoints for a trading bot.29

| Table 2: Aster Futures API Endpoint Reference (v3) |  |  |  |  |
| :---- | :---- | :---- | :---- | :---- |
| **Functionality** | **Endpoint Path** | **HTTP Method** | **Key Parameters** | **Signed/Public** |
| Get All Markets | /api/v3/contracts | GET | \- | Public |
| Get Ticker Info | /api/v3/ticker | GET | symbol | Public |
| Get Order Book | /api/v3/depth | GET | symbol, limit | Public |
| Get K-Line Data | /api/v3/klines | GET | symbol, interval, startTime, endTime, limit | Public |
| Get Funding Rate | /api/v3/fundingRate | GET | symbol | Public |
| Place Order | /api/v3/orders | POST | symbol, side, type, size, price, leverage | Signed |
| Cancel Order | /api/v3/orders/{orderId} | DELETE | orderId, symbol | Signed |
| Get Open Orders | /api/v3/openOrders | GET | symbol | Signed |
| Get Account Balances | /api/v3/accounts | GET | \- | Signed |
| Get Positions | /api/v3/positions | GET | symbol | Signed |
| Set Leverage | /api/v3/leverage | POST | symbol, leverage | Signed |
| Set Margin Type | /api/v3/marginType | POST | symbol, marginType | Signed |

## **Part III: System Architecture and Implementation Blueprint**

### **A Modular Framework for an AI Trading Bot**

Drawing inspiration from the modular design of established open-source trading bots like freqtrade and the LLM-specific LLM\_trader, a robust architecture should be built on the principle of separation of concerns.35 This approach enhances maintainability, testability, and scalability.

* **Component 1: Data Aggregator:** This module serves as the sole interface for external data sources. It is responsible for making API calls to Aster to fetch market data (k-lines, order book depth, funding rates) and can be extended to pull from other sources, such as sentiment analysis APIs for a Fear & Greed Index.36  
* **Component 2: Signal Generation Core (The DeepSeek Agent):** This is the system's cognitive center. It receives structured data from the Aggregator, constructs a detailed prompt, and queries the DeepSeek deepseek-reasoner API. Its primary responsibility is to parse the structured JSON response from the LLM, which contains the trading signal.  
* **Component 3: Trade Execution Engine:** This module acts on the signal provided by the AI core. It receives a standardized command (e.g., a JSON object with action, symbol, stop-loss, etc.) and translates it into the specific parameters required by the Aster API's place\_order endpoint. It also manages the lifecycle of an order, including subsequent placement of stop-loss and take-profit orders.  
* **Component 4: Risk Management & Monitoring Module:** This critical component operates independently and continuously. It monitors open positions, account equity, and overall market volatility. Crucially, it possesses the authority to override signals from the AI core. For instance, it can execute a market close of all positions if a predefined maximum drawdown threshold for the account is breached, acting as a final safeguard.

### **Advanced Prompt Engineering for Trading Signals**

In an LLM-agent architecture, the traditional, hard-coded trading logic is abstracted. Instead of writing explicit conditional rules in code, the developer's primary task becomes crafting a highly structured, comprehensive prompt that gives the LLM complete situational awareness. The quality of this prompt directly determines the performance of the trading strategy. The prompt itself effectively becomes the new source code for the trading algorithm.

#### **Structuring the Prompt**

The prompt must be designed as a structured instructional task, guiding the LLM through a logical analysis.20 It should include:

1. **Role Definition:** Begin by assigning a role to the model (e.g., "You are an expert quantitative analyst specializing in high-frequency trading of perpetual futures...").  
2. **Data Provision:** Supply all relevant data in a clean, machine-readable format. This data schema is the most critical data structure in the system, standardizing the interface between the data aggregator and the AI core.  
3. **Chain-of-Thought (CoT) Instruction:** Explicitly instruct the model to "think step-by-step" or "provide your reasoning before the final decision".12 This forces the model to articulate its analytical process, which not only improves the quality and logical consistency of the output but also provides an invaluable audit trail for debugging and strategy refinement.  
4. **Enforced JSON Output:** The prompt must conclude with a strict instruction to return the final output *only* in a specific JSON format, providing the schema in the prompt itself.1 This is non-negotiable for automation, as it ensures the LLM's response is machine-readable and eliminates the need for fragile and error-prone natural language parsing.

| Table 3: Example Input Data Schema for LLM Prompt |  |
| :---- | :---- |
| \`\`\`json |  |
| { |  |
| "market\_context": { |  |
| "symbol": "BTC-PERP", |  |
| "klines\_1h": \[... \], | // Array of last 100 1-hour OHLCV candles |
| "order\_book\_snapshot": { "bids": \[... \], "asks": \[... \] }, |  |
| "funding\_rate\_8h": 0.0001, |  |
| "volatility\_atr\_14": 150.75 |  |
| }, |  |
| "technical\_indicators": { | // Based on LLM\_trader indicators 36 |
| "RSI\_14": 45.2, |  |
| "MACD\_12\_26\_9": { "macd": \-25.3, "signal": \-30.1, "hist": 4.8 }, |  |
| "BollingerBands\_20\_2": { "upper": 70150.0, "middle": 69500.0, "lower": 68850.0 }, |  |
| "VWAP": 69550.4, |  |
| "ADX\_14": 22.5 |  |
| }, |  |
| "sentiment\_data": { |  |
| "fear\_and\_greed\_index": 55 |  |
| }, |  |
| "current\_portfolio\_state": { |  |
| "position\_open": false, |  |
| "account\_equity": 10000.0, |  |
| "available\_collateral": 10000.0 |  |
| } |  |
| } |  |
| \`\`\` |  |

An example concluding instruction would be: "Based on all the data provided, determine the optimal trading action. Provide your analysis step-by-step. Your final output must be only a JSON object matching this exact schema: {'action': 'LONG'|'SHORT'|'HOLD', 'reasoning': '\<Your detailed step-by-step analysis\>', 'entry\_price': float|null, 'stop\_loss': float|null, 'take\_profit': float|null}."

### **Core Python Implementation Snippets**

#### **Connecting to the DeepSeek API**

The DeepSeek API is compatible with the OpenAI SDK, simplifying integration. The connection is established by overriding the base\_url and providing a DeepSeek-generated API key.12

Python

import os  
from openai import OpenAI

client \= OpenAI(  
    api\_key=os.environ.get("DEEPSEEK\_API\_KEY"),  
    base\_url="https://api.deepseek.com/v1"  
)

\#... construct messages payload with structured data...

response \= client.chat.completions.create(  
    model="deepseek-reasoner",  
    messages=messages,  
    \# Enforce JSON output if supported by the model version  
    \# response\_format={"type": "json\_object"},   
    temperature=0.2 \# Low temperature for deterministic analysis  
)

\#... parse response.choices.message.content as JSON...

#### **Aster API Client Structure**

A Python class should encapsulate all interactions with the Aster API, handling request signing and endpoint communication.

Python

import hmac  
import hashlib  
import time  
import requests

class AsterClient:  
    def \_\_init\_\_(self, api\_key, api\_secret, base\_url="https://fapi.asterdex.com"):  
        self.api\_key \= api\_key  
        self.api\_secret \= api\_secret  
        self.base\_url \= base\_url

    def \_sign\_request(self, method, path, body=""):  
        timestamp \= str(int(time.time() \* 1000))  
        prehash\_string \= f"{timestamp}{method.upper()}{path}{body}"  
        signature \= hmac.new(  
            self.api\_secret.encode('utf-8'),  
            prehash\_string.encode('utf-8'),  
            hashlib.sha256  
        ).hexdigest()  
          
        headers \= {  
            'API-KEY': self.api\_key,  
            'API-SIGN': signature,  
            'API-TIMESTAMP': timestamp,  
            'Content-Type': 'application/json'  
        }  
        return headers

    def place\_order(self, symbol, side, order\_type, size):  
        path \= "/api/v3/orders"  
        body \= {  
            "symbol": symbol,  
            "side": side,  
            "type": order\_type,  
            "size": size  
        }  
        \#... implementation to make a signed POST request...

#### **Main Execution Loop**

The bot's operation is governed by a continuous loop that orchestrates the actions of its modules.

Python

def main\_loop():  
    while True:  
        \# 1\. Data Aggregator  
        market\_data \= data\_aggregator.fetch\_all\_data("BTC-PERP")  
          
        \# 2\. Signal Generation Core  
        trade\_signal \= signal\_generator.get\_signal(market\_data)  
          
        \# 3\. Risk Management Pre-Check  
        if risk\_manager.is\_trade\_permissible(trade\_signal):  
            \# 4\. Trade Execution Engine  
            execution\_engine.execute(trade\_signal)  
          
        \# 5\. Risk Management Monitoring  
        risk\_manager.monitor\_positions()  
          
        time.sleep(300) \# e.g., re-evaluate every 5 minutes

## **Part IV: Robust Risk Management and Advanced Considerations**

### **Programmatic Risk Controls for an Autonomous System**

In a leveraged trading environment, particularly with perpetual futures, robust risk management is paramount. The amplification of both gains and losses means that a single adverse trade can lead to rapid, significant losses or even full liquidation of a position.37 For an autonomous agent, these controls cannot be discretionary; they must be programmatically enforced.  
This introduces a new layer of abstracted risk beyond traditional market and liquidity concerns.38 The system's performance is now subject to **Model Risk**, where the LLM may exhibit unpredictable behavior or biases from its training data, and **Prompt Risk**, where subtle changes to the prompt could drastically alter the agent's strategy. The risk management module must therefore account for both financial and model-specific failure modes.

* **Position Sizing:** A fixed-fractional risk model is essential. The position size for any given trade should be calculated based on the account's total equity, a predefined risk percentage per trade (e.g., 1-2%), and the distance to the stop-loss level.39 This ensures that no single loss can catastrophically impact the account.  
* **Dynamic Leverage Control:** The agent should not use a static, high leverage setting. A more robust approach is to adjust leverage dynamically based on market volatility, often measured by the Average True Range (ATR). In periods of high volatility, leverage should be programmatically reduced to mitigate the risk of liquidation from sharp price swings.  
* **Mandatory Stop-Loss:** The Trade Execution Engine must be hard-coded to reject any trade signal from the LLM that does not include a valid stop-loss price. Every executed market order must be immediately followed by API calls to place corresponding stop-loss and take-profit orders on the exchange.40  
* **Funding Rate Awareness:** The cost of holding a position can significantly impact profitability. The Data Aggregator must fetch funding rate data, which should be included in the prompt to the LLM. The prompt should instruct the model to consider this cost, penalizing strategies that would hold a position against a high negative funding rate for an extended period.37

### **Challenges in Backtesting and Simulation**

Traditional backtesting relies on the deterministic nature of an algorithm; given the same historical data, it will produce the exact same sequence of trades every time. LLMs, however, are not fully deterministic. Even with a temperature set to 0, slight variations in the model or its underlying infrastructure can lead to different nuances in its reasoning. This makes true, repeatable backtesting a significant challenge.  
The most viable method for strategy validation is therefore a prolonged period of **forward-testing simulation**. The bot should be run in a live environment, connected to real-time market data, but executing trades in a paper trading account or by logging them to a database without actual execution. This approach tests the agent's performance against real, unfolding market conditions and provides a more realistic assessment of its viability.

### **Operational Risks of LLM Agents: The "Black Box" Dilemma**

Deploying an LLM as the core of a trading system introduces unique operational risks:

* **Model Reliability and Hallucination:** There is an inherent risk that the LLM may misinterpret data or "hallucinate" a flawed rationale for a trade. The use of structured prompts and Chain-of-Thought reasoning mitigates this by forcing a logical process, but it does not eliminate the risk entirely.42  
* **API Latency and Failure:** The system's operation depends on the reliability of two external APIs: DeepSeek and Aster. The architecture must include robust error handling, timeouts, and fallback mechanisms. For example, the Risk Management module must have a protocol for situations where a position is open but the LLM API is unresponsive, potentially triggering a time-based exit.  
* **Over-Optimization:** An LLM is fundamentally a sophisticated pattern-matching system. There is a significant risk of the agent developing a strategy that appears highly profitable in simulation but is merely over-fitted to recent market conditions. Continuous, real-time performance monitoring and periodic re-evaluation of the core prompt are necessary to combat strategy decay.39

## **Conclusion: The Future of Agentic Trading in Decentralized Finance**

This report has detailed a comprehensive architecture for an autonomous trading agent, integrating the advanced reasoning capabilities of the DeepSeek LLM with the decentralized execution venue of the Aster DEX. The core principles of this architecture are modularity, the conceptual shift of the "prompt-as-algorithm," and the non-negotiable primacy of an independent, programmatic risk management module.  
The confluence of cost-effective, open-weight LLMs and accessible DeFi APIs is fundamentally democratizing the field of quantitative trading.11 It empowers individuals and small teams with tools that were once the exclusive domain of large financial institutions. This opens up a new frontier for financial innovation, but also introduces novel and complex challenges.  
Looking forward, the evolution of these systems will likely involve agents that are fine-tuned on specific traders' historical data, engage in collaborative or adversarial multi-agent strategies, and dynamically adapt their core prompts and logic in response to changing market regimes. This progression toward increasingly autonomous and intelligent financial agents holds profound implications for market efficiency, stability, and the very nature of trading itself, demanding a parallel evolution in our approaches to risk management and system design.

#### **引用的著作**

1. Can Large Language Models Trade? Testing Financial Theories with LLM Agents in Market Simulations \- arXiv, 访问时间为 十月 22, 2025， [https://arxiv.org/html/2504.10789v1](https://arxiv.org/html/2504.10789v1)  
2. Harness the power of AI and LLMs in the modern trading world, 访问时间为 十月 22, 2025， [https://t4b.com/about-us/blog/harness-the-power-of-ai-and-llms-in-the-modern-trading-world/](https://t4b.com/about-us/blog/harness-the-power-of-ai-and-llms-in-the-modern-trading-world/)  
3. DeFi's Newest Darling? Everything You Should Know About Aster, the Talk of CT, 访问时间为 十月 22, 2025， [https://www.blocmates.com/news-posts/defi-s-newest-darling-everything-you-should-know-about-aster-the-talk-of-ct](https://www.blocmates.com/news-posts/defi-s-newest-darling-everything-you-should-know-about-aster-the-talk-of-ct)  
4. Aster ($ASTER) a project I think has some serious potential. If you like risk & upside, this might be one to dig into : r/defi \- Reddit, 访问时间为 十月 22, 2025， [https://www.reddit.com/r/defi/comments/1nm516u/aster\_aster\_a\_project\_i\_think\_has\_some\_serious/](https://www.reddit.com/r/defi/comments/1nm516u/aster_aster_a_project_i_think_has_some_serious/)  
5. Aster Crypto (ASTER): Complete Guide to Tokenomics, APX Swap & Price Prediction \- Bitget, 访问时间为 十月 22, 2025， [https://www.bitget.com/academy/aster-crypto-guide-tokenomics-apx-swap-price-prediction-2025](https://www.bitget.com/academy/aster-crypto-guide-tokenomics-apx-swap-price-prediction-2025)  
6. DeepSeek-R1: Technical Overview of its Architecture and Innovations \- GeeksforGeeks, 访问时间为 十月 22, 2025， [https://www.geeksforgeeks.org/artificial-intelligence/deepseek-r1-technical-overview-of-its-architecture-and-innovations/](https://www.geeksforgeeks.org/artificial-intelligence/deepseek-r1-technical-overview-of-its-architecture-and-innovations/)  
7. What is DeepSeek? AI Model Basics Explained \- YouTube, 访问时间为 十月 22, 2025， [https://www.youtube.com/watch?v=KTonvXhsxpc](https://www.youtube.com/watch?v=KTonvXhsxpc)  
8. DeepSeek: Everything you need to know about this new LLM in one place \- Daily.dev, 访问时间为 十月 22, 2025， [https://daily.dev/blog/deepseek-everything-you-need-to-know-about-this-new-llm-in-one-place](https://daily.dev/blog/deepseek-everything-you-need-to-know-about-this-new-llm-in-one-place)  
9. DeepSeek's Latest AI model Prompts Market Frenzy, But Investors Should Remember To Stay The Course | J.P. Morgan, 访问时间为 十月 22, 2025， [https://www.jpmorgan.com/insights/markets/top-market-takeaways/tmt-deepseeks-latest-ai-model-prompts-market-frenzy-but-investors-should-remember-to-stay-the-course](https://www.jpmorgan.com/insights/markets/top-market-takeaways/tmt-deepseeks-latest-ai-model-prompts-market-frenzy-but-investors-should-remember-to-stay-the-course)  
10. DeepSeek \- Wikipedia, 访问时间为 十月 22, 2025， [https://en.wikipedia.org/wiki/DeepSeek](https://en.wikipedia.org/wiki/DeepSeek)  
11. Understanding DeepSeek: A New Era in AI Models | by Ajay Verma | Medium, 访问时间为 十月 22, 2025， [https://medium.com/@ajayverma23/understanding-deepseek-a-new-era-in-ai-models-47cd2d07ec69](https://medium.com/@ajayverma23/understanding-deepseek-a-new-era-in-ai-models-47cd2d07ec69)  
12. DeepSeek API: A Guide With Examples and Cost Calculations \- DataCamp, 访问时间为 十月 22, 2025， [https://www.datacamp.com/tutorial/deepseek-api](https://www.datacamp.com/tutorial/deepseek-api)  
13. DeepSeek API Docs: Your First API Call, 访问时间为 十月 22, 2025， [https://api-docs.deepseek.com/](https://api-docs.deepseek.com/)  
14. DeepSeek API: Your First API Call, 访问时间为 十月 22, 2025， [https://deepseek.apidog.io/your-first-api-call-835227m0](https://deepseek.apidog.io/your-first-api-call-835227m0)  
15. Build an Intelligent Agent System for Market Analysis with DeepSeek \- Dynamiq, 访问时间为 十月 22, 2025， [https://www.getdynamiq.ai/post/build-an-intelligent-agent-system-for-market-analysis-with-deepseek](https://www.getdynamiq.ai/post/build-an-intelligent-agent-system-for-market-analysis-with-deepseek)  
16. Stock market analysis: the impact of AI tools like DeepSeek \- Meer, 访问时间为 十月 22, 2025， [https://www.meer.com/en/88687-stock-market-analysis-the-impact-of-ai-tools-like-deepseek](https://www.meer.com/en/88687-stock-market-analysis-the-impact-of-ai-tools-like-deepseek)  
17. Large Language Models in equity markets: applications, techniques, and insights \- Frontiers, 访问时间为 十月 22, 2025， [https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1608365/full](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1608365/full)  
18. Large Language Models in equity markets: applications, techniques, and insights \- PMC, 访问时间为 十月 22, 2025， [https://pmc.ncbi.nlm.nih.gov/articles/PMC12421730/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12421730/)  
19. LLMs in Quant Finance: Leveraging Smarter Strategies and Market Edge \- Medium, 访问时间为 十月 22, 2025， [https://medium.com/@quantclubiitkgp/llms-in-quant-finance-leveraging-smarter-strategies-and-market-edge-6c4176e02114](https://medium.com/@quantclubiitkgp/llms-in-quant-finance-leveraging-smarter-strategies-and-market-edge-6c4176e02114)  
20. Sentiment-Aware Stock Price Prediction with Transformer and LLM-Generated Formulaic Alpha \- arXiv, 访问时间为 十月 22, 2025， [https://arxiv.org/html/2508.04975v1](https://arxiv.org/html/2508.04975v1)  
21. (PDF) Sentiment-Aware Stock Price Prediction with Transformer and ..., 访问时间为 十月 22, 2025， [https://www.researchgate.net/publication/394396975\_Sentiment-Aware\_Stock\_Price\_Prediction\_with\_Transformer\_and\_LLM-Generated\_Formulaic\_Alpha](https://www.researchgate.net/publication/394396975_Sentiment-Aware_Stock_Price_Prediction_with_Transformer_and_LLM-Generated_Formulaic_Alpha)  
22. \[2508.04975\] Sentiment-Aware Stock Price Prediction with Transformer and LLM-Generated Formulaic Alpha \- arXiv, 访问时间为 十月 22, 2025， [https://arxiv.org/abs/2508.04975](https://arxiv.org/abs/2508.04975)  
23. Aster \- Decentralized Finance \- IQ.wiki, 访问时间为 十月 22, 2025， [https://iq.wiki/wiki/aster](https://iq.wiki/wiki/aster)  
24. Top 10 Upcoming Crypto Airdrops in 2025 (UPDATED) \- CoinGecko, 访问时间为 十月 22, 2025， [https://www.coingecko.com/learn/new-crypto-airdrop-rewards](https://www.coingecko.com/learn/new-crypto-airdrop-rewards)  
25. What Is Aster (ASTER) And How Does It Work? \- CoinMarketCap, 访问时间为 十月 22, 2025， [https://coinmarketcap.com/cmc-ai/aster/what-is/](https://coinmarketcap.com/cmc-ai/aster/what-is/)  
26. ASTER/USD TETHER Trade Ideas — BLOFIN:ASTERUSDT \- TradingView, 访问时间为 十月 22, 2025， [https://www.tradingview.com/symbols/ASTERUSDT/ideas/?exchange=BLOFIN](https://www.tradingview.com/symbols/ASTERUSDT/ideas/?exchange=BLOFIN)  
27. How to Buy Aster Coin ($ASTER): A Complete Step-by-Step Guide \- BitCourier, 访问时间为 十月 22, 2025， [https://bitcourier.co.uk/blog/buy-aster](https://bitcourier.co.uk/blog/buy-aster)  
28. What Is Aster Perpetual DEX and How Does It Work? \- BingX Academy, 访问时间为 十月 22, 2025， [https://bingx.com/en/learn/what-is-aster-perp-dex-and-token-tge](https://bingx.com/en/learn/what-is-aster-perp-dex-and-token-tge)  
29. asterdex/api-docs \- GitHub, 访问时间为 十月 22, 2025， [https://github.com/asterdex/api-docs](https://github.com/asterdex/api-docs)  
30. Solana Founder Unveils 'Percolator' Perp DEX – A Direct Shot at Aster and Hyperliquid, 访问时间为 十月 22, 2025， [https://cryptonews.com/news/solana-founder-unveils-percolator-perp-dex-a-direct-shot-at-aster-and-hyperliquid/](https://cryptonews.com/news/solana-founder-unveils-percolator-perp-dex-a-direct-shot-at-aster-and-hyperliquid/)  
31. asteraiagent \- GitHub, 访问时间为 十月 22, 2025， [https://github.com/asteraiagent/](https://github.com/asteraiagent/)  
32. Unlocking Crypto Data: A Deep Dive into Kukapay's Aster Finance MCP Server for AI Engineers \- Skywork.ai, 访问时间为 十月 22, 2025， [https://skywork.ai/skypage/en/unlocking-crypto-data-kukapay-aster-finance/1977988715307257856](https://skywork.ai/skypage/en/unlocking-crypto-data-kukapay-aster-finance/1977988715307257856)  
33. AscendEx Pro API Documentation – API Reference \- GitHub Pages, 访问时间为 十月 22, 2025， [https://ascendex.github.io/ascendex-pro-api/](https://ascendex.github.io/ascendex-pro-api/)  
34. Introducing Futures Pro (v2) APIs – AscendEX Futures API Reference \- GitHub Pages, 访问时间为 十月 22, 2025， [https://ascendex.github.io/ascendex-futures-pro-api-v2/](https://ascendex.github.io/ascendex-futures-pro-api-v2/)  
35. freqtrade/freqtrade: Free, open source crypto trading bot \- GitHub, 访问时间为 十月 22, 2025， [https://github.com/freqtrade/freqtrade](https://github.com/freqtrade/freqtrade)  
36. qrak/LLM\_trader: AI-Powered trading analysis tool using ... \- GitHub, 访问时间为 十月 22, 2025， [https://github.com/qrak/LLM\_trader](https://github.com/qrak/LLM_trader)  
37. Understanding Perpetual Futures: A Guide for Cryptocurrency Traders \- Investopedia, 访问时间为 十月 22, 2025， [https://www.investopedia.com/what-are-perpetual-futures-7494870](https://www.investopedia.com/what-are-perpetual-futures-7494870)  
38. What are the risks of trading perpetuals? \- Gemini Support, 访问时间为 十月 22, 2025， [https://support.gemini.com/hc/en-us/articles/12086894290203-What-are-the-risks-of-trading-perpetuals](https://support.gemini.com/hc/en-us/articles/12086894290203-What-are-the-risks-of-trading-perpetuals)  
39. Risk Management in Futures Trading \- Investopedia, 访问时间为 十月 22, 2025， [https://www.investopedia.com/articles/optioninvestor/07/money\_management\_futures.asp](https://www.investopedia.com/articles/optioninvestor/07/money_management_futures.asp)  
40. Risk Management for Futures Trading | NinjaTrader, 访问时间为 十月 22, 2025， [https://ninjatrader.com/futures/futures-trading-basics/risk-management/](https://ninjatrader.com/futures/futures-trading-basics/risk-management/)  
41. How to Use Perpetual Futures to boost trading potential \- Mudrex Learn, 访问时间为 十月 22, 2025， [https://mudrex.com/learn/how-to-use-perpetual-futures-to-boost-trading-potential/](https://mudrex.com/learn/how-to-use-perpetual-futures-to-boost-trading-potential/)  
42. LLMs for trading : r/algotrading \- Reddit, 访问时间为 十月 22, 2025， [https://www.reddit.com/r/algotrading/comments/1k1s8q9/llms\_for\_trading/](https://www.reddit.com/r/algotrading/comments/1k1s8q9/llms_for_trading/)