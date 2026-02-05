# 🚀 QuantEdge - Crypto Paper Trading Bot with Live Dashboard

A professional algorithmic trading system for cryptocurrency with real-time web dashboard, pattern recognition, and automated risk management.

## ✨ Features

- **🎯 Pattern Recognition**: Identifies 4 trading patterns (trend pullbacks, breakouts, mean reversion, momentum)
- **📊 Live Dashboard**: Beautiful Attio-style web interface with real-time updates
- **💾 Persistent Storage**: SQLite database for trade history and equity curve
- **🔄 Multi-Pair Support**: Run multiple bots simultaneously on different pairs
- **🛡️ Risk Management**: ATR-based stops, position sizing, daily limits
- **📈 Real-Time Charts**: Equity curve, P&L distribution, live indicators
- **🖥️ PM2 Ready**: Production deployment with auto-restart and log management

## 🎨 Dashboard Preview

Beautiful, modern UI showing:

- Real-time equity curve
- Current position details
- Live technical indicators (RSI, MACD, Price, Volume)
- Recent trades table
- Performance metrics (Win rate, Profit factor, ROI)
- P&L distribution chart

Access from anywhere: Desktop, Tablet, Mobile (fully responsive)

## 📦 Quick Start

### **Local Development**

```bash
# Install dependencies
pip install -r requirements.txt

# Create static folder for dashboard
mkdir static

# Test single bot
python paper_trader_api.py BTCUSDT 15m 5000

# Open dashboard
# Visit http://localhost:5000
```

### **Ubuntu Server Deployment**

```bash
# Run setup script
chmod +x setup.sh
./setup.sh

# Start with PM2
pm2 start ecosystem.config.js

# View dashboard
http://YOUR_SERVER_IP:5000
```

Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)

## 🎯 Usage

### **Command Line Arguments**

```bash
# Format: python paper_trader_api.py [SYMBOL] [TIMEFRAME] [PORT]

# Examples
python paper_trader_api.py BTCUSDT 15m 5000
python paper_trader_api.py ETHUSDT 1h 5001
python paper_trader_api.py SOLUSDT 5m 5002
```

### **Backtesting**

```bash
# Test strategy on historical data
python backtester.py BTCUSDT 15m 30

# Results
Initial Capital:  $10,000
Final Capital:    $17,448
Net Profit:       +74.49%
Win Rate:         45.3%
Profit Factor:    1.27
```

### **Multiple Bots**

Run different pairs on different ports:

```bash
pm2 start paper_trader_api.py --name btc -- BTCUSDT 15m 5000
pm2 start paper_trader_api.py --name eth -- ETHUSDT 15m 5001
pm2 start paper_trader_api.py --name sol -- SOLUSDT 15m 5002
```

Access dashboards:

- BTC: http://localhost:5000
- ETH: http://localhost:5001
- SOL: http://localhost:5002

## 📊 API Endpoints

- **GET** `/api/status` - Bot status and performance
- **GET** `/api/trades` - Trade history (last 100)
- **GET** `/api/equity` - Equity curve data
- **POST** `/api/stop` - Stop the bot

## 🏗️ Architecture

```
┌─────────────────────┐
│  trading_engine.py  │  ← Core strategy logic
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐  ┌──▼───────────────┐
│backtester│  │paper_trader_api │
└─────────┘  └────────┬─────────┘
                      │
             ┌────────┴────────┐
             │                 │
        ┌────▼─────┐    ┌─────▼─────┐
        │ SQLite   │    │  Flask    │
        │ Database │    │  API      │
        └──────────┘    └─────┬─────┘
                              │
                       ┌──────▼──────┐
                       │  Dashboard  │
                       │  (HTML/JS)  │
                       └─────────────┘
```

## 🎓 Strategy Details

### **Trading Patterns**

1. **Trend Pullback** (Most Reliable)
   - Entry: Pullback to EMA + momentum shift
   - Use: Trending markets

2. **Breakout/Breakdown** (High Volatility)
   - Entry: Break above/below consolidation + volume
   - Use: Range breakouts

3. **Mean Reversion** (Range-bound)
   - Entry: Bollinger Band extremes + RSI
   - Use: Sideways markets

4. **Momentum** (Catch-all)
   - Entry: Strong directional candle + confirmation
   - Use: Obvious moves

### **Risk Management**

- Stop Loss: 2× ATR
- Take Profit: 3.5× ATR (1.75:1 R:R)
- Position Size: 2% risk per trade
- Max Leverage: 3x (adjustable)
- Daily Limits: 8 trades max, 8% loss limit
- Trailing Stop: Activates at 1.5% profit

### **Indicators Used**

- EMA (12/26/50)
- RSI (14)
- MACD (12/26/9)
- Bollinger Bands (20, 2σ)
- ATR (14)
- Volume analysis

## 🔧 Configuration

Edit parameters in `paper_trader_api.py`:

```python
bot = PaperTradingBotAPI(
    symbol='BTC/USDT',      # Trading pair
    timeframe='15m',        # Candle timeframe
    initial_capital=10000,  # Starting capital
    leverage=3,             # Leverage (1-10)
    risk_per_trade=0.02,    # Risk per trade (2%)
    port=5000               # Dashboard port
)
```

## 📈 Performance Metrics

The system tracks:

- Win Rate & Total Trades
- Profit Factor (Total Wins / Total Losses)
- Expectancy (Expected $ per trade)
- Sharpe Ratio (Risk-adjusted returns)
- Max Drawdown
- ROI (Return on Investment)
- Max Consecutive Losses

## 🛡️ Risk Warnings

⚠️ **IMPORTANT**: This is for **PAPER TRADING ONLY**

- Crypto is extremely volatile
- Leverage amplifies both gains AND losses
- Past performance ≠ future results
- Test thoroughly before using real money
- Never risk money you can't afford to lose

## 📁 File Structure

```
quantedge/
├── trading_engine.py        # Core strategy (modify here)
├── backtester.py           # Historical testing
├── paper_trader_api.py     # Live paper trading with API
├── ecosystem.config.js     # PM2 configuration
├── requirements.txt        # Python dependencies
├── setup.sh               # Automated setup script
├── DEPLOYMENT.md          # Full deployment guide
├── README.md             # This file
├── static/
│   └── dashboard.html    # Web dashboard
├── logs/                 # PM2 logs (auto-created)
├── trading_data.db      # SQLite database (auto-created)
└── trading_state.json   # Bot state (auto-created)
```

## 🚀 PM2 Commands

```bash
# Start
pm2 start ecosystem.config.js

# Status
pm2 status
pm2 list

# Logs
pm2 logs
pm2 logs quantedge-btc

# Control
pm2 stop all
pm2 restart all
pm2 delete all

# Monitor
pm2 monit

# Save & Startup
pm2 save
pm2 startup
```

## 🔍 Monitoring

### **View Logs**

```bash
pm2 logs quantedge-btc --lines 100
```

### **Check Database**

```bash
sqlite3 trading_data.db
> SELECT * FROM trades ORDER BY id DESC LIMIT 10;
> .quit
```

### **Performance**

```bash
pm2 monit
```

## 🆘 Troubleshooting

**Bot won't start?**

```bash
source venv/bin/activate
python paper_trader_api.py BTCUSDT
```

**Can't access dashboard?**

```bash
curl http://localhost:5000/api/status
sudo ufw allow 5000/tcp
```

**Database locked?**

```bash
pm2 stop all
rm trading_data.db-journal
pm2 restart all
```

Full troubleshooting: [DEPLOYMENT.md](DEPLOYMENT.md)

## 📝 Notes

- Bot uses Binance public API (no key needed for paper trading)
- Updates every 60 seconds (configurable)
- Dashboard updates every 5 seconds
- All data stored locally in SQLite
- Fully responsive dashboard (works on mobile)

## 🤝 Contributing

To improve the strategy:

1. Modify `trading_engine.py`
2. Run backtest to verify
3. Test in paper trading
4. Share results!

## 📄 License

MIT License - Use at your own risk

---

**Remember**: This is a learning tool. Always paper trade extensively before considering real capital.

🎯 **Ready to start?** Run `./setup.sh` then check [DEPLOYMENT.md](DEPLOYMENT.md)!
