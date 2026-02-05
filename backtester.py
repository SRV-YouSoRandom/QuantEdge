import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import matplotlib.pyplot as plt
import seaborn as sns
from trading_engine import TradingEngine

class CryptoBacktester(TradingEngine):
    """
    Backtester that inherits from TradingEngine
    All strategy logic is in the parent class
    """
    
    def __init__(self, symbol='BTC/USDT', timeframe='15m', initial_capital=10000, 
                 leverage=3, risk_per_trade=0.02):
        super().__init__(symbol, timeframe, initial_capital, leverage, risk_per_trade)
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.equity_curve = []
        
    def fetch_data(self, days=30):
        """Fetch historical OHLCV data from Binance"""
        print(f"Fetching {days} days of {self.timeframe} data for {self.symbol}...")
        
        since = self.exchange.parse8601((datetime.now() - timedelta(days=days)).isoformat())
        all_ohlcv = []
        
        while True:
            try:
                ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since, limit=1000)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                if len(ohlcv) < 1000:
                    break
            except Exception as e:
                print(f"Error fetching data: {e}")
                break
                
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        print(f"✓ Fetched {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        return df
    
    def run(self, df):
        """Run backtest on historical data"""
        print("\n" + "="*60)
        print("RUNNING BACKTEST")
        print("="*60)
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        print(f"Analyzing {len(df)} candles...")
        print(f"Period: {df.index[0]} to {df.index[-1]}")
        print(f"Strategy: {self.timeframe} timeframe, {self.leverage}x leverage")
        print("="*60 + "\n")
        
        # Backtest loop
        for i in range(len(df)):
            current_time = df.index[i]
            current_price = df['close'].iloc[i]
            current_atr = df['atr'].iloc[i]
            
            # Update equity curve
            current_equity = self.capital
            if self.position:
                if self.position['type'] == 'long':
                    unrealized_pnl = (current_price - self.position['entry_price']) * self.position['size']
                else:
                    unrealized_pnl = (self.position['entry_price'] - current_price) * self.position['size']
                current_equity += unrealized_pnl
            
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': current_equity
            })
            
            # Check exit conditions
            if self.position:
                should_exit, reason = self.should_exit_position(current_price, current_atr)
                if should_exit:
                    trade = self.close_position(current_price, current_time, reason)
                    self._print_trade_closed(trade)
            
            # Check for new signals
            if not self.position:
                signal = self.check_signal(df, i)
                if signal:
                    if self.open_position(signal, current_time):
                        self._print_trade_opened(self.position)
        
        # Close any remaining position
        if self.position:
            trade = self.close_position(df['close'].iloc[-1], df.index[-1], 'END_OF_DATA')
            self._print_trade_closed(trade)
        
        return self.analyze_results()
    
    def _print_trade_opened(self, position):
        """Print trade opening details"""
        print(f"\n{position['pattern'].upper()}: {position['type'].upper()} "
              f"@ ${position['entry_price']:.2f} | "
              f"Size: {position['size']:.4f} | "
              f"SL: ${position['stop_loss']:.2f} | "
              f"TP: ${position['take_profit']:.2f} | "
              f"Conf: {position['confidence']:.1f}")
    
    def _print_trade_closed(self, trade):
        """Print trade closing details"""
        emoji = "✓" if trade['pnl'] > 0 else "✗"
        print(f"{emoji} CLOSE @ ${trade['exit_price']:.2f} | "
              f"PnL: ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%) | "
              f"{trade['reason']} | "
              f"Capital: ${self.capital:.2f}")
    
    def analyze_results(self):
        """Analyze and display backtest results"""
        performance = self.analyze_performance()
        
        if not performance:
            print("\n❌ No trades executed!")
            return None
        
        equity_df = pd.DataFrame(self.equity_curve)
        trades_df = pd.DataFrame(self.trades)
        
        # Calculate max drawdown
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Print results
        print("\n" + "="*60)
        print("📊 BACKTEST RESULTS")
        print("="*60)
        print(f"Initial Capital:        ${self.initial_capital:,.2f}")
        print(f"Final Capital:          ${self.capital:,.2f}")
        print(f"Net Profit:             ${performance['net_profit']:,.2f} ({performance['roi']:+.2f}%)")
        print(f"\nTotal Trades:           {performance['total_trades']}")
        print(f"Winning Trades:         {performance['winning_trades']} ({performance['win_rate']:.1f}%)")
        print(f"Losing Trades:          {performance['losing_trades']}")
        print(f"\nProfit Factor:          {performance['profit_factor']:.2f}")
        print(f"Average Win:            ${performance['avg_win']:.2f}")
        print(f"Average Loss:           ${performance['avg_loss']:.2f}")
        print(f"Expectancy:             ${performance['expectancy']:.2f}")
        print(f"\nMax Drawdown:           {max_drawdown:.2f}%")
        print(f"Sharpe Ratio:           {performance['sharpe_ratio']:.2f}")
        print(f"Max Consecutive Losses: {int(performance['max_consecutive_losses'])}")
        print("="*60)
        
        # Trade distribution
        print("\n📈 Exit Reasons:")
        exit_reasons = trades_df['reason'].value_counts()
        for reason, count in exit_reasons.items():
            print(f"  {reason}: {count}")
        
        return {
            'performance': performance,
            'equity_df': equity_df,
            'trades_df': trades_df,
            'max_drawdown': max_drawdown
        }
    
    def plot_results(self, results):
        """Plot equity curve and analysis"""
        if not results:
            return
        
        equity_df = results['equity_df']
        trades_df = results['trades_df']
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # Equity Curve
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(equity_df['timestamp'], equity_df['equity'], linewidth=2, color='#2E86AB', label='Equity')
        ax1.axhline(y=self.initial_capital, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
        ax1.fill_between(equity_df['timestamp'], equity_df['equity'], self.initial_capital, 
                         where=(equity_df['equity'] >= self.initial_capital), alpha=0.3, color='green')
        ax1.fill_between(equity_df['timestamp'], equity_df['equity'], self.initial_capital,
                         where=(equity_df['equity'] < self.initial_capital), alpha=0.3, color='red')
        ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Capital (USDT)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Drawdown
        ax2 = fig.add_subplot(gs[1, :])
        ax2.fill_between(equity_df['timestamp'], equity_df['drawdown'], 0, 
                         color='#A23B72', alpha=0.6)
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # PnL Distribution
        ax3 = fig.add_subplot(gs[2, 0])
        wins = trades_df[trades_df['pnl'] > 0]['pnl']
        losses = trades_df[trades_df['pnl'] <= 0]['pnl']
        ax3.hist([wins, losses], bins=20, label=['Wins', 'Losses'], color=['green', 'red'], alpha=0.7)
        ax3.set_title('PnL Distribution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('PnL (USDT)', fontsize=10)
        ax3.set_ylabel('Frequency', fontsize=10)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Cumulative Returns
        ax4 = fig.add_subplot(gs[2, 1])
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        ax4.plot(range(len(trades_df)), trades_df['cumulative_pnl'], linewidth=2, color='#F18F01')
        ax4.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax4.set_title('Cumulative PnL', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Trade Number', fontsize=10)
        ax4.set_ylabel('Cumulative PnL (USDT)', fontsize=10)
        ax4.grid(True, alpha=0.3)
        
        plt.savefig('backtest_results.png', dpi=300, bbox_inches='tight')
        print("\n✓ Plot saved as 'backtest_results.png'")
        plt.show()


if __name__ == "__main__":
    import sys
    
    # Default parameters
    symbol = 'BTC/USDT'
    timeframe = '15m'
    days = 30
    initial_capital = 10000
    leverage = 3
    risk_per_trade = 0.02
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        # Convert ETHUSDT to ETH/USDT format
        pair = sys.argv[1].upper()
        if '/' not in pair:
            # Assume it's like ETHUSDT, convert to ETH/USDT
            if pair.endswith('USDT'):
                base = pair[:-4]
                symbol = f"{base}/USDT"
            elif pair.endswith('BTC'):
                base = pair[:-3]
                symbol = f"{base}/BTC"
            else:
                symbol = pair
        else:
            symbol = pair
    
    # Optional: timeframe as second argument
    if len(sys.argv) > 2:
        timeframe = sys.argv[2]
    
    # Optional: days as third argument
    if len(sys.argv) > 3:
        days = int(sys.argv[3])
    
    print(f"\n{'='*70}")
    print(f"🎯 BACKTESTING CONFIGURATION")
    print(f"{'='*70}")
    print(f"Symbol:          {symbol}")
    print(f"Timeframe:       {timeframe}")
    print(f"Period:          {days} days")
    print(f"Initial Capital: ${initial_capital:,}")
    print(f"Leverage:        {leverage}x")
    print(f"Risk per Trade:  {risk_per_trade*100}%")
    print(f"{'='*70}\n")
    
    # Initialize backtester
    backtester = CryptoBacktester(
        symbol=symbol,
        timeframe=timeframe,
        initial_capital=initial_capital,
        leverage=leverage,
        risk_per_trade=risk_per_trade
    )
    
    # Fetch data
    df = backtester.fetch_data(days=days)
    
    # Run backtest
    results = backtester.run(df)
    
    # Plot results
    if results:
        backtester.plot_results(results)