import requests
import json
from datetime import datetime
import os, csv
from hehexd_exchange_rates import fetch_exchange_rates
import logging
import locale
from colorama import Fore, Back, Style

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set the log file path
log_file_path = os.path.join(script_dir, 'log.log')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d.%m.%Y %H:%M:%S',
                    filename=log_file_path,
                    filemode='w',
                    encoding='utf-8')
logger = logging.getLogger()

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def json_fund_data(isin):
    logger.debug("-" * 15 + " STARTED json_fund_data " + "-" * 15)
    logger.debug(f'Searching Data for {isin}')
    headers = {
        "Accept": "application/json",
        "Accept-Language": "de",
        "Connection": "keep-alive",
        "OeKB-Platform-Context": "eyJsb25ndWFnZSI6ImRlIiwicGxhdGZvcm0iOiJLTVMiLCJkYXNoYm9hcmQiOiJLTVNfT1VUUFVUIn0=",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Brave\";v=\"122\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }

    allgemeine_daten = None
    fondsmeldungen = None

    # Fetch allgemeine_daten
    url_allgemeine_daten = f"https://my.oekb.at/fond-info/rest/public/stammDaten/fonds/{isin}/allg"
    headers["Referer"] = f"https://my.oekb.at/kapitalmarkt-services/kms-output/fonds-info/sd/af/f?isin={isin}"
    try:
        response = requests.get(url_allgemeine_daten, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        allgemeine_daten = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Abrufen der allgemeinen Daten für ISIN {isin}: {e}")

    # Fetch fondsmeldungen
    url_fondsmeldungen = f"https://my.oekb.at/fond-info/rest/public/steuerMeldung/isin/{isin}"
    headers["Referer"] = f"https://my.oekb.at/kapitalmarkt-services/kms-output/fonds-info/sd/af/f?isin={isin}"
    try:
        response = requests.get(url_fondsmeldungen, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        fondsmeldungen = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Abrufen der Fondsmeldungen für ISIN {isin}: {e}")
    logger.debug("-" * 15 + " FINISHED json_fund_data " + "-" * 15)
    return allgemeine_daten, fondsmeldungen

def json_allgemeine_daten(json_data):
    # Parse the JSON data
    data = json_data
    
    # Extract the required values
    numWkn = data['numWkn']
    txtBezX1 = data['txtBezXl']
    kagName = data['kagName']
    stVer = data['stVer']
    ertragstypBez = data['ertragstypBez']
    waehrung = data['waehrung']
    
    return numWkn, txtBezX1, kagName, stVer, ertragstypBez, waehrung

def json_tax_data_all(json_data):
    logger.debug("-" * 15 + " STARTED json_tax_data_all " + "-" * 15)
    fund_data = json_data
    stm_data_list = []
    if fund_data:
        stm_list = fund_data.get("list", [])
        if not stm_list:
            logger.error("Keine Steuermeldungen verfügbar.")
            return stm_data_list
        
        for stm in stm_list:
            meldeid = stm['stmId']
            meldedat = datetime.strptime(stm['zufluss'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%d.%m.%Y')
            meldetyp = "Jahresdatenmeldung" if stm['jahresdatenmeldung'] == "JA" else "Ausschüttungsmeldung" if stm['jahresdatenmeldung'] == "NEIN" else "Ungültiger Meldetyp"
            sitzland = stm['sitzlandFonds']
            
            # Create dictionary for each record
            stm_data = {
                "MeldeID": meldeid,
                "Meldedatum": meldedat,
                "Meldetyp": meldetyp,
                "Sitzland": sitzland
            }
            # Append dictionary to the list
            stm_data_list.append(stm_data)
    return stm_data_list

def format_json_tax_data_all(json_data):
    formatted_data = ""
    for item in json_data:
        melde_id = item.get("MeldeID")
        meldedatum = item.get("Meldedatum")
        meldetyp = item.get("Meldetyp")
        sitzland = item.get("Sitzland")
        formatted_data += f"Melde-ID: {melde_id}, Meldedatum: {meldedatum}, Meldetyp: {meldetyp}, Sitzland: {sitzland}\n"
    return formatted_data

def json_tax_data_single_year(json_data, jahr):
    logger.debug("-" * 15 + " STARTED json_tax_data_single_year " + "-" * 15)
    fund_data = json_data
    stm_data_list = []
    if fund_data:
        stm_list = fund_data.get("list", [])
        if not stm_list:
            logger.error("Keine Steuermeldungen verfügbar.")
            return stm_data_list
        
        for stm in stm_list:
            meldedat = datetime.strptime(stm['zufluss'], '%Y-%m-%dT%H:%M:%S.%f')
            if meldedat.year == jahr:
                meldeid = stm['stmId']
                meldedat = meldedat.strftime('%d.%m.%Y')
                meldetyp = "Jahresdatenmeldung" if stm['jahresdatenmeldung'] == "JA" else "Ausschüttungsmeldung" if stm['jahresdatenmeldung'] == "NEIN" else "Ungültiger Meldetyp"
                sitzland = stm['sitzlandFonds']
                currency = stm['waehrung']
                
                #LOGGER
                logger.debug(f'Found STM {meldeid} for selected year {jahr}')
                # Create dictionary for each record
                stm_data = {
                    "Steuermelde-ID": meldeid,
                    "Meldedatum": meldedat,
                    "Meldetyp": meldetyp,
                    "Sitzland": sitzland,
                    "Währung der Meldung" : currency,
                }
                # Append dictionary to the list
                stm_data_list.append(stm_data)
    return stm_data_list

def tax_data_year(json_data, isin):
    logger.debug("-" * 15 + " STARTED tax_data_year " + "-" * 15)
    all_tax_data = []
    json_stm_data_list = json_data
    label_stk = [
        "Ausschüttungen 27,5%",
        "Ausschüttungsgleiche Erträge 27,5%",
        "Nicht gemeldete Ausschüttungen",
        "Ausländische Quellensteuer",
        "Anschaffungskostenkorrektur"
    ]
    kennzahlen_stk = [
        "897 oder 898",
        "936 oder 937",
        "897 oder 898",
        "984 oder 998",
        ""
    ]
    for item in json_stm_data_list:
        zufluss_date = datetime.strptime(item['Meldedatum'], '%d.%m.%Y').strftime('%Y-%m-%d')
        stm_id = item['Steuermelde-ID']
        logger.debug(f'Processing Melde-ID {stm_id} with Melde-Dat {zufluss_date}')
        #print(zufluss_date, stm_id)
        url = f"https://my.oekb.at/fond-info/rest/public/steuerMeldung/stmId/{stm_id}/privatAnl"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "de",
            "Connection": "keep-alive",
            "OeKB-Platform-Context": "eyJsb25ndWFnZSI6ImRlIiwicGxhdGZvcm0iOiJLTVMiLCJkYXNoYm9hcmQiOiJLTVNfT1VUUFVUIn0=",
            "Referer": f"https://my.oekb.at/kapitalmarkt-services/kms-output/fonds-info/sd/af/f?isin={isin}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Brave\";v=\"122\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        tax_entry = {
            'Zufluss-Datum': datetime.strptime(zufluss_date, '%Y-%m-%d').strftime('%d.%m.%Y'),
            'Zufluss-Datum_US': zufluss_date,
            'Währung der Meldung':item['Währung der Meldung'],
            'Umrechnungskurs': fetch_exchange_rates(item['Währung der Meldung'],zufluss_date),
            'Melde-ID': str(stm_id),
            'Steuerdaten': []
        }
        for i, item_data in enumerate(data["list"]):
            entry_data = {
                'Bezeichnung': label_stk[i],
                'Kennzahlen': kennzahlen_stk[i],
                'Wert': item_data.get('pvMitOption4', '0.0000') #Nur Privatanleger mit Option | keine Rücksicht auf § 124b Z 186
            }
            tax_entry['Steuerdaten'].append(entry_data)
            logger.debug(f'Added {entry_data} to tax_entry')
        
        all_tax_data.append(tax_entry)

    # Convert the all_tax_data list to JSON
    json_variable = json.dumps(all_tax_data, ensure_ascii=False)
    return json_variable

def export_tax_data_as_csv(json_data, isin):
    logger.debug("-" * 15 + " STARTED EXPORTING " + "-" * 15)
    # Open CSV file for writing
    json_data = json.loads(json_data)
    locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')
    with open('tax_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        
        # Write headers
        writer.writerow(["ISIN", "Melde-ID", "Währung", "Umrechnungskurs", "Ausschüttungen", "Ausschüttungsgleiche Erträge", "Nicht gemeldete Ausschüttungen", "Quellensteuer", "Anschaffungskostenkorrektur"])
        
        # Iterate over each item in the JSON data
        for item in json_data:
            # Initialize variables for each item to ensure they are reset
            ausschüttungen = ausschüttungsgleiche_erträge = nicht_gemeldete_ausschüttungen = quellensteuer = anschaffungskostenkorrektur = 0
            
            # Extract required fields
            melde_id = item["Melde-ID"]  # Convert Melde-ID to integer
            währung = item["Währung der Meldung"]
            umrechnungskurs = locale.format_string("%.4f", item["Umrechnungskurs"])
            steuerdaten = item["Steuerdaten"]
            
            # Loop through tax data to find corresponding values
            for tax_data in steuerdaten:
                if tax_data["Bezeichnung"] == "Ausschüttungen 27,5%":
                    ausschüttungen = locale.format_string("%.4f", tax_data["Wert"])
                elif tax_data["Bezeichnung"] == "Ausschüttungsgleiche Erträge 27,5%":
                    ausschüttungsgleiche_erträge = locale.format_string("%.4f", tax_data["Wert"])
                elif tax_data["Bezeichnung"] == "Nicht gemeldete Ausschüttungen":
                    nicht_gemeldete_ausschüttungen = locale.format_string("%.4f", tax_data["Wert"])
                elif tax_data["Bezeichnung"] == "Ausländische Quellensteuer":
                    quellensteuer = locale.format_string("%.4f", tax_data["Wert"])
                elif tax_data["Bezeichnung"] == "Anschaffungskostenkorrektur":
                    anschaffungskostenkorrektur = locale.format_string("%.4f", tax_data["Wert"])
            
            # Write data to CSV
            writer.writerow([isin, melde_id, währung, umrechnungskurs, ausschüttungen, ausschüttungsgleiche_erträge, nicht_gemeldete_ausschüttungen, quellensteuer, anschaffungskostenkorrektur])
    logger.debug("-" * 15 + " EXPORTING FINISHED " + "-" * 15)

def main():
    print("Welche Art von Daten möchten Sie abrufen?")
    print("1. Allgemeine Daten")
    print("2. Fondsmeldungen")
    print("3. Fondsmeldungen in CSV speichern")
    data_type_input = input("Wählen Sie eine Option (1, 2 oder 3): ")
    
    if data_type_input not in ["1", "2", "3"]:
        print("Ungültige Eingabe.")
        return
    cls()
    print(Fore.GREEN + f'Möchten Sie eine vorgegebene ISIN auswählen oder eine eigene eingeben?')
    print("1. Vorgegebene ISIN auswählen")
    print("2. Eigene ISIN eingeben")
    isin_option = input("Wählen Sie eine Option (1 oder 2): ")

    if isin_option == "1":
        print("Bitte wählen Sie eine vorgegebene ISIN:")
        print("1. iShares Core S&P 500 UCITS ETF (Acc)")
        print("2. iShares STOXX Global Select Dividend 100 UCITS ETF (DE)")
        print("3. iShares Core EUR Corporate Bond UCITS ETF (Dist)")
        isin_selection = input("Wählen Sie eine Option: ")
        predefined_isins = {
            "1": "IE00B5BMR087",
            "2": "DE000A0F5UH1",
            "3": "IE00B3F81R35"
        }
        if isin_selection not in predefined_isins:
            print("Ungültige Auswahl.")
            return
        isin = predefined_isins[isin_selection]
    elif isin_option == "2":
        isin = input("Bitte geben Sie die ISIN des Fonds ein: ")
    else:
        print("Ungültige Auswahl.")
        return
    allgemeine_daten, fondsmeldungen = json_fund_data(isin)
    
    if data_type_input == "1": #Allgemeine Daten
        print(json_allgemeine_daten(allgemeine_daten))
    elif data_type_input == "2": #Fonds-Meldungen
        print(format_json_tax_data_all(json_tax_data_all(fondsmeldungen)))
    elif data_type_input == "3": #Download
        jahr = int(input("Jahr eingeben:"))
        logger.debug(json_tax_data_single_year(fondsmeldungen, jahr))
        export_data = (tax_data_year(json_tax_data_single_year(fondsmeldungen, jahr), isin))
        export_tax_data_as_csv(export_data, isin)
    else:
        print("falsche Auswahl")
    input("\nDrücken Sie die Eingabetaste, um das Programm zu beenden.")

if __name__ == "__main__":
    main()
