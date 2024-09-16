import os
import re
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def scrape_website(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        p_tags = soup.find_all('p')

        for p in p_tags:
            if re.search(r'Rank\s+\d+', p.text):
                a_tags = p.find_all('a')

                for a in a_tags:
                    href = a.get('href')
                    if href:
                        full_url = urllib.parse.urljoin(url, href)
                        scrape_pdf_links(full_url)
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

def scrape_pdf_links(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Search for "AIR" and the number next to it
        air_match = re.search(r'AIR\s+(\d+)', soup.get_text())
        if air_match:
            air_number = int(air_match.group(1))
            if air_number > 90:
                print(f"AIR {air_number} is greater than 90. Skipping this page.")
                return

        a_tags = soup.find_all('a')

        for a in a_tags:
            href = a.get('href')
            if href and href.lower().endswith('.pdf'):
                pdf_text = a.text.strip()
                full_url = urllib.parse.urljoin(url, href)

                if "GS" in pdf_text:
                    category = "General Studies"
                elif "Essay" in pdf_text:
                    category = "Essay"
                elif "Ethics" in pdf_text:
                    category = "Ethics"
                else:
                    category = "Other"

                print(f"{category} - {pdf_text}: {full_url}")
                download_pdf(full_url, category, pdf_text)
    else:
        print(f"Failed to retrieve the webpage {url}. Status code: {response.status_code}")

def download_pdf(url, category, filename):
    response = requests.get(url)
    if response.status_code == 200:
        if not os.path.exists(category):
            os.makedirs(category)

        clean_filename = re.sub(r'[^\w\-_\. ]', '_', filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{clean_filename}_{timestamp}.pdf"

        filepath = os.path.join(category, full_filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {filepath}")
    else:
        print(f"Failed to download {url}. Status code: {response.status_code}")

def main():
    url = "https://forumias.com/blog/testimonials/"  # Replace with the actual URL you want to scrape
    scrape_website(url)

if __name__ == "__main__":
    main()
