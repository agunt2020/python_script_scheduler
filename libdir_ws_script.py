import requests
from bs4 import BeautifulSoup
import csv

# Target URL
url = "https://www.american.edu/library/about/directory.cfm"


def decode_cloudflare_email(encoded_string):
    """
    Decodes a Cloudflare-obfuscated email address using the XOR cipher.
    """
    r = int(encoded_string[:2], 16)
    email = ''.join([chr(int(encoded_string[i:i + 2], 16) ^ r) for i in range(2, len(encoded_string), 2)])
    return email


def scrape_directory():
    try:
        # 1. Send request with a "User-Agent" so the website treats us like a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # 2. Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # 3. Find the directory rows
        staff_rows = soup.find_all('tr')

        scraped_data = []

        for row in staff_rows:
            cells = row.find_all('td')

            # The directory has 4 columns: Name, Title, Profile, Email
            if len(cells) >= 4:
                name = cells[0].get_text(strip=True)
                title = cells[1].get_text(strip=True)
                profile = cells[2].get_text(strip=True)

                # --- NEW EMAIL DECODING LOGIC ---
                email_cell = cells[3]
                email = ""

                # Look for the hidden code (data-cfemail attribute)
                cf_tag = email_cell.find(attrs={"data-cfemail": True})
                if cf_tag:
                    email = decode_cloudflare_email(cf_tag['data-cfemail'])
                else:
                    # Alternative check: some sites hide it in the href link
                    cf_link = email_cell.find('a', href=True)
                    if cf_link and "email-protection#" in cf_link['href']:
                        encoded_str = cf_link['href'].split('#')[-1]
                        email = decode_cloudflare_email(encoded_str)
                    else:
                        # Fallback if the email is not protected/obfuscated
                        email = email_cell.get_text(strip=True)

                # Skip the placeholder text if decoding fails
                if email == "[email protected]":
                    email = "N/A"
                # --------------------------------

                scraped_data.append([name, title, profile, email])

        # 4. Write data to a CSV file
        with open('library_staff_directory.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Updated Headers to reflect the actual website columns
            writer.writerow(['Name', 'Title', 'Profile', 'Email'])
            writer.writerows(scraped_data)

        print(f"Successfully scraped {len(scraped_data)} staff members with decoded emails!")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    scrape_directory()