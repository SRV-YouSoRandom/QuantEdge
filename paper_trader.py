import pandas as pd
from datetime import datetime
import ccxt
import time
import json
from pathlib import Path
from trading_engine import TradingEngine

class PaperTradingBot(TradingEngine):
    """
    Live Paper Trading Bot that inherits from TradingEngine
    All strategy logic is in the parent class
    """
    
    def __init__(self, symbol='BTC/USDT', timeframe='15m', initial_capital=10000,
                 leverage=3, risk_per_trade=0.02):
        super().__init__(symbol, timeframe, initial_capital, leverage, risk_per_trade)
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.state_file = Path('trading_state.json')
        
        # Load previous state if exists
        self.load_state()
        
    def save_state(self):
        """Save trading state to file"""
        state = {
            'capital': self.capital,
            'position': self.position,
            'trades': self.trades,
            'daily_pnl': self.daily_pnl,
            'daily_trade_count': self.daily_trade_count,
            'last_trade_date': str(self.last_trade_date) if self.last_trade_date else None,
            'last_update': datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_state(self):
        """Load previous trading state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.capital = state.get('capital', self.initial_capital)
                    self.position = state.get('position')
                    self.trades = state.get('trades', [])
                    self.daily_pnl = state.get('daily_pnl', 0)
                    self.daily_trade_count = state.get('daily_trade_count', 0)
                    
                    last_date = state.get('last_trade_date')
                    if last_date:
                        self.last_trade_date = datetime.fromisoformat(last_date).date()
                    
                    print(f"✓ Loaded previous state:")
                    print(f"  Capital: ${self.capital:.2f}")
                    print(f"  Open Position: {'Yes' if self.position else 'No'}")
                    print(f"  Total Trades: {len(self.trades)}\n")
            except Exception as e:
                print(f"⚠️ Error loading state: {e}")
    
    def fetch_live_data(self, lookback=200):
        """Fetch recent OHLCV data for analysis"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=lookback)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"⚠️ Error fetching data: {e}")
            return None
    
    def print_status(self, df):
        """Print current bot status"""
        current = df.iloc[-1]
        current_price = current['close']
        current_time = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"📊 BOT STATUS - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Symbol: {self.symbol} | Timeframe: {self.timeframe} | Leverage: {self.leverage}x")
        print(f"Current Price: ${current_price:,.2f}")
        print(f"Capital: ${self.capital:,.2f} | Daily Trades: {self.daily_trade_count}/{self.max_trades_per_day}")
        
        print(f"\n📈 Indicators:")
        print(f"  RSI: {current['rsi']:.1f} | MACD: {current['macd']:.2f} (Signal: {current['macd_signal']:.2f})")
        print(f"  Trend Strength: {current['trend_strength']:.2f}% | ATR: ${current['atr']:.2f} ({current['atr_pct']:.2f}%)")
        print(f"  Volume Ratio: {current['volume_ratio']:.2f}x | Momentum(5): {current['momentum_5']:.2f}%")
        
        if self.position:
            pos = self.position
            if pos['type'] == 'long':
                unrealized_pnl = (current_price - pos['entry_price']) * pos['size']
            else:
                unrealized_pnl = (pos['entry_price'] - current_price) * pos['size']
            
            unrealized_pnl_pct = (unrealized_pnl / pos['entry_capital']) * 100
            risk_reward = abs((pos['take_profit'] - pos['entry_price']) / (pos['entry_price'] - pos['stop_loss']))
            
            print(f"\n🎯 Open {pos['type'].upper()} Position:")
            print(f"  Entry: ${pos['entry_price']:,.2f} | Current P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)")
            print(f"  Stop Loss: ${pos['stop_loss']:,.2f} | Take Profit: ${pos['take_profit']:,.2f}")
            print(f"  Risk/Reward: {risk_reward:.2f} | Confidence: {pos['confidence']:.2f}")
            
            if 'trailing_stop' in pos:
                print(f"  Trailing Stop: ${pos['trailing_stop']:,.2f} (Active)")
        else:
            print(f"\n⏳ No Open Position - Scanning for signals...")
        
        if self.trades:
            perf = self.analyze_performance()
            print(f"\n📊 Performance Summary:")
            print(f"  Trades: {perf['total_trades']} | Win Rate: {perf['win_rate']:.1f}% | "
                  f"Profit Factor: {perf['profit_factor']:.2f}")
            print(f"  Net P&L: ${perf['net_profit']:.2f} | ROI: {perf['roi']:+.2f}%")
            print(f"  Expectancy: ${perf['expectancy']:.2f} | Sharpe: {perf['sharpe_ratio']:.2f}")
        
        print(f"{'='*70}\n")
    
    def run(self, update_interval=60):
        """Run the paper trading bot"""
        print(f"\n{'='*70}")
        print(f"🤖 STARTING PAPER TRADING BOT")
        print(f"{'='*70}")
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Current Capital: ${self.capital:,.2f}")
        print(f"Leverage: {self.leverage}x")
        print(f"Risk per Trade: {self.risk_per_trade * 100}%")
        print(f"Update Interval: {update_interval}s")
        print(f"{'='*70}\n")
        
        iteration = 0
        
        try:
            while True:
                try:
                    iteration += 1
                    
                    # Fetch data and calculate indicators
                    df = self.fetch_live_data()
                    if df is None or len(df) < 100:
                        print("⚠️ Insufficient data, retrying in 30s...")
                        time.sleep(30)
                        continue
                    
                    df = self.calculate_indicators(df)
                    current_price = df['close'].iloc[-1]
                    current_atr = df['atr'].iloc[-1]
                    current_time = df.index[-1]
                    
                    # Check exit conditions
                    if self.position:
                        should_exit, reason = self.should_exit_position(current_price, current_atr)
                        if should_exit:
                            trade = self.close_position(current_price, current_time, reason)
                            self._print_trade_closed(trade)
                            self.save_state()
                    
                    # Check for new signals
                    if not self.position:
                        signal = self.check_signal(df)
                        if signal:
                            if self.open_position(signal, current_time):
                                self._print_trade_opened(self.position)
                                self.save_state()
                    
                    # Print status every iteration
                    if iteration % 1 == 0:  # Print every update
                        self.print_status(df)
                    
                    # Wait for next update
                    time.sleep(update_interval)
                    
                except ccxt.NetworkError as e:
                    print(f"⚠️ Network error: {e}. Retrying in 30s...")
                    time.sleep(30)
                except ccxt.ExchangeError as e:
                    print(f"⚠️ Exchange error: {e}. Retrying in 30s...")
                    time.sleep(30)
                except Exception as e:
                    print(f"⚠️ Unexpected error: {e}. Retrying in 30s...")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
            
            # Close open position on manual stop
            if self.position:
                df = self.fetch_live_data()
                if df is not None:
                    current_price = df['close'].iloc[-1]
                    trade = self.close_position(current_price, datetime.now(), 'MANUAL_STOP')
                    self._print_trade_closed(trade)
                    self.save_state()
            
            self.print_final_stats()
    
    def _print_trade_opened(self, position):
        """Print trade opening notification"""
        print(f"\n{'='*70}")
        print(f"🚀 OPENED {position['type'].upper()} POSITION")
        print(f"{'='*70}")
        print(f"Entry Price:      ${position['entry_price']:,.2f}")
        print(f"Position Size:    {position['size']:.4f}")
        print(f"Stop Loss:        ${position['stop_loss']:,.2f}")
        print(f"Take Profit:      ${position['take_profit']:,.2f}")
        print(f"Liquidation:      ${position['liquidation_price']:,.2f}")
        print(f"Confidence:       {position['confidence']:.2f}")
        print(f"Capital:          ${self.capital:,.2f}")
        print(f"{'='*70}\n")
    
    def _print_trade_closed(self, trade):
        """Print trade closing notification"""
        emoji = "✅" if trade['pnl'] > 0 else "❌"
        print(f"\n{'='*70}")
        print(f"{emoji} CLOSED {trade['type'].upper()} POSITION")
        print(f"{'='*70}")
        print(f"Entry Price:      ${trade['entry_price']:,.2f}")
        print(f"Exit Price:       ${trade['exit_price']:,.2f}")
        print(f"P&L:              ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%)")
        print(f"Reason:           {trade['reason']}")
        print(f"New Capital:      ${self.capital:,.2f}")
        print(f"Total Trades:     {len(self.trades)}")
        print(f"{'='*70}\n")
    
    def print_final_stats(self):
        """Print final statistics"""
        perf = self.analyze_performance()
        
        if not perf:
            print("\n📊 No trades were executed during this session.")
            return
        
        print(f"\n{'='*70}")
        print(f"📊 FINAL STATISTICS")
        print(f"{'='*70}")
        print(f"Initial Capital:        ${self.initial_capital:,.2f}")
        print(f"Final Capital:          ${self.capital:,.2f}")
        print(f"Net P&L:                ${perf['net_profit']:,.2f}")
        print(f"ROI:                    {perf['roi']:+.2f}%")
        print(f"\nTotal Trades:           {perf['total_trades']}")
        print(f"Winning Trades:         {perf['winning_trades']} ({perf['win_rate']:.1f}%)")
        print(f"Losing Trades:          {perf['losing_trades']}")
        print(f"\nProfit Factor:          {perf['profit_factor']:.2f}")
        print(f"Risk/Reward Ratio:      {perf['risk_reward']:.2f}")
        print(f"Expectancy:             ${perf['expectancy']:.2f}")
        print(f"Sharpe Ratio:           {perf['sharpe_ratio']:.2f}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    # Initialize paper trading bot
    bot = PaperTradingBot(
        symbol='BTC/USDT',
        timeframe='15m',
        initial_capital=10000,
        leverage=3,
        risk_per_trade=0.02
    )
    
    # Run bot (updates every 60 seconds)
    bot.run(update_interval=60)