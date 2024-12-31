# binance-api-data

Download and Update Historical Data for All Coins on Binance

This project provides a Python script to fetch historical trading data for all available coins on Binance using public API endpoints. The data is saved in individual CSV files for each coin, organized by the 1-minute (1m) time frame. If the crypto_data directory already exists, the script will read the existing CSV files and append new data if available, ensuring no duplication and efficient data updates.

The downloaded data follows this CSV file structure:

csv
timestamp,open,high,low,close,volume  
2020-11-18 03:00:00,0.4904,0.618,0.4904,0.5175,79250.42  

Features
Utilizes Binance's public API (no API key required).
Downloads 1-minute (1m) historical data for all available coins on Binance.
Saves each coin's data into a separate CSV file named after the coin (e.g., BTCUSDT.csv).
Organizes all CSV files into a folder called crypto_data.
If the crypto_data folder already exists:
Reads existing CSV files.
Appends new data to the files, ensuring no data duplication.
Resumes fetching data from the latest available timestamp.
Requirements
Python 3.12 or higher
Internet connection

Install dependencies:

pip install -r requirements.txt  
Usage
Run the script:
python run.py  

The script will:

Fetch historical data for all coins in the 1m time frame.
Create a directory named crypto_data (if it doesn’t already exist).
Save each coin's data in a CSV file within the crypto_data directory.
Append new data to existing CSV files if they already exist, ensuring the data is up to date.
CSV File Naming
Each coin’s data will be saved in a file named after the trading pair, e.g., BTCUSDT.csv, ETHUSDT.csv, etc.

Contributing
Contributions are welcome! Feel free to Suggestions for new features or improvements are appreciated.

