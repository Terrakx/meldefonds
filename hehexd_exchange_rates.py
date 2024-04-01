import requests
import xml.etree.ElementTree as ET

# List of valid currency codes
VALID_CURRENCIES = ['EUR', 'USD', 'GBP', 'JPY', 'HUF', 'SEK', 'NOK', 'RON', 'BGN','CHF','CZK','PLN','DKK','HRK','CNY','INR','KRW', 'TRY','RUB','MXN','CAD','BRL','AUD',]  # Add more currencies as needed

def fetch_exchange_rates(currency, date):
    if currency == 'EUR':
        return 1
    if currency not in VALID_CURRENCIES:
        raise ValueError(f"Invalid currency: {currency}")
    entrypoint = 'https://data-api.ecb.europa.eu/service/'
    resource = 'data'
    flowRef = 'EXR'
    key = f'D.{currency}.EUR.SP00.A'
    parameters = {
        'startPeriod': date,
        'endPeriod': date
    }
    request_url = entrypoint + resource + '/' + flowRef + '/' + key

    response = requests.get(request_url, params=parameters)

    if response.status_code == 200:
        root = ET.fromstring(response.text)
        for obs in root.findall('.//{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Obs'):
            obs_dimension = obs.find('{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsDimension')
            obs_value = obs.find('{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsValue')
            
            if obs_dimension is not None and obs_value is not None:
                return obs_value.attrib['value']

    else:
        return "Exception"

def fetch_exchange_rates_period(currency, date_start, date_end):
    if currency == 'EUR':
        return 1
    if currency not in VALID_CURRENCIES:
        raise ValueError(f"Invalid currency: {currency}")
    entrypoint = 'https://data-api.ecb.europa.eu/service/'
    resource = 'data'
    flowRef = 'EXR'
    key = f'D.{currency}.EUR.SP00.A'
    parameters = {
        'startPeriod': date_start,
        'endPeriod': date_end
    }
    request_url = entrypoint + resource + '/' + flowRef + '/' + key

    response = requests.get(request_url, params=parameters)
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        for obs in root.findall('.//{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Obs'):
            obs_dimension = obs.find('{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsDimension')
            obs_value = obs.find('{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsValue')
            
            if obs_dimension is not None and obs_value is not None:
                print(f"Datum: {obs_dimension.attrib['value']}")
                print(f"Kurs: {obs_value.attrib['value']} {currency}/1.0000 EUR")
                print("-" * 20)
    else:
        return "Exception"

if __name__ == "__main__":
    try:
        print(fetch_exchange_rates('EUR', '2024-03-01'))
        print(fetch_exchange_rates_period('AUD', '2024-03-01','2024-03-11'))
    except ValueError as e:
        print(e)
