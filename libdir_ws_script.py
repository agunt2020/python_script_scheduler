import requests
from bs4 import BeautifulSoup
import csv
import os
import datetime

# --- CONFIGURATION ---
# Replace the text inside the quotes with the actual path you copied from File Explorer
SHAREPOINT_FOLDER = r"C:\Users\libsystems\american.edu\Python Script Scheduler - Documents"
FILE_NAME = "library_staff_directory.csv"
TARGET_URL = "https://www.american.edu/library/about/directory.cfm"

def decode_cloudflare_email(encoded_string):
    """
    Decodes the Cloudflare-obfuscated email hex string into a readable email address.
    """
    r = int(encoded_string[:2], 16)
    email = ''.join([chr(int(encoded_string[i:i + 2], 16) ^ r) for i in range(2, len(encoded_string), 2)])
    return email

def scrape_directory():
    try:
        # 1. Setup headers to look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        print(f"Connecting to {TARGET_URL}...")
        response = requests.get(TARGET_URL, headers=headers)
        response.raise_for_status()

        # 2. Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        staff_rows = soup.find_all('tr')
        scraped_data = []

        print("Scraping and decoding data...")
        for row in staff_rows:
            cells = row.find_all('td')

            # The directory table has 4 columns: Name, Title, Profile, Email
            if len(cells) >= 4:
                name = cells[0].get_text(strip=True)
                title = cells[1].get_text(strip=True)
                profile = cells[2].get_text(strip=True)

                # Email Decoding Logic
                email_cell = cells[3]
                email = "N/A"

                # Search for Cloudflare's encoded email attribute
                cf_tag = email_cell.find(attrs={"data-cfemail": True})
                if cf_tag:
                    email = decode_cloudflare_email(cf_tag['data-cfemail'])
                else:
                    # Fallback for standard mailto links or unencoded text
                    cf_link = email_cell.find('a', href=True)
                    if cf_link and "email-protection#" in cf_link['href']:
                        encoded_str = cf_link['href'].split('#')[-1]
                        email = decode_cloudflare_email(encoded_str)
                    else:
                        email = email_cell.get_text(strip=True)

                scraped_data.append([name, title, profile, email])

        # 3. Create the Full File Path
        full_output_path = os.path.join(SHAREPOINT_FOLDER, FILE_NAME)

        # Ensure the directory exists (prevents errors if sync is broken)
        if not os.path.exists(SHAREPOINT_FOLDER):
            print(f"ERROR: The path {SHAREPOINT_FOLDER} was not found.")
            print("Make sure your SharePoint folder is synced via OneDrive.")
            return

        # 4. Save the File
        with open(full_output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Title', 'Profile', 'Email'])
            writer.writerows(scraped_data)

        print("-" * 30)
        print("SUCCESS!")
        print(f"Scraped {len(scraped_data)} staff members.")
        print(f"Saved to: {full_output_path}")
        print("OneDrive will now sync this to the SharePoint cloud.")
        print("-" * 30)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    with open(os.path.join(SHAREPOINT_FOLDER, "log.txt"), "a") as log:
        log.write(f"Scrape successful at {datetime.datetime.now()}\n")

if __name__ == "__main__":
    scrape_directory()
