Stock Technical Indicator Analyzer
A Flask web application for analyzing stocks and options using RSI and MACD technical indicators.

Features
Stock Analysis: Uses yearly data with weekly intervals
Option Analysis: Uses 90-day data with daily intervals
RSI condition checking (30-60 range, rising trend)
MACD crossover and rising trend detection
Interactive charts for both indicators
Clean, responsive web interface
Installation
Clone or download this repository
Install dependencies:
pip install -r requirements.txt
Running the Application
Local Development
python app.py
The app will be available at http://localhost:5000

Production Deployment
gunicorn -w 4 -b 0.0.0.0:5000 app:app
Usage
Enter a stock ticker symbol (e.g., AAPL, TSLA)
Select analysis type:
Stock: Analyzes yearly data with weekly intervals
Option: Analyzes 90-day data with daily intervals
Click "Run Analysis" to see results
Technical Indicators
RSI (Relative Strength Index)
Calculated using Wilder's method with 14-period default
Condition: RSI between 30-60 and rising
MACD (Moving Average Convergence Divergence)
Uses 12-period fast EMA, 26-period slow EMA, 9-period signal
Condition: MACD line rising or crossing above signal line
File Structure
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Web interface template
├── static/
│   └── style.css      # Styling
└── README.md          # This file
Deployment Notes
This application is designed for easy deployment to platforms like:

Heroku
DigitalOcean App Platform
Railway
Render
The simple file structure makes it suitable for most cloud platforms.
