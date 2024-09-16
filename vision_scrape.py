import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import hashlib
import re

pattern = r"Rank\s*-\s*(\d+)"


def extract_rank(text):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    else:
        return None


def wait_for_download(download_dir, timeout=60):
    """Wait for a file to appear in the download directory and return the latest PDF file."""
    end_time = time.time() + timeout
    latest_file = None
    latest_mtime = 0
    while True:
        files = os.listdir(download_dir)
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(download_dir, file)
                mtime = os.path.getmtime(file_path)
                if mtime > latest_mtime:
                    latest_file = file_path
                    latest_mtime = mtime
        if latest_file:
            return latest_file
        if time.time() > end_time:
            raise Exception("Timeout waiting for download")
        time.sleep(1)


# URL of the main page
main_url = "https://www.visionias.in/resources/toppers_answers.php"

# Initialize the webdriver (e.g., Chrome)
driver = webdriver.Chrome()  # Make sure you have the appropriate webdriver installed

try:
    # Visit the main page
    driver.get(main_url)

    # Get the page source
    page_source = driver.page_source

    # Create a BeautifulSoup objeact
    soup = BeautifulSoup(page_source, "html.parser")

    # Find all the div elements with the specified class
    div_elements = soup.find_all(
        "div",
        class_="tw-p-[20px] tw-bg-white tw-border-[1px] tw-border-[#E5EAF4] tw-rounded-[4px]",
    )

    # Iterate over each div element
    data_dict = {}

    num = 0
    for div in div_elements:
        # Extract the h5 heading
        h5_heading = div.find("h5").text.strip()

        # Extract the "a" tag's "href" attribute
        a_href = div.find("a")["href"]

        span_texts = [
            span.text.strip()
            for span in div.find_all(
                "span",
                class_="tw-text-[#686E70] tw-font-sans tw-text-[12px] tw-font-medium",
            )
        ]
        span_texts_medium = [
            span.text.strip()
            for span in div.find_all(
                "span",
                class_="tw-text-[#686E70] tw-font-sans tw-text-[12px] tw-font-medium tw-capitalize",
            )
        ]
        if len(span_texts) >= 3:
            rank = span_texts[2]
        elif len(span_texts_medium) >= 2:
            rank = span_texts_medium[0]
        else:
            rank = "Rank - 9999"

        hash_value = hashlib.md5(a_href.encode()).hexdigest()
        data_dict[hash_value] = {
            "link": a_href,
            "topper": h5_heading,
            "paper": span_texts[0],
            "rank": extract_rank(rank),
        }

    failed_downloads = []
    for hash_value, data in data_dict.items():
        if data["rank"] <= 80:
            print(data_dict[hash_value])
            link = "https://www.visionias.in/resources/" + data["link"]
            driver.get(link)

            try:
                # Wait for the span to be clickable
                download_span = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "downlode-pdf"))
                )

                # Click on the span to download the PDF
                download_span.click()

                # Wait for the download to complete (adjust the sleep time if needed)
                time.sleep(5)

                # Go the download directory
                download_dir = os.path.expanduser(
                    "~/Downloads"
                )

                # Wait for the file to appear in the download directory
                downloaded_file = wait_for_download(download_dir)

                # Create the folder structure
                topper_and_rank = data["topper"] + " - Rank - " + str(data["rank"])
                folder_name = os.path.join("Toppers", topper_and_rank)
                os.makedirs(folder_name, exist_ok=True)
                nested_folder_name = os.path.join(folder_name, data["paper"])
                os.makedirs(nested_folder_name, exist_ok=True)

                # Move the downloaded PDF to the nested folder
                timestamp = int(time.time())
                current_directory = os.getcwd()
                file_name, file_extension = os.path.splitext(
                    os.path.basename(downloaded_file)
                )

                # Append the timestamp to the file name
                new_file_name = f"{file_name}_{timestamp}{file_extension}"
                destination_folder = os.path.join(
                    current_directory, "Toppers", topper_and_rank, data["paper"]
                )
                destination_file = os.path.join(destination_folder, new_file_name)
                print("Destination file ", destination_file)
                os.rename(downloaded_file, destination_file)

            except Exception as e:
                print(f"Error downloading PDF from {link}: {str(e)}")
                failed_downloads.append((folder_name, link))

    with open("failed_downloads.txt", "w") as file:
        for folder, link in failed_downloads:
            file.write(f"Folder: {folder}, Link: {link}\n")

except Exception as e:
    print(f"Error accessing the main page: {str(e)}")

finally:
    # Close the webdriver
    driver.quit()
