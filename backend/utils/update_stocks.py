import os
import zipfile
import csv
import json
import glob
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent.parent
BHAV_DIR = BASE_DIR / "data" / "bhavcopy"
# Save to backend's own data directory
OUT_FILE = BASE_DIR / "data" / "stocks.json"

def process_latest_bhavcopy():
    # 1. Find the latest ZIP file
    zip_files = glob.glob(str(BHAV_DIR / "*.zip"))
    if not zip_files:
        print(f"Error: No ZIP files found in {BHAV_DIR}")
        return

    latest_zip = max(zip_files, key=os.path.getctime)
    print(f"Processing: {os.path.basename(latest_zip)}")

    # 2. Extract ZIP
    with zipfile.ZipFile(latest_zip, 'r') as zip_ref:
        extract_path = BHAV_DIR / "temp_extract"
        zip_ref.extractall(extract_path)
        csv_files = glob.glob(str(extract_path / "*.csv"))
        if not csv_files:
            print("Error: No CSV found inside ZIP.")
            return
        
        csv_file = csv_files[0]
        
        # 3. Parse and Filter
        stocks = []
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Normalizing column names as some NSE files have different headers
            for row in reader:
                # Primary filters: Cash Market (CM) and Equity Series (EQ)
                # Note: BhavCopy headers can vary slightly by date, we'll try to be robust
                segment = row.get('Sgmt', row.get('SERIES', ''))
                series = row.get('SctySrs', row.get('SERIES', ''))
                symbol = row.get('TckrSymb', row.get('SYMBOL', ''))
                name = row.get('FinInstrmNm', row.get('NAME', ''))
                
                if segment == 'CM' and series == 'EQ':
                    # Add .NS suffix for Yahoo Finance compatibility
                    stocks.append({
                        "symbol": f"{symbol}.NS",
                        "name": name.strip() if name else symbol,
                        "type": "STOCK"
                    })

        # 4. Save to JSON for Frontend
        os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
        with open(OUT_FILE, 'w', encoding='utf-8') as out:
            json.dump(stocks, out, indent=2)
        
        print(f"Success! {len(stocks)} stocks exported to {OUT_FILE}")

        # Cleanup
        for file in glob.glob(str(extract_path / "*")):
            os.remove(file)
        os.rmdir(extract_path)

if __name__ == "__main__":
    process_latest_bhavcopy()
