import datetime as dt
import pandas as pd
from helium import *

# Define the URL to scrape
url = 'http://www.freddiemac.com/pmms/'

# Define the filename for the data
filename = 'mortgage_rates_FM.parquet'

# Load the existing data from the file, or create a new empty dataframe
try:
    rates = pd.read_parquet(filename)
except FileNotFoundError:
    rates = pd.DataFrame(columns=['date', '30yr', '15yr'])

# Check if it has been more than a week since the last update
last_update = pd.to_datetime(rates['date'].max())
one_week_ago = pd.to_datetime(dt.date.today() - dt.timedelta(days=7))
if last_update >= one_week_ago:
    print('Mortgage rates are up to date, no need to scrape.')
else:
    # Scrape the website to get the current mortgage rates
    browser = start_firefox(url, headless=True)
    current_rate_30yr = float(Text(below='30-Yr FRM').value.strip('%'))
    current_rate_15yr = float(Text(below='15-Yr FRM').value.strip('%'))
    current_date = dt.date.today()

    # Append the new data to the existing dataframe and save to file
    new_data = pd.DataFrame({'date': [current_date], '30yr': [current_rate_30yr], '15yr': [current_rate_15yr]})
    rates = pd.concat([rates, new_data], ignore_index=True)
    rates.to_parquet(filename)
    print('Mortgage rates updated.')