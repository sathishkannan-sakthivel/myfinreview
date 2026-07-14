import requests
import json
import os

AMFI_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
# Correct path to match backend local data structure
# Since this script is now in backend/utils/, we need to go up one level to reach backend/data/
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "mutualfunds.json")

def refresh_mf_data():
    print(f"Fetching AMFI data and saving to {OUTPUT_FILE}...")
    try:
        response = requests.get(AMFI_URL, timeout=30)
        response.raise_for_status()
        
        lines = response.text.split('\n')
        mf_data = {}
        
        for line in lines:
            if not line.strip() or ';' not in line:
                continue
                
            parts = line.split(';')
            if len(parts) >= 5:
                scheme_code = parts[0].strip()
                scheme_name = parts[3].strip()
                nav = parts[4].strip()
                
                try:
                    nav_float = float(nav)
                    mf_data[scheme_code] = {
                        "name": scheme_name,
                        "nav": nav_float,
                        "updated_at": parts[5].strip() if len(parts) > 5 else ""
                    }
                except ValueError:
                    continue
        
        # Ensure the directory exists
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(mf_data, f)
            
        print(f"Successfully saved {len(mf_data)} Mutual Funds.")
        return mf_data
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    refresh_mf_data()
