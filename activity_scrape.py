from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import re

# Launch a Chrome browser in headless mode (runs in the background)
options = webdriver.ChromeOptions()
options.add_argument("--headless")
# webdriver_manager installs the matching ChromeDriver automatically
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Navigate to the activities page
url = 'https://www.alzheimer-nederland.nl/gezond-brein/artikelen/100-activiteiten-voor-mensen-met-dementie'
driver.get(url)

# Grab the full HTML from the browser
html = driver.page_source
driver.quit()  # close the browser

# Parse the rendered HTML so we can search it easily
soup = BeautifulSoup(html, 'html.parser')

# Find each section whose id starts with "activiteiten-"
# This matches the categories of activities
sections = soup.find_all('section', id=re.compile(r'^activiteiten-'))

# Create a CSV and write a header row
with open('activiteiten.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Category', 'Subcategory', 'Activity'])

    # For each category section:
    for sec in sections:
        # Get the category name from the <h2> tag
        h2 = sec.find('h2')
        category = h2.get_text(strip=True) if h2 else 'No category'

        # Inside each category, each <details> is a subcategory
        for detail in sec.find_all('details'):
            # The subcategory label is in the <summary>
            summ = detail.find('summary')
            subcat = summ.get_text(strip=True) if summ else 'No subcategory'

            # Each <li> under this <details> is one activity
            for li in detail.select('ul li'):
                activity = li.get_text(strip=True)
                writer.writerow([category, subcat, activity])

print("Saved all activities to activiteiten.csv")
