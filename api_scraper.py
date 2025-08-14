import os
import re
import requests
import json

# Data for districts and constituencies
# This can be expanded with data from the other districts.
DISTRICTS = [
    {
        "name": "KASARAGOD",
        "id": "1",
        "constituencies": [
            {"name": "MANJESHWAR", "id": "1"},
            {"name": "KASARAGOD", "id": "2"},
            {"name": "UDMA", "id": "3"},
            {"name": "KANHANGAD", "id": "4"},
            {"name": "TRIKARIPUR", "id": "5"},
        ],
    },
    # TODO: Add other districts here
]

BASE_URL = "http://webapp.ceo.kerala.gov.in/electoralroll/partsListAjax.html"
DOWNLOAD_BASE_DIR = "voter_lists"
HREF_REGEX = re.compile(r'href=[\'"]?([^\'" >]+)')

def download_pdf(url, folder, filename):
    """Downloads a PDF from a URL and saves it to a specified folder."""
    if not os.path.exists(folder):
        os.makedirs(folder)

    filepath = os.path.join(folder, filename)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  - Successfully downloaded {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - Error downloading {filename}: {e}")
        return False

def main():
    """
    Main function to scrape and download voter lists.
    """
    print("Starting voter list download script...")

    for district in DISTRICTS:
        district_name = district["name"]
        district_id = district["id"]
        print(f"\nProcessing District: {district_name}")

        for constituency in district["constituencies"]:
            constituency_name = constituency["name"]
            constituency_id = constituency["id"]
            print(f"  Processing Constituency: {constituency_name}")

            params = {
                "currentYear": "2023",
                "distNo": district_id,
                "lacNo": constituency_id,
            }

            try:
                response = requests.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("ERROR"):
                    print(f"    API returned an error for {constituency_name}: {data.get('errors')}")
                    continue

                polling_stations = data.get("aaData", [])
                print(f"    Found {len(polling_stations)} polling stations.")

                for station_data in polling_stations:
                    polling_station_name = station_data[1]
                    final_roll_html = station_data[3]

                    match = HREF_REGEX.search(final_roll_html)
                    if match:
                        pdf_url = match.group(1)

                        # Sanitize the polling station name to create a valid filename
                        safe_filename = "".join(c for c in polling_station_name if c.isalnum() or c in (' ', '_')).rstrip()
                        pdf_filename = f"{safe_filename}.pdf"

                        download_folder = os.path.join(DOWNLOAD_BASE_DIR, district_name, constituency_name)

                        download_pdf(pdf_url, download_folder, pdf_filename)
                    else:
                        print(f"    Could not find download link for {polling_station_name}")

            except requests.exceptions.RequestException as e:
                print(f"    An error occurred while fetching data for {constituency_name}: {e}")
            except json.JSONDecodeError:
                print(f"    Failed to decode JSON for {constituency_name}")

    print("\nScript finished.")

if __name__ == "__main__":
    main()
