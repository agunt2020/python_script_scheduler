# Overview
This project automatically scrapes the American University Library Directory, decodes protected email addresses, and generates professional, department-specific organizational charts. The entire process is synced directly to SharePoint via OneDrive.

# How it works: 
1. Windows Task Scheduler: Wakes up once a week
2. The Scraper (merged_orgchart_generator.py): Connects to the AU Directory website.
   - Decodes protected emails
   - Saves the data to library_staff_directory.csv in SharePoint.
3. The Generator: Reads the new CSV data and the manually managed Library Org Chart - Library Data.csv.
   - Creates six high-resolution PNG org charts using the Matplotlib engine.
   - Saves the images directly to SharePoint for library-wide access.

# Installation and Setup 
1. Prerequisites:
   - Python 3.13+ Installed.
   - OneDrive signed in and syncing the SharePoint folder: Python Script Scheduler - Documents.
   - Required Libraries: pip install requests beautifulsoup4 pandas matplotlib
2. Folder Structure - Your folder should contain:
   - merged_orgchart_generator.py (The main script)
   - Library Org Chart - Library Data.csv (The manual file that defines who reports to whom)
   - library_staff_directory.csv (Automatically updated by the script)

# Manual Data Management
While the names and emails are scraped automatically, the reporting structure (who is the manager) must be updated manually in the Library Org Chart - Library Data.csv file.
- Full Name: Must match the name on the AU website
- Manager: The name of the person they report to.
Note: If a new staff member is hired, the scraper will find their email, but they won't appear on a chart until you add them and their manager to this CSV.

# How to Run Manually
1. Open PyCharm.
2. Open merged_orgchart_generator.py.
3. Right-click anywhere in the code and select Run.
4. Check the SharePoint folder after about 30 seconds for the new .png files.

# Troubleshooting
- "The system cannot find the path specified": Check if your OneDrive has "paused" or if you have been signed out of your AU account. Re-sync the SharePoint folder if the building icon is missing from File Explorer.
- "Syntax Error in Label": This usually means a name or title has a special character (like &) that wasn't escaped. The script includes html.escape() to handle this, but ensure names in the Manual CSV are clean text.
- Emails showing as "N/A": The website structure may have changed. Check the TARGET_URL in the script to ensure it still points to the correct directory page.

# Configuration Settings
You can modify these variables at the top of the script:
- SHAREPOINT_FOLDER: The local path to your synced SharePoint.
- DEPT_HEADS: A list of the six heads. You can change their assigned hex colors here to update the chart branding.
- SCALE: Adjust this number (default 18) to make the cards larger or smaller.
