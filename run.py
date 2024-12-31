import ccxt
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import time
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Binance exchange configureren
exchange = ccxt.binance({
    'rateLimit': 1200,  # API rate limit
    'enableRateLimit': True,
    'timeout': 10050,   # 10 seconden timeout
})

# Blacklist van munten die niet gedownload moeten worden
blacklist = []

# Controleer of de gegevensmap bestaat, zo niet, maak deze aan
data_folder = 'crypto_data'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# Begin- en eindtijd in milliseconden
timeframe = '1m'
since = exchange.parse8601('2000-08-11T00:00:00Z')
end_time = exchange.milliseconds()
limit = 500
batch_size = 20000  # Aantal candles per bestand

# Functie om gegevens op te halen in batches
def fetch_ohlcv(symbol, timeframe, since, limit=500):
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            return ohlcv
        except ccxt.RequestTimeout:
            logger.warning(f"Timeout bij ophalen van data voor {symbol}. Wacht 5 seconden en probeer opnieuw...")
            time.sleep(5)
        except ccxt.NetworkError as e:
            logger.error(f"Netwerkfout bij ophalen van data voor {symbol}: {e}. Wacht 5 seconden en probeer opnieuw...")
            time.sleep(5)
        except ccxt.ExchangeError as e:
            logger.error(f"Fout bij ophalen van data voor {symbol}: {e}. Wacht 5 seconden en probeer opnieuw...")
            time.sleep(5)

# Alle beschikbare markten/cryptoparen ophalen
try:
    markets = exchange.load_markets()
except ccxt.NetworkError as e:
    logger.error(f"Netwerkfout bij ophalen van markten: {e}")
    exit()
except ccxt.ExchangeError as e:
    logger.error(f"Fout bij ophalen van markten: {e}")
    exit()

# Lijst van USDT-paren verzamelen, exclusief de munten in de blacklist
usdt_pairs = [symbol for symbol in markets.keys() if '/USDT' in symbol and symbol not in blacklist]

# Lijst van cryptomunten weergeven die zullen worden gedownload
logger.info("De volgende cryptoparen zullen worden gedownload (exclusief blacklist):")
for pair in usdt_pairs:
    logger.info(pair)

# Voor elk handelspaar gegevens ophalen
for symbol in usdt_pairs:
    logger.info(f"\nOphalen van gegevens voor {symbol}...")

    all_ohlcv = []
    candles_processed = 0

    # Genereer een geldig bestandspad, vervang '/' door '_'
    sanitized_symbol = symbol.replace("/", "_")
    output_file = os.path.join(data_folder, f'{sanitized_symbol}_1m_data.csv')
    
    # Check if the CSV file exists and resume from the last timestamp
    if os.path.exists(output_file):
        df_existing = pd.read_csv(output_file)
        if not df_existing.empty:
            last_timestamp = pd.to_datetime(df_existing['timestamp']).max()
            current_since = last_timestamp.value // 10**6 + 60000  # Start from the next minute
            logger.info(f"Resuming from {datetime.utcfromtimestamp(current_since / 1000)}")
        else:
            current_since = since
    else:
        current_since = since

    # Voortgangsbalk instellen
    pbar = tqdm(desc=f'Fetching data for {symbol}', unit='1m')

    while True:
        ohlcv = fetch_ohlcv(symbol, timeframe, current_since, limit)
        if not ohlcv:
            logger.info(f"Geen nieuwe data meer voor {symbol}, stoppen met downloaden.")
            break
        
        all_ohlcv.extend(ohlcv)
        candles_processed += len(ohlcv)
        current_since = ohlcv[-1][0] + 60000  # Volgende batch begint na de laatste datum

        # Update voortgangsbalk
        pbar.update(len(ohlcv))
        
        # Als het aantal verwerkte candles de batchgrootte overschrijdt, sla de gegevens op
        if candles_processed >= batch_size:
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            write_mode = 'w' if not os.path.exists(output_file) else 'a'
            header = not os.path.exists(output_file)

            try:
                df.to_csv(output_file, mode=write_mode, header=header, index=False)
                logger.info(f"Gegevens voor {symbol} opgeslagen in '{output_file}' met {len(df)} rijen.")
            except OSError as e:
                logger.error(f"Fout bij opslaan van gegevens voor {symbol}: {e}")
                break
            
            # Reset voor de volgende batch
            all_ohlcv = []
            candles_processed = 0
        
        # Even wachten om de rate limit van Binance niet te overschrijden
        time.sleep(exchange.rateLimit / 1000)

    # Opslaan van overgebleven gegevens als er nog candles zijn die niet zijn opgeslagen
    if all_ohlcv:
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        write_mode = 'a' if os.path.exists(output_file) else 'w'
        try:
            df.to_csv(output_file, mode=write_mode, header=not os.path.exists(output_file), index=False)
            logger.info(f"Gegevens voor {symbol} opgeslagen in '{output_file}' met {len(df)} rijen.")
        except OSError as e:
            logger.error(f"Fout bij opslaan van gegevens voor {symbol}: {e}")

    # Voortgangsbalk sluiten
    pbar.close()
