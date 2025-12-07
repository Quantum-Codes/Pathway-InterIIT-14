import csv
import time
import requests
import os
from dotenv import load_dotenv
import sys 

# Load environment variables from a .env file
load_dotenv()

def get_google_links(query, api_key, pse_id):
    """
    Searches Google using the official API and returns a list of links.
    This function will RAISE an exception if the API call fails.
    """
    print(f"Searching API for: {query}")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': pse_id,
        'q': query,
        'num': 2
    }
    
    # Make the request. If this fails (4xx, 5xx), it will raise an error.
    response = requests.get(url, params=params)
    response.raise_for_status() 
    
    results = response.json()
    links = []
    
    if 'items' in results:
        for item in results['items']:
            links.append(item['link'])
            
    return links

# # --- Command-line input handling ---
# if len(sys.argv) < 2:
#     print("Usage: python adverse_media_finder.py <csv_file>")
#     print("Example: python adverse_media_finder.py people.csv")
#     sys.exit(1)

# csv_file = sys.argv[1]

# # Check if file exists
# if not os.path.isfile(csv_file):
#     print(f"Error: File '{csv_file}' not found.")
#     sys.exit(1)

# # Extract names from CSV
# kyc_names = []
# try:
#     with open(csv_file, 'r', encoding='utf-8') as f:
#         csv_reader = csv.DictReader(f)
#         if csv_reader.fieldnames is None or 'name' not in csv_reader.fieldnames:
#             print("Error: CSV file must contain a 'name' column.")
#             sys.exit(1)
        
#         for row in csv_reader:
#             name = row['name'].strip()
#             if name:  # Only add non-empty names
#                 kyc_names.append(name)
# except Exception as e:
#     print(f"Error reading CSV file: {e}")
#     sys.exit(1)

# if not kyc_names:
#     print("Error: No names found in the 'name' column.")
#     sys.exit(1)

# print(f"Loaded {len(kyc_names)} name(s) from '{csv_file}'.")

# --- How to use the agent ---

def scrape(kyc_name):
    # for kyc_name in kyc_names:
    # kyc_name = "Nirav Modi"
        adverse_keywords = ["fraud", "scam"]
        #, "sanctions", "criminal", "1MDB", "fugitive"]
        all_found_links = set()

        # --- NEW: Load all API keys from .env ---
        api_keys = []
        i = 1
        while True:
            key = os.environ.get(f"GOOGLE_CLOUD_API_KEY_{i}")
            pse_id = os.environ.get(f"PROGRAMMABLE_SEARCH_ENGINE_ID_{i}")
            
            if key and pse_id:
                api_keys.append({"key": key, "id": pse_id})
                i += 1
            else:
                # Stop when we can't find the next numbered key
                break

        if not api_keys:
            print("Error: No API keys found. Check your .env file for correct naming.")
        else:
            print(f"Loaded {len(api_keys)} API key(s).")
            
            key_index = 0  # Start with the first key in our list
            
            try:
                # Loop through each keyword
                for keyword in adverse_keywords:
                    search_query = f'"{kyc_name}" "{keyword}"'
                    
                    # This flag tracks if the *current keyword* was successful
                    success_for_this_keyword = False
                    
                    # Keep trying until this keyword is successful
                    while not success_for_this_keyword:
                    
                        # Check if we've run out of keys
                        if key_index >= len(api_keys):
                            print("Error: All API keys have exceeded their quota or failed.")
                            raise Exception("All API keys exhausted.") # Stop the script
                        
                        # Get the current key to try
                        current_key_info = api_keys[key_index]
                        print(f"Using API Key {key_index + 1} for: {search_query}")

                        try:
                            # --- Try to make the API call ---
                            found_links = get_google_links(
                                search_query, 
                                current_key_info["key"], 
                                current_key_info["id"]
                            )
                            
                            # --- SUCCESS! ---
                            all_found_links.update(found_links)
                            print(f"Found {len(found_links)} links.")
                            success_for_this_keyword = True # Mark as successful
                            time.sleep(0.5) # Wait before next keyword
                        
                        # --- ERROR HANDLING ---
                        except requests.exceptions.HTTPError as e:
                            
                            # 1. KEY ROTATION LOGIC (4xx errors)
                            if e.response.status_code == 429: # Quota Exceeded
                                print(f"--- QUOTA EXCEEDED for Key {key_index + 1}. Rotating to next key. ---")
                                key_index += 1 # Move to the next key
                                # Loop continues to retry this *same keyword* with the *new key*
                            
                            elif 400 <= e.response.status_code < 500: # Other "bad" error (bad key, bad request)
                                print(f"--- PERMANENT ERROR for Key {key_index + 1}: {e}. Skipping this key. ---")
                                key_index += 1 # Move to the next key
                            
                            # 2. RETRY LOGIC (5xx errors)
                            elif 500 <= e.response.status_code < 600: # Server error
                                print(f"--- Server Error ({e.response.status_code}). Retrying in 5 seconds... ---")
                                time.sleep(5)
                                # Loop continues to retry this *same keyword* with the *same key*
                            
                            else:
                                raise e # Re-raise any other HTTP error
                        
                        except requests.exceptions.RequestException as e:
                            # 2. RETRY LOGIC (Network errors)
                            print(f"--- Network Error: {e}. Retrying in 5 seconds... ---")
                            time.sleep(5)
                            # Loop continues to retry this *same keyword* with the *same key*

            except Exception as e:
                print(f"A critical error stopped the search: {e}")

            finally:
                print("All searches complete.")

            # 5. Print all unique results
            print("\n--- All Unique Links Found ---")
            if all_found_links:
                return list(all_found_links)
            else:
                print("No links found for any of the keywords.")
                return []