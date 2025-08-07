import pandas as pd
import numpy as np
from ta.trend import ADXIndicator
import plotly.graph_objects as go
import plotly.utils
import json
from typing import Dict, Any, Optional, Tuple

class TechnicalAnalyzer:
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI using Wilder's method"""
        if 'Close' not in df.columns or len(df) < period:
            return pd.Series(dtype='float64')
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def check_rsi_condition(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check if RSI is between 30-60 and rising"""
        if 'RSI' not in df.columns or len(df['RSI'].dropna()) < 2:
            return {"status": "❌", "message": "Not enough RSI data", "value": None}
        
        recent_rsi = df['RSI'].dropna().iloc[-2:]
        current_rsi = recent_rsi.iloc[-1]
        previous_rsi = recent_rsi.iloc[-2]
        
        is_in_range = (30 <= current_rsi <= 60) and (30 <= previous_rsi <= 60)
        is_rising = current_rsi > previous_rsi
        
        if is_in_range and is_rising:
            return {
                "status": "✅", 
                "message": f"RSI is between 30-60 and rising ({current_rsi:.2f})",
                "value": current_rsi
            }
        return {
            "status": "❌", 
            "message": f"RSI condition not met ({current_rsi:.2f})",
            "value": current_rsi
        }
    
    def get_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD and Signal Line"""
        if len(data) < slow:
            return pd.Series(dtype='float64'), pd.Series(dtype='float64')
        
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal_period, adjust=False).mean()
        return macd, signal_line
    
    def check_macd_crossover_or_rising(self, macd: pd.Series, signal: pd.Series) -> Dict[str, Any]:
        """Check for bullish MACD crossover or rising MACD"""
        macd = macd.dropna()
        signal = signal.dropna()
        
        if len(macd) < 2 or len(signal) < 2:
            return {"status": "❌", "message": "Not enough MACD data", "value": None}
        
        macd_last = float(macd.iloc[-1])
        macd_prev = float(macd.iloc[-2])
        signal_last = float(signal.iloc[-1])
        signal_prev = float(signal.iloc[-2])
        
        crossover = (macd_last > signal_last) and (macd_prev <= signal_prev)
        is_rising = macd_last > macd_prev
        
        if crossover or is_rising:
            return {
                "status": "✅", 
                "message": "MACD is rising or has crossed above the signal line",
                "value": {"macd": macd_last, "signal": signal_last}
            }
        return {
            "status": "❌", 
            "message": "MACD condition not met",
            "value": {"macd": macd_last, "signal": signal_last}
        }
    
    def check_dmi_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for bullish DMI trend confirmation"""
        if len(df) < 28:
            return {"status": "❌", "message": "Not enough data for DMI calculation", "value": None}
        
        try:
            adx = ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
            adx_values = adx.adx()
            plus_di = adx.adx_pos()
            minus_di = adx.adx_neg()
            
            last_adx = float(adx_values.iloc[-1])
            last_plus_di = float(plus_di.iloc[-1])
            last_minus_di = float(minus_di.iloc[-1])
            
            if last_adx > 20 and last_plus_di > last_minus_di:
                return {
                    "status": "✅",
                    "message": f"Bullish DMI trend confirmed (ADX: {last_adx:.2f})",
                    "value": {"adx": last_adx, "plus_di": last_plus_di, "minus_di": last_minus_di}
                }
            return {
                "status": "❌",
                "message": f"DMI condition not met (ADX: {last_adx:.2f})",
                "value": {"adx": last_adx, "plus_di": last_plus_di, "minus_di": last_minus_di}
            }
        except Exception as e:
            return {"status": "❌", "message": f"Error calculating DMI: {e}", "value": None}
    
    def check_ema_crossover(self, df: pd.DataFrame, fast: int = 8, slow: int = 21) -> Dict[str, Any]:
        """Check for bullish EMA crossover"""
        if len(df) < slow:
            return {"status": "❌", "message": "Not enough data for EMA calculation", "value": None}
        
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        
        if len(df) < 2:
            return {"status": "❌", "message": "Not enough data to check for crossover", "value": None}
        
        prev_fast = float(ema_fast.iloc[-2])
        prev_slow = float(ema_slow.iloc[-2])
        curr_fast = float(ema_fast.iloc[-1])
        curr_slow = float(ema_slow.iloc[-1])
        
        if (prev_fast <= prev_slow) and (curr_fast > curr_slow):
            return {
                "status": "✅",
                "message": "EMA 8 just crossed above EMA 21",
                "value": {"ema_fast": curr_fast, "ema_slow": curr_slow}
            }
        return {
            "status": "❌",
            "message": "No recent bullish EMA crossover",
            "value": {"ema_fast": curr_fast, "ema_slow": curr_slow}
        }
    
    def check_short_squeeze_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for potential short squeeze risk"""
        if len(df) < 30:
            return {"status": "❌", "message": "Not enough data for squeeze analysis", "value": None}
        
        try:
            ma20 = df['Close'].rolling(window=20).mean()
            volume_avg20 = df['Volume'].rolling(window=20).mean()
            rvol = df['Volume'] / volume_avg20
            resistance = df['Close'].rolling(window=30).max().shift(1)
            
            last_row = df.iloc[-1]
            last_close = float(last_row['Close'])
            last_resistance = float(resistance.iloc[-1])
            last_rvol = float(rvol.iloc[-1])
            
            has_breakout = (last_close > last_resistance) and (last_rvol > 2)
            
            if has_breakout:
                return {
                    "status": "⚠️",
                    "message": f"Potential short squeeze risk detected! Price broke resistance on high relative volume (RVOL: {last_rvol:.2f})",
                    "value": {"rvol": last_rvol, "resistance": last_resistance, "price": last_close}
                }
            return {
                "status": "✅",
                "message": "No major short squeeze risk detected",
                "value": {"rvol": last_rvol, "resistance": last_resistance, "price": last_close}
            }
        except Exception as e:
            return {"status": "❌", "message": f"Error analyzing squeeze risk: {e}", "value": None}
    
    def analyze_ticker(self, ticker: str, asset_type: str, data_df: pd.DataFrame, 
                      daily_df: pd.DataFrame, current_price: float, criteria: dict, api_client) -> Optional[Dict[str, Any]]:
        """Analyze a single ticker against all selected criteria"""
        result = {
            "ticker": ticker,
            "asset_type": asset_type,
            "current_price": {"value": current_price, "formatted": f"${current_price:.2f}" if current_price else "N/A"}
        }
        
        # Run analyses based on criteria
        if not data_df.empty:
            if criteria.get('rsi_confirmation'):
                data_df['RSI'] = self.calculate_rsi(data_df)
                result['rsi_confirmation'] = self.check_rsi_condition(data_df)
            
            if criteria.get('dmi_confirmation') and asset_type == 'Stock':
                result['dmi_confirmation'] = self.check_dmi_trend(daily_df)
            
            if criteria.get('ema_crossover') and asset_type == 'Stock':
                result['ema_crossover'] = self.check_ema_crossover(daily_df)
            
            if criteria.get('macd_crossover') and asset_type == 'Stock':
                daily_macd, daily_signal = self.get_macd(daily_df, fast=8, slow=21, signal_period=9)
                result['macd_crossover'] = self.check_macd_crossover_or_rising(daily_macd, daily_signal)
            
            if criteria.get('weekly_macd') and asset_type == 'Stock':
                weekly_macd, weekly_signal = self.get_macd(data_df)
                result['weekly_macd'] = self.check_macd_crossover_or_rising(weekly_macd, weekly_signal)
            
            if criteria.get('avoid_squeeze') and asset_type == 'Stock':
                result['avoid_squeeze'] = self.check_short_squeeze_risk(daily_df)
        
        if criteria.get('next_earning_date') and asset_type == 'Stock':
            earnings_date, earnings_error = api_client.get_next_earnings_date(ticker)
            result['next_earning_date'] = {
                "status": "✅" if earnings_date else "❌",
                "message": earnings_date if earnings_date else earnings_error,
                "value": earnings_date
            }
        
        return result
    
    def generate_chart(self, ticker: str, chart_type: str, daily_df: pd.DataFrame, 
                      weekly_df: pd.DataFrame, asset_type: str) -> str:
        """Generate Plotly chart JSON for a specific chart type"""
        fig = go.Figure()
        
        try:
            if chart_type == 'rsi' and not daily_df.empty:
                rsi = self.calculate_rsi(daily_df)
                fig.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=rsi,
                    mode='lines',
                    name='RSI',
                    line=dict(color='purple')
                ))
                fig.add_hline(y=70, line_dash="dash", line_color="red")
                fig.add_hline(y=30, line_dash="dash", line_color="green")
                fig.update_layout(title=f'{ticker} RSI', yaxis_title='RSI')
            
            elif chart_type == 'macd' and not daily_df.empty:
                macd, signal = self.get_macd(daily_df, fast=8, slow=21, signal_period=9)
                fig.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=macd,
                    mode='lines',
                    name='MACD',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=signal,
                    mode='lines',
                    name='Signal',
                    line=dict(color='red')
                ))
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                fig.update_layout(title=f'{ticker} Daily MACD', yaxis_title='MACD')
            
            elif chart_type == 'weekly_macd' and not weekly_df.empty:
                macd, signal = self.get_macd(weekly_df)
                fig.add_trace(go.Scatter(
                    x=weekly_df.index,
                    y=macd,
                    mode='lines',
                    name='Weekly MACD',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=weekly_df.index,
                    y=signal,
                    mode='lines',
                    name='Weekly Signal',
                    line=dict(color='red')
                ))
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                fig.update_layout(title=f'{ticker} Weekly MACD', yaxis_title='MACD')
            
            elif chart_type == 'ema' and not daily_df.empty:
                ema8 = daily_df['Close'].ewm(span=8, adjust=False).mean()
                ema21 = daily_df['Close'].ewm(span=21, adjust=False).mean()
                
                fig.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=daily_df['Close'],
                    mode='lines',
                    name='Close Price',
                    line=dict(color='black')
                ))
                fig.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=ema8,
                    mode='lines',
                    name='EMA 8',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=ema21,
                    mode='lines',
                    name='EMA 21',
                    line=dict(color='red')
                ))
                fig.update_layout(title=f'{ticker} EMA Crossover', yaxis_title='Price')
            
            elif chart_type == 'dmi' and not daily_df.empty:
                adx = ADXIndicator(high=daily_df['High'], low=daily_df['Low'], close=daily_df['Close'], window=14)
                
                fig.add_trace(go.Scatter(
                    x=daily_df.index[-60:],
                    y=adx.adx_pos().iloc[-60:],
                    mode='lines',
                    name='+DI',
                    line=dict(color='green')
                ))
                fig.add_trace(go.Scatter(
                    x=daily_df.index[-60:],
                    y=adx.adx_neg().iloc[-60:],
                    mode='lines',
                    name='-DI',
                    line=dict(color='red')
                ))
                fig.add_trace(go.Scatter(
                    x=daily_df.index[-60:],
                    y=adx.adx().iloc[-60:],
                    mode='lines',
                    name='ADX',
                    line=dict(color='blue')
                ))
                fig.add_hline(y=20, line_dash="dash", line_color="gray")
                fig.update_layout(title=f'{ticker} DMI Indicators (Last 60 Days)', yaxis_title='DMI')
            
            # Update layout for all charts
            fig.update_layout(
                template='plotly_dark',
                height=400,
                margin=dict(l=40, r=40, t=40, b=40),
                showlegend=True
            )
            
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
        except Exception as e:
            # Return empty chart with error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error generating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            fig.update_layout(template='plotly_dark', height=400)
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)