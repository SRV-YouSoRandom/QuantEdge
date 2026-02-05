import pandas as pd
import numpy as np
from datetime import datetime
import ccxt
import time
import json
import sqlite3
from pathlib import Path
from trading_engine import TradingEngine
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import threading
import sys

class PaperTradingBotAPI(TradingEngine):
    """
    Live Paper Trading Bot with Web API
    """
    
    def __init__(self, symbol='BTC/USDT', timeframe='15m', initial_capital=10000,
                 leverage=3, risk_per_trade=0.02, port=5000):
        super().__init__(symbol, timeframe, initial_capital, leverage, risk_per_trade)
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.state_file = Path('trading_state.json')
        self.db_path = Path('trading_data.db')
        self.port = port
        
        # Initialize database
        self.init_database()
        
        # Load previous state
        self.load_state()
        
        # Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
        
        # Trading status
        self.is_running = False
        self.last_update = None
        self.current_indicators = {}
        
    def init_database(self):
        """Initialize SQLite database for trade history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_time TEXT,
                exit_time TEXT,
                type TEXT,
                pattern TEXT,
                entry_price REAL,
                exit_price REAL,
                size REAL,
                pnl REAL,
                pnl_percent REAL,
                reason TEXT,
                capital_after REAL
            )
        ''')
        
        # Equity curve table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                equity REAL,
                position_open INTEGER,
                symbol TEXT
            )
        ''')
        
        # Bot status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_status (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                timeframe TEXT,
                leverage REAL,
                capital REAL,
                is_running INTEGER,
                last_update TEXT,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def save_state(self):
        """Save trading state"""
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
        
        # Update database
        self.update_bot_status()
    
    def load_state(self):
        """Load previous state"""
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
                    
                    print(f"✓ Loaded state: ${self.capital:.2f}, {len(self.trades)} trades")
            except Exception as e:
                print(f"⚠️ Error loading state: {e}")
    
    def fetch_live_data(self, lookback=200):
        """Fetch recent data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=lookback)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"⚠️ Error fetching data: {e}")
            return None
    
    def save_trade_to_db(self, trade):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades (entry_time, exit_time, type, pattern, entry_price, 
                              exit_price, size, pnl, pnl_percent, reason, capital_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade['entry_time'], trade['exit_time'], trade['type'], trade['pattern'],
            trade['entry_price'], trade['exit_price'], trade['size'],
            trade['pnl'], trade['pnl_percent'], trade['reason'], self.capital
        ))
        
        conn.commit()
        conn.close()
    
    def save_equity_point(self, timestamp, equity):
        """Save equity curve point"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO equity_curve (timestamp, equity, position_open, symbol)
            VALUES (?, ?, ?, ?)
        ''', (timestamp.isoformat(), equity, 1 if self.position else 0, self.symbol))
        
        conn.commit()
        conn.close()
    
    def update_bot_status(self):
        """Update bot status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        perf = self.analyze_performance()
        
        cursor.execute('''
            INSERT OR REPLACE INTO bot_status 
            (id, symbol, timeframe, leverage, capital, is_running, last_update, 
             total_trades, winning_trades, losing_trades)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.symbol, self.timeframe, self.leverage, self.capital,
            1 if self.is_running else 0, datetime.now().isoformat(),
            len(self.trades),
            perf['winning_trades'] if perf else 0,
            perf['losing_trades'] if perf else 0
        ))
        
        conn.commit()
        conn.close()
    
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/')
        def index():
            return send_from_directory('static', 'dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get current bot status"""
            perf = self.analyze_performance()
            
            status = {
                'is_running': self.is_running,
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'capital': round(self.capital, 2),
                'initial_capital': self.initial_capital,
                'roi': round(((self.capital - self.initial_capital) / self.initial_capital) * 100, 2),
                'leverage': self.leverage,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'position': self.position,
                'indicators': self.current_indicators,
                'performance': perf
            }
            
            return jsonify(status)
        
        @self.app.route('/api/trades')
        def get_trades():
            """Get trade history"""
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('SELECT * FROM trades ORDER BY id DESC LIMIT 100', conn)
            conn.close()
            return jsonify(df.to_dict('records'))
        
        @self.app.route('/api/equity')
        def get_equity():
            """Get equity curve data"""
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('SELECT * FROM equity_curve ORDER BY id DESC LIMIT 1000', conn)
            conn.close()
            return jsonify(df.to_dict('records'))
        
        @self.app.route('/api/analytics')
        def get_analytics():
            """Get analytics data for advanced charts"""
            analytics = {
                'drawdown': self.calculate_drawdown(),
                'pnl_distribution': self.calculate_pnl_distribution(),
                'cumulative_pnl': self.calculate_cumulative_pnl()
            }
            return jsonify(analytics)
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop_bot():
            """Stop the trading bot"""
            self.is_running = False
            return jsonify({'status': 'stopped'})
    
    def calculate_drawdown(self):
        """Calculate drawdown data from equity curve"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('SELECT timestamp, equity FROM equity_curve ORDER BY id', conn)
            conn.close()
            
            if len(df) == 0:
                return []
            
            # Calculate running maximum and drawdown
            df['peak'] = df['equity'].cummax()
            df['drawdown'] = ((df['equity'] - df['peak']) / df['peak']) * 100
            
            # Return last 200 points for performance
            result = df.tail(200).to_dict('records')
            return result
        except Exception as e:
            print(f"Error calculating drawdown: {e}")
            return []
    
    def calculate_pnl_distribution(self):
        """Calculate PnL distribution for histogram"""
        try:
            if len(self.trades) == 0:
                return {'bins': [], 'frequencies': []}
            
            trades_df = pd.DataFrame(self.trades)
            pnl_values = trades_df['pnl'].values
            
            # Create bins
            num_bins = min(20, len(pnl_values))
            hist, bin_edges = np.histogram(pnl_values, bins=num_bins)
            
            # Format bin labels
            bin_labels = [f"${bin_edges[i]:.0f}" for i in range(len(bin_edges)-1)]
            
            return {
                'bins': bin_labels,
                'frequencies': hist.tolist(),
                'bin_edges': bin_edges.tolist()
            }
        except Exception as e:
            print(f"Error calculating PnL distribution: {e}")
            return {'bins': [], 'frequencies': []}
    
    def calculate_cumulative_pnl(self):
        """Calculate cumulative PnL over time"""
        try:
            if len(self.trades) == 0:
                return []
            
            trades_df = pd.DataFrame(self.trades)
            trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
            
            result = [{
                'timestamp': trade['exit_time'],
                'cumulative_pnl': float(cum_pnl)
            } for trade, cum_pnl in zip(self.trades, trades_df['cumulative_pnl'])]
            
            return result
        except Exception as e:
            print(f"Error calculating cumulative PnL: {e}")
            return []
    
    def run_trading_loop(self, update_interval=60):
        """Main trading loop"""
        self.is_running = True
        iteration = 0
        
        print(f"\n🤖 Bot started for {self.symbol}")
        
        while self.is_running:
            try:
                iteration += 1
                
                # Fetch data
                df = self.fetch_live_data()
                if df is None or len(df) < 100:
                    time.sleep(30)
                    continue
                
                df = self.calculate_indicators(df)
                current_price = df['close'].iloc[-1]
                current_atr = df['atr'].iloc[-1]
                current_time = df.index[-1]
                
                # Store current indicators for API
                current = df.iloc[-1]
                self.current_indicators = {
                    'price': float(current['close']),
                    'rsi': float(current['rsi']),
                    'macd': float(current['macd']),
                    'macd_signal': float(current['macd_signal']),
                    'bb_upper': float(current['bb_upper']),
                    'bb_lower': float(current['bb_lower']),
                    'atr': float(current['atr']),
                    'volume_ratio': float(current['volume_ratio'])
                }
                
                # Save equity point
                current_equity = self.capital
                if self.position:
                    if self.position['type'] == 'long':
                        unrealized = (current_price - self.position['entry_price']) * self.position['size']
                    else:
                        unrealized = (self.position['entry_price'] - current_price) * self.position['size']
                    current_equity += unrealized
                
                self.save_equity_point(current_time, current_equity)
                
                # Check exits
                if self.position:
                    should_exit, reason = self.should_exit_position(current_price, current_atr)
                    if should_exit:
                        trade = self.close_position(current_price, current_time, reason)
                        self.save_trade_to_db(trade)
                        self.save_state()
                        print(f"✓ Closed {trade['type']} | PnL: ${trade['pnl']:.2f}")
                
                # Check entries
                if not self.position:
                    signal = self.check_signal(df)
                    if signal:
                        if self.open_position(signal, current_time):
                            self.save_state()
                            print(f"🚀 Opened {signal['type']} @ ${signal['price']:.2f}")
                
                self.last_update = datetime.now()
                
                # Print status every 10 iterations
                if iteration % 10 == 0:
                    status = "POSITION OPEN" if self.position else "SCANNING"
                    print(f"[{self.last_update.strftime('%H:%M:%S')}] {status} | "
                          f"${current_price:.2f} | Capital: ${self.capital:.2f}")
                
                time.sleep(update_interval)
                
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(30)
        
        print("\n🛑 Bot stopped")
        self.update_bot_status()
    
    def run(self, update_interval=60):
        """Implementation of abstract run() method - starts the bot"""
        self.start(update_interval)
    
    def start(self, update_interval=60):
        """Start bot with web server"""
        # Start trading in separate thread
        trading_thread = threading.Thread(
            target=self.run_trading_loop,
            args=(update_interval,),
            daemon=True
        )
        trading_thread.start()
        
        # Start Flask server
        print(f"\n🌐 Dashboard: http://localhost:{self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)


if __name__ == "__main__":
    # Parse arguments
    symbol = 'BTC/USDT'
    timeframe = '15m'
    port = 5000
    
    if len(sys.argv) > 1:
        pair = sys.argv[1].upper()
        if '/' not in pair and pair.endswith('USDT'):
            symbol = f"{pair[:-4]}/USDT"
        else:
            symbol = pair
    
    if len(sys.argv) > 2:
        timeframe = sys.argv[2]
    
    if len(sys.argv) > 3:
        port = int(sys.argv[3])
    
    print(f"\n{'='*60}")
    print(f"🤖 PAPER TRADING BOT")
    print(f"{'='*60}")
    print(f"Symbol:    {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Port:      {port}")
    print(f"{'='*60}\n")
    
    # Start bot
    bot = PaperTradingBotAPI(
        symbol=symbol,
        timeframe=timeframe,
        initial_capital=10000,
        leverage=3,
        risk_per_trade=0.02,
        port=port
    )
    
    bot.start(update_interval=60)