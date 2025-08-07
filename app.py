from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_session import Session
import os
import json
from datetime import datetime, timedelta
from database import DatabaseManager
from api_client import PolygonAPIClient
from technical_analysis import TechnicalAnalyzer
import plotly.graph_objects as go
import plotly.utils
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# Initialize components
db = DatabaseManager()
api_client = PolygonAPIClient()
analyzer = TechnicalAnalyzer()

@app.route('/')
def index():
    """Main dashboard page"""
    api_key = session.get('api_key', '')
    watchlist = db.get_watchlist()
    return render_template('index.html', api_key=api_key, watchlist=watchlist)

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    """Set API key in session"""
    api_key = request.form.get('api_key', '').strip()
    if api_key:
        session['api_key'] = api_key
        flash('API key saved successfully!', 'success')
    else:
        flash('Please enter a valid API key.', 'error')
    return redirect(url_for('index'))

@app.route('/add_ticker', methods=['POST'])
def add_ticker():
    """Add ticker to watchlist"""
    ticker = request.form.get('ticker', '').strip().upper()
    asset_type = request.form.get('asset_type', 'Stock')
    
    if ticker:
        success = db.add_stock_to_watchlist(ticker, asset_type)
        if success:
            flash(f'Added {ticker} ({asset_type}) to watchlist!', 'success')
        else:
            flash(f'Error adding {ticker} to watchlist.', 'error')
    else:
        flash('Please enter a ticker symbol.', 'error')
    
    return redirect(url_for('index'))

@app.route('/remove_ticker/<ticker>')
def remove_ticker(ticker):
    """Remove ticker from watchlist"""
    success = db.remove_stock_from_watchlist(ticker)
    if success:
        flash(f'Removed {ticker} from watchlist!', 'success')
    else:
        flash(f'Error removing {ticker} from watchlist.', 'error')
    return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze_watchlist():
    """Analyze all tickers in watchlist against selected criteria"""
    api_key = session.get('api_key')
    if not api_key:
        flash('Please set your API key first.', 'error')
        return redirect(url_for('index'))
    
    # Get selected criteria
    criteria = {
        'avoid_squeeze': 'avoid_squeeze' in request.form,
        'rsi_confirmation': 'rsi_confirmation' in request.form,
        'dmi_confirmation': 'dmi_confirmation' in request.form,
        'ema_crossover': 'ema_crossover' in request.form,
        'macd_crossover': 'macd_crossover' in request.form,
        'weekly_macd': 'weekly_macd' in request.form,
        'next_earning_date': 'next_earning_date' in request.form
    }
    
    watchlist = db.get_watchlist()
    if not watchlist:
        flash('Your watchlist is empty. Please add some tickers first.', 'error')
        return redirect(url_for('index'))
    
    # Analyze each ticker
    results = []
    for ticker_data in watchlist:
        ticker = ticker_data['ticker']
        asset_type = ticker_data['asset_type']
        
        # Initialize API client with key
        api_client.set_api_key(api_key)
        
        # Get current price
        current_price, price_error = api_client.get_current_price(ticker)
        
        # Get data based on asset type
        if asset_type == 'Stock':
            data_df, data_error = api_client.get_weekly_data(ticker)
            daily_df, _ = api_client.get_daily_data(ticker, period_days=90)
        else:  # Option
            data_df, data_error = api_client.get_daily_data(ticker, period_days=90)
            daily_df = data_df.copy()
        
        # Analyze ticker
        result = analyzer.analyze_ticker(
            ticker, asset_type, data_df, daily_df, current_price, criteria, api_client
        )
        
        if result:
            results.append(result)
    
    # Filter for passing tickers
    passing_results = [
        result for result in results 
        if any(value.get('status') in ['✅', '⚠️'] for key, value in result.items() 
               if key not in ['ticker', 'asset_type', 'current_price'])
    ]
    
    return render_template('results.html', results=passing_results, criteria=criteria)

@app.route('/chart/<ticker>/<chart_type>')
def get_chart(ticker, chart_type):
    """Generate and return chart data for a specific ticker"""
    api_key = session.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key not set'})
    
    api_client.set_api_key(api_key)
    
    try:
        # Get ticker data from database
        watchlist = db.get_watchlist()
        ticker_info = next((t for t in watchlist if t['ticker'] == ticker), None)
        
        if not ticker_info:
            return jsonify({'error': 'Ticker not found in watchlist'})
        
        asset_type = ticker_info['asset_type']
        
        # Get appropriate data
        if asset_type == 'Stock':
            weekly_df, _ = api_client.get_weekly_data(ticker)
            daily_df, _ = api_client.get_daily_data(ticker, period_days=90)
        else:
            daily_df, _ = api_client.get_daily_data(ticker, period_days=90)
            weekly_df = daily_df.copy()
        
        # Generate chart based on type
        chart_json = analyzer.generate_chart(ticker, chart_type, daily_df, weekly_df, asset_type)
        
        return jsonify({'chart': chart_json})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/ticker_detail/<ticker>')
def ticker_detail(ticker):
    """Detailed view for a specific ticker"""
    api_key = session.get('api_key')
    if not api_key:
        flash('Please set your API key first.', 'error')
        return redirect(url_for('index'))
    
    # Get ticker from watchlist
    watchlist = db.get_watchlist()
    ticker_info = next((t for t in watchlist if t['ticker'] == ticker), None)
    
    if not ticker_info:
        flash('Ticker not found in watchlist.', 'error')
        return redirect(url_for('index'))
    
    api_client.set_api_key(api_key)
    
    # Get current price
    current_price, price_error = api_client.get_current_price(ticker)
    
    # Get earnings date if it's a stock
    earnings_date = None
    if ticker_info['asset_type'] == 'Stock':
        earnings_date, _ = api_client.get_next_earnings_date(ticker)
    
    return render_template('ticker_detail.html', 
                         ticker=ticker, 
                         ticker_info=ticker_info,
                         current_price=current_price,
                         earnings_date=earnings_date)

if __name__ == '__main__':
    # Initialize database
    db.init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)