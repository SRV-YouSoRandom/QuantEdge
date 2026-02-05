import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from abc import ABC, abstractmethod

class TradingEngine(ABC):
    """
    Core Trading Engine - Human-Like Pattern Recognition
    Trades like a discretionary trader: context + momentum + support/resistance
    """
    
    def __init__(self, symbol='BTC/USDT', timeframe='15m', initial_capital=10000, 
                 leverage=3, risk_per_trade=0.02):
        """
        Initialize Trading Engine with Balanced Approach
        
        Parameters:
        - symbol: Trading pair
        - timeframe: 15m for good balance
        - leverage: 3x moderate leverage
        - risk_per_trade: 2% per trade
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.leverage = leverage
        self.risk_per_trade = risk_per_trade
        
        # BALANCED INDICATOR PARAMETERS
        self.ema_short = 12
        self.ema_mid = 26
        self.ema_long = 50
        
        self.rsi_period = 14
        self.bb_period = 20
        self.bb_std = 2
        self.atr_period = 14
        
        # Risk settings
        self.stop_atr_multiplier = 2.0
        self.target_atr_multiplier = 3.5  # 1.75:1 R:R
        self.trailing_activation = 1.5  # Activate trailing at 1.5% profit
        
        self.max_trades_per_day = 8
        self.daily_loss_limit = 0.08
        
        # Trading State
        self.position = None
        self.trades = []
        self.daily_pnl = 0
        self.daily_trade_count = 0
        self.last_trade_date = None
        
    def calculate_indicators(self, df):
        """Calculate indicators for pattern recognition"""
        # EMAs
        df['ema_short'] = EMAIndicator(df['close'], window=self.ema_short).ema_indicator()
        df['ema_mid'] = EMAIndicator(df['close'], window=self.ema_mid).ema_indicator()
        df['ema_long'] = EMAIndicator(df['close'], window=self.ema_long).ema_indicator()
        
        # RSI
        df['rsi'] = RSIIndicator(df['close'], window=self.rsi_period).rsi()
        
        # MACD
        macd = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_hist'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = BollingerBands(df['close'], window=self.bb_period, window_dev=self.bb_std)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_mid'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_pband'] = bb.bollinger_pband()  # % position in band
        
        # ATR
        df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], 
                                     window=self.atr_period).average_true_range()
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        
        # Volume
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price action patterns
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['range'] = df['high'] - df['low']
        
        # Support/Resistance levels
        df['swing_high'] = df['high'].rolling(window=10, center=True).max()
        df['swing_low'] = df['low'].rolling(window=10, center=True).min()
        
        # Momentum
        df['price_change'] = df['close'].pct_change() * 100
        df['momentum_3'] = df['close'].pct_change(3) * 100
        
        # Trend context
        df['ema_alignment_bull'] = (df['ema_short'] > df['ema_mid']) & (df['ema_mid'] > df['ema_long'])
        df['ema_alignment_bear'] = (df['ema_short'] < df['ema_mid']) & (df['ema_mid'] < df['ema_long'])
        
        return df.dropna()
    
    def check_signal(self, df, i=None):
        """
        Human-like pattern recognition
        Looks for: context + setup + trigger (like a real trader)
        """
        if i is None:
            i = -1
        
        if i < 5:  # Need lookback
            return None
            
        current = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]
        
        # Reset daily limits
        if self.last_trade_date and self.last_trade_date != current.name.date():
            self.daily_trade_count = 0
            self.daily_pnl = 0
        
        if self.daily_trade_count >= self.max_trades_per_day:
            return None
        
        if self.daily_pnl < -self.daily_loss_limit * self.capital:
            return None
        
        # === PATTERN 1: TREND PULLBACK ===
        # Context: Strong trend, Setup: Pullback to EMA, Trigger: Momentum shift
        
        # LONG: Uptrend pullback
        uptrend_context = current['ema_alignment_bull'] or (current['ema_short'] > current['ema_long'])
        
        pullback_complete = (
            prev2['close'] < prev2['ema_short'] and  # Was below EMA
            prev['close'] < prev['ema_short'] and
            current['close'] > current['ema_short']  # Now reclaimed
        )
        
        rsi_oversold_recovery = prev['rsi'] < 45 and current['rsi'] > 45
        
        macd_turning = current['macd_hist'] > prev['macd_hist']
        
        bullish_momentum = current['price_change'] > 0 and current['body'] > current['range'] * 0.5
        
        if uptrend_context and (pullback_complete or rsi_oversold_recovery) and (macd_turning or bullish_momentum):
            return {
                'type': 'long',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'trend_pullback',
                'confidence': 0.7
            }
        
        # SHORT: Downtrend pullback
        downtrend_context = current['ema_alignment_bear'] or (current['ema_short'] < current['ema_long'])
        
        rally_complete = (
            prev2['close'] > prev2['ema_short'] and
            prev['close'] > prev['ema_short'] and
            current['close'] < current['ema_short']
        )
        
        rsi_overbought_rejection = prev['rsi'] > 55 and current['rsi'] < 55
        
        macd_weakening = current['macd_hist'] < prev['macd_hist']
        
        bearish_momentum = current['price_change'] < 0 and current['body'] > current['range'] * 0.5
        
        if downtrend_context and (rally_complete or rsi_overbought_rejection) and (macd_weakening or bearish_momentum):
            return {
                'type': 'short',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'trend_pullback',
                'confidence': 0.7
            }
        
        # === PATTERN 2: MEAN REVERSION ===
        # Bollinger Band extremes in ranging market
        
        ranging = not current['ema_alignment_bull'] and not current['ema_alignment_bear']
        
        # LONG: BB lower extreme bounce
        at_lower_bb = current['bb_pband'] < 0.15  # In lower 15% of band
        rsi_oversold = current['rsi'] < 35
        hammer_candle = current['lower_wick'] > current['body'] * 1.5
        
        if ranging and at_lower_bb and rsi_oversold and (hammer_candle or current['price_change'] > 0):
            return {
                'type': 'long',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'bb_bounce',
                'confidence': 0.6
            }
        
        # SHORT: BB upper extreme rejection
        at_upper_bb = current['bb_pband'] > 0.85
        rsi_overbought = current['rsi'] > 65
        shooting_star = current['upper_wick'] > current['body'] * 1.5
        
        if ranging and at_upper_bb and rsi_overbought and (shooting_star or current['price_change'] < 0):
            return {
                'type': 'short',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'bb_rejection',
                'confidence': 0.6
            }
        
        # === PATTERN 3: MOMENTUM BREAKOUT ===
        # Price breaking above/below consolidation with volume
        
        # LONG: Upside breakout
        consolidating = df['high'].iloc[i-5:i].max() - df['low'].iloc[i-5:i].min() < current['atr'] * 3
        
        breaking_higher = current['close'] > df['high'].iloc[i-5:i-1].max()
        
        volume_surge = current['volume_ratio'] > 1.5
        
        macd_bullish = current['macd'] > current['macd_signal']
        
        if consolidating and breaking_higher and volume_surge and macd_bullish:
            return {
                'type': 'long',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'breakout',
                'confidence': 0.8
            }
        
        # SHORT: Downside breakdown
        breaking_lower = current['close'] < df['low'].iloc[i-5:i-1].min()
        
        macd_bearish = current['macd'] < current['macd_signal']
        
        if consolidating and breaking_lower and volume_surge and macd_bearish:
            return {
                'type': 'short',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'breakdown',
                'confidence': 0.8
            }
        
        # === PATTERN 4: SIMPLE MOMENTUM ===
        # When all else fails, ride strong momentum
        
        # LONG: Strong upward momentum
        strong_green_candle = (current['close'] > current['open'] and 
                              current['body'] > current['range'] * 0.7 and
                              current['price_change'] > 0.5)
        
        rsi_bullish = 40 < current['rsi'] < 70
        ema_support = current['close'] > current['ema_mid']
        
        if strong_green_candle and rsi_bullish and ema_support and current['volume_ratio'] > 1.2:
            return {
                'type': 'long',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'momentum',
                'confidence': 0.5
            }
        
        # SHORT: Strong downward momentum
        strong_red_candle = (current['close'] < current['open'] and
                            current['body'] > current['range'] * 0.7 and
                            current['price_change'] < -0.5)
        
        rsi_bearish = 30 < current['rsi'] < 60
        ema_resistance = current['close'] < current['ema_mid']
        
        if strong_red_candle and rsi_bearish and ema_resistance and current['volume_ratio'] > 1.2:
            return {
                'type': 'short',
                'price': current['close'],
                'atr': current['atr'],
                'pattern': 'momentum',
                'confidence': 0.5
            }
        
        return None
    
    def calculate_position_size(self, entry_price, stop_loss_price, confidence=1.0):
        """Position sizing with confidence adjustment"""
        risk_amount = self.capital * self.risk_per_trade * confidence
        stop_distance = abs(entry_price - stop_loss_price)
        
        if stop_distance == 0:
            return 0
        
        position_size = (risk_amount / stop_distance) * self.leverage
        
        # Cap at 50% of capital
        max_position = self.capital * self.leverage * 0.5
        return min(position_size, max_position)
    
    def calculate_stops(self, entry_price, signal_type, atr):
        """Calculate stops based on ATR"""
        if signal_type == 'long':
            stop_loss = entry_price - (atr * self.stop_atr_multiplier)
            take_profit = entry_price + (atr * self.target_atr_multiplier)
        else:
            stop_loss = entry_price + (atr * self.stop_atr_multiplier)
            take_profit = entry_price - (atr * self.target_atr_multiplier)
        
        return stop_loss, take_profit
    
    def calculate_liquidation_price(self, entry_price, position_type):
        """Calculate liquidation price"""
        if position_type == 'long':
            return entry_price * (1 - 0.9 / self.leverage)
        else:
            return entry_price * (1 + 0.9 / self.leverage)
    
    def should_exit_position(self, current_price, current_atr=None):
        """Exit logic with trailing stop"""
        if not self.position:
            return False, None
        
        position_type = self.position['type']
        entry_price = self.position['entry_price']
        stop_loss = self.position['stop_loss']
        take_profit = self.position['take_profit']
        liquidation = self.position['liquidation_price']
        
        # Calculate current P&L %
        if position_type == 'long':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Liquidation
        if position_type == 'long' and current_price <= liquidation:
            return True, 'LIQUIDATION'
        if position_type == 'short' and current_price >= liquidation:
            return True, 'LIQUIDATION'
        
        # Trailing stop activation
        if current_atr and pnl_pct > self.trailing_activation:
            if position_type == 'long':
                trailing = current_price - (current_atr * self.stop_atr_multiplier * 0.75)
                if 'trailing_stop' not in self.position or trailing > self.position['trailing_stop']:
                    self.position['trailing_stop'] = trailing
                if current_price <= self.position['trailing_stop']:
                    return True, 'TRAILING_STOP'
            else:
                trailing = current_price + (current_atr * self.stop_atr_multiplier * 0.75)
                if 'trailing_stop' not in self.position or trailing < self.position['trailing_stop']:
                    self.position['trailing_stop'] = trailing
                if current_price >= self.position['trailing_stop']:
                    return True, 'TRAILING_STOP'
        
        # Regular stops
        if position_type == 'long':
            if current_price <= stop_loss:
                return True, 'STOP_LOSS'
            if current_price >= take_profit:
                return True, 'TAKE_PROFIT'
        else:
            if current_price >= stop_loss:
                return True, 'STOP_LOSS'
            if current_price <= take_profit:
                return True, 'TAKE_PROFIT'
        
        return False, None
    
    def open_position(self, signal, timestamp):
        """Open position"""
        entry_price = signal['price']
        position_type = signal['type']
        atr = signal['atr']
        confidence = signal.get('confidence', 1.0)
        pattern = signal.get('pattern', 'unknown')
        
        stop_loss, take_profit = self.calculate_stops(entry_price, position_type, atr)
        position_size = self.calculate_position_size(entry_price, stop_loss, confidence)
        
        if position_size <= 0:
            return False
        
        liquidation_price = self.calculate_liquidation_price(entry_price, position_type)
        
        self.position = {
            'type': position_type,
            'entry_price': entry_price,
            'size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'liquidation_price': liquidation_price,
            'entry_time': timestamp,
            'entry_capital': self.capital,
            'confidence': confidence,
            'pattern': pattern
        }
        
        self.daily_trade_count += 1
        self.last_trade_date = timestamp if hasattr(timestamp, 'date') else None
        
        return True
    
    def close_position(self, exit_price, timestamp, reason):
        """Close position"""
        if not self.position:
            return None
        
        position_type = self.position['type']
        entry_price = self.position['entry_price']
        size = self.position['size']
        
        if position_type == 'long':
            pnl = (exit_price - entry_price) * size
        else:
            pnl = (entry_price - exit_price) * size
        
        if reason == 'LIQUIDATION':
            pnl = -self.position['entry_capital'] * 0.9
        
        self.capital += pnl
        pnl_percent = (pnl / self.position['entry_capital']) * 100
        self.daily_pnl += pnl
        
        trade_record = {
            'entry_time': self.position['entry_time'],
            'exit_time': timestamp,
            'type': position_type,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'size': size,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'reason': reason,
            'pattern': self.position.get('pattern', 'unknown')
        }
        
        self.trades.append(trade_record)
        self.position = None
        
        return trade_record
    
    def analyze_performance(self):
        """Analyze performance"""
        if not self.trades:
            return None
        
        trades_df = pd.DataFrame(self.trades)
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100
        
        total_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(trades_df[trades_df['pnl'] <= 0]['pnl'].sum())
        net_profit = trades_df['pnl'].sum()
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = abs(trades_df[trades_df['pnl'] <= 0]['pnl'].mean()) if losing_trades > 0 else 0
        
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)
        
        returns = trades_df['pnl_percent'] / 100
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        # Max consecutive losses
        trades_df['is_loss'] = trades_df['pnl'] <= 0
        trades_df['loss_streak'] = trades_df['is_loss'].groupby(
            (trades_df['is_loss'] != trades_df['is_loss'].shift()).cumsum()
        ).cumsum()
        max_consecutive_losses = trades_df['loss_streak'].max() if len(trades_df) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'net_profit': net_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'sharpe_ratio': sharpe,
            'max_consecutive_losses': max_consecutive_losses,
            'roi': ((self.capital - self.initial_capital) / self.initial_capital) * 100
        }
    
    @abstractmethod
    def run(self):
        pass