# 🚀 Binance Futures Testnet — Trading Bot

> A clean, production-ready Python CLI trading bot for Binance USDT-M Futures Testnet.  
> Built for the **Python Developer Intern** application at Anything AI.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Order types** | MARKET · LIMIT · STOP_MARKET (bonus) |
| **Sides** | BUY · SELL |
| **CLI modes** | Direct flags *and* interactive menu |
| **Validation** | Full input validation with clear error messages |
| **Logging** | Structured file + console logging |
| **Error handling** | API errors · network failures · invalid inputs |
| **Code structure** | Clean separation: client / orders / validators / CLI |

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper
│   ├── orders.py          # Order placement + pretty printing
│   ├── validators.py      # Input validation
│   └── logging_config.py  # File + console logging setup
├── cli.py                 # CLI entry point (argparse)
├── sample_logs/
│   ├── market_order.log
│   ├── limit_order.log
│   └── stop_market_order.log
├── logs/                  # Auto-created at runtime
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1 · Get Testnet Credentials

1. Visit [Binance Futures Testnet](https://testnet.binancefuture.com)
2. Sign in with your GitHub or Google account
3. Go to **API Management** → generate a key pair
4. Copy your **API Key** and **Secret Key**

### 2 · Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/binance-trading-bot.git
cd binance-trading-bot
pip install -r requirements.txt
```

### 3 · Set Credentials

**Option A — Environment variables (recommended)**

```bash
# Linux / macOS
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"

# Windows (PowerShell)
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

**Option B — CLI flags** (shown in examples below)

**Option C — Interactive prompt** (bot will ask if not set)

---

## 🖥️ How to Run

### Market Order (BUY)

```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

**Output:**
```
╔══════════════════════════════════════════════════════════╗
║       🚀  Binance Futures Testnet  —  Trading Bot        ║
╚══════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📋  ORDER SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✅  ORDER PLACED SUCCESSFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Order ID      : 4059355891
  Status        : FILLED
  Executed Qty  : 0.001
  Avg Price     : 43250.50
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Limit Order (SELL)

```bash
python cli.py order --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3200
```

---

### Stop-Market Order (Bonus)

```bash
python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop-price 42000
```

---

### With API keys as flags

```bash
python cli.py order \
  --api-key YOUR_KEY \
  --api-secret YOUR_SECRET \
  --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

---

### Interactive Menu Mode (Bonus)

```bash
python cli.py interactive
```

Launches a full menu:
```
  MAIN MENU
  [1]  Place an Order
  [2]  View Account Balance
  [3]  View Open Orders
  [4]  Cancel an Order
  [q]  Quit
```

---

### Check Account Balance

```bash
python cli.py balance
```

---

### Help

```bash
python cli.py --help
python cli.py order --help
```

---

## 📝 Log Files

Logs are written to `logs/trading_bot_YYYYMMDD.log` automatically.

**Log format:**
```
2025-01-15 14:22:01 | INFO     | trading_bot | Placing BUY MARKET order | symbol=BTCUSDT qty=0.001 price=N/A
2025-01-15 14:22:02 | INFO     | trading_bot | Order placed | id=4059355891 status=FILLED executedQty=0.001
```

Sample logs from testnet runs are included in `sample_logs/`:
- `sample_logs/market_order.log` — MARKET BUY on BTCUSDT
- `sample_logs/limit_order.log` — LIMIT SELL on ETHUSDT
- `sample_logs/stop_market_order.log` — STOP_MARKET SELL on BTCUSDT (bonus)

---

## 🏗️ Architecture

```
CLI (cli.py)
    │
    ├─ validates raw input → bot/validators.py
    │
    ├─ calls place_order() → bot/orders.py
    │       │
    │       └─ calls BinanceFuturesClient → bot/client.py
    │               │
    │               └─ signs & sends HTTP requests → Binance Testnet REST API
    │
    └─ logs everything → bot/logging_config.py → logs/
```

---

## 🔧 Assumptions

- **Testnet only** — base URL is hardcoded to `https://testnet.binancefuture.com`
- **USDT-M Futures** — only Futures perpetual contracts are supported
- **Quantity precision** — the user is responsible for entering a quantity that meets the symbol's step size; the bot will relay any precision errors from Binance clearly
- **No margin mode switching** — the bot assumes your account is already set to the desired margin mode (cross/isolated) on the testnet dashboard
- **Python 3.8+** required

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP client for Binance REST API |

No heavy frameworks, no vendor lock-in to python-binance — raw REST calls give full control and transparency.

---

## 🧪 Running Tests (optional)

```bash
# Validate input logic without API calls
python -c "
from bot.validators import validate_all
print(validate_all('BTCUSDT', 'BUY', 'LIMIT', 0.001, price=43000))
"
```

---

## 📧 Submission

- **GitHub:** https://github.com/YOUR_USERNAME/binance-trading-bot
- **Email:** joydip@anything.ai, chetan@anything.ai, hello@anything.ai
- **CC:** sonika@anything.ai

---

*Built with ❤️ for the Anything AI Python Developer Intern application.*
