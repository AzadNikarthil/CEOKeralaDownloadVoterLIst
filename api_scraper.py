import os
import re
import requests
import json

# Data for districts and constituencies
DISTRICTS_DATA = {
    "1": "KASARAGOD",
    "2": "KANNUR",
    "3": "WAYANAD",
    "4": "KOZHIKODE",
    "5": "MALAPPURAM",
    "6": "PALAKKAD",
    "7": "THRISSUR",
    "8": "ERNAKULAM",
    "9": "IDUKKI",
    "10": "KOTTAYAM",
    "11": "ALAPPUZHA",
    "12": "PATHANAMTHITTA",
    "13": "KOLLAM",
    "14": "THIRUVANANTHAPURAM"
}

CONSTITUENCIES_DATA = {
    "1": [
        {"id": "1", "name": "MANJESHWAR"}, {"id": "2", "name": "KASARAGOD"},
        {"id": "3", "name": "UDMA"}, {"id": "4", "name": "KANHANGAD"},
        {"id": "5", "name": "TRIKARIPUR"},
    ],
    "2": [
        {"id": "6", "name": "PAYYANNUR"}, {"id": "7", "name": "KALLIASSERI"},
        {"id": "8", "name": "TALIPARAMBA"}, {"id": "9", "name": "IRIKKUR"},
        {"id": "10", "name": "AZHIKODE"}, {"id": "11", "name": "KANNUR"},
        {"id": "12", "name": "DHARMADAM"}, {"id": "13", "name": "THALASSERY"},
        {"id": "14", "name": "KUTHUPARAMBA"}, {"id": "15", "name": "MATTANNUR"},
        {"id": "16", "name": "PERAVOOR"},
    ],
    "3": [
        {"id": "17", "name": "MANANTHAVADY"}, {"id": "18", "name": "SULTHANBATHERY"},
        {"id": "19", "name": "KALPETTA"},
    ],
    "4": [
        {"id": "20", "name": "VADAKARA"}, {"id": "21", "name": "KUTTIADI"},
        {"id": "22", "name": "NADAPURAM"}, {"id": "23", "name": "QUILANDY"},
        {"id": "24", "name": "PERAMBRA"}, {"id": "25", "name": "BALUSSERI"},
        {"id": "26", "name": "ELATHUR"}, {"id": "27", "name": "KOZHIKODE NORTH"},
        {"id": "28", "name": "KOZHIKODE SOUTH"}, {"id": "29", "name": "BEYPORE"},
        {"id": "30", "name": "KUNNAMANGALAM"}, {"id": "31", "name": "KODUVALLY"},
        {"id": "32", "name": "THIRUVAMBADY"},
    ],
    "5": [
        {"id": "33", "name": "KONDOTTY"}, {"id": "34", "name": "ERANAD"},
        {"id": "35", "name": "NILAMBUR"}, {"id": "36", "name": "WANDOOR"},
        {"id": "37", "name": "MANJERI"}, {"id": "38", "name": "PERINTHALMANNA"},
        {"id": "39", "name": "MANKADA"}, {"id": "40", "name": "MALAPPURAM"},
        {"id": "41", "name": "VENGARA"}, {"id": "42", "name": "VALLIKKUNNU"},
        {"id": "43", "name": "TIRURANGADI"}, {"id": "44", "name": "TANUR"},
        {"id": "45", "name": "TIRUR"}, {"id": "46", "name": "KOTTAKKAL"},
        {"id": "47", "name": "THAVANUR"}, {"id": "48", "name": "PONNANI"},
    ],
    "6": [
        {"id": "49", "name": "THRITHALA"}, {"id": "50", "name": "PATTAMBI"},
        {"id": "51", "name": "SHORNUR"}, {"id": "52", "name": "OTTAPALAM"},
        {"id": "53", "name": "KONGAD"}, {"id": "54", "name": "MANNARKAD"},
        {"id": "55", "name": "MALAMPUZHA"}, {"id": "56", "name": "PALAKKAD"},
        {"id": "57", "name": "TARUR"}, {"id": "58", "name": "CHITTUR"},
        {"id": "59", "name": "NENMARA"}, {"id": "60", "name": "ALATHUR"},
    ],
    "7": [
        {"id": "61", "name": "CHELAKKARA"}, {"id": "62", "name": "KUNNAMKULAM"},
        {"id": "63", "name": "GURUVAYOOR"}, {"id": "64", "name": "MANALUR"},
        {"id": "65", "name": "WADAKKANCHERY"}, {"id": "66", "name": "OLLUR"},
        {"id": "67", "name": "THRISSUR"}, {"id": "68", "name": "NATTIKA"},
        {"id": "69", "name": "KAIPAMANGALAM"}, {"id": "70", "name": "IRINJALAKKUDA"},
        {"id": "71", "name": "PUTHUKKAD"}, {"id": "72", "name": "CHALAKKUDY"},
        {"id": "73", "name": "KODUNGALLUR"},
    ],
    "8": [
        {"id": "74", "name": "PERUMBAVOOR"}, {"id": "75", "name": "ANGAMALY"},
        {"id": "76", "name": "ALUVA"}, {"id": "77", "name": "KALAMASSERY"},
        {"id": "78", "name": "PARAVUR"}, {"id": "79", "name": "VYPEN"},
        {"id": "80", "name": "KOCHI"}, {"id": "81", "name": "THRIPUNITHURA"},
        {"id": "82", "name": "ERANAKULAM"}, {"id": "83", "name": "THRIKKAKARA"},
        {"id": "84", "name": "KUNNATHUNAD"}, {"id": "85", "name": "PIRAVOM"},
        {"id": "86", "name": "MUVATTUPUZHA"}, {"id": "87", "name": "KOTHAMANGALAM"},
    ],
    "9": [
        {"id": "88", "name": "DEVIKULAM"}, {"id": "89", "name": "UDUMBANCHOLA"},
        {"id": "90", "name": "THODUPUZHA"}, {"id": "91", "name": "IDUKKI"},
        {"id": "92", "name": "PEERUMADE"},
    ],
    "10": [
        {"id": "93", "name": "PALA"}, {"id": "94", "name": "KADUTHURUTHY"},
        {"id": "95", "name": "VAIKOM"}, {"id": "96", "name": "ETTUMANOOR"},
        {"id": "97", "name": "KOTTAYAM"}, {"id": "98", "name": "PUTHUPPALLY"},
        {"id": "99", "name": "CHANGANASSERY"}, {"id": "100", "name": "KANJIRAPPALLY"},
        {"id": "101", "name": "POONJAR"},
    ],
    "11": [
        {"id": "102", "name": "AROOR"}, {"id": "103", "name": "CHERTHALA"},
        {"id": "104", "name": "ALAPPUZHA"}, {"id": "105", "name": "AMBALAPUZHA"},
        {"id": "106", "name": "KUTTANAD"}, {"id": "107", "name": "HARIPAD"},
        {"id": "108", "name": "KAYAMKULAM"}, {"id": "109", "name": "MAVELIKARA"},
        {"id": "110", "name": "CHENGANNUR"},
    ],
    "12": [
        {"id": "111", "name": "THIRUVALLA"}, {"id": "112", "name": "RANNI"},
        {"id": "113", "name": "ARANMULA"}, {"id": "114", "name": "KONNI"},
        {"id": "115", "name": "ADOOR"},
    ],
    "13": [
        {"id": "116", "name": "KARUNAGAPPALLY"}, {"id": "117", "name": "CHAVARA"},
        {"id": "118", "name": "KUNNATHUR"}, {"id": "119", "name": "KOTTARAKKARA"},
        {"id": "120", "name": "PATHANAPURAM"}, {"id": "121", "name": "PUNALUR"},
        {"id": "122", "name": "CHADAYAMANGALAM"}, {"id": "123", "name": "KUNDARA"},
        {"id": "124", "name": "KOLLAM"}, {"id": "125", "name": "ERAVIPURAM"},
        {"id": "126", "name": "CHATHANNUR"},
    ],
    "14": [
        {"id": "127", "name": "VARKALA"}, {"id": "128", "name": "ATTINGAL"},
        {"id": "129", "name": "CHIRAYINKEEZHU"}, {"id": "130", "name": "NEDUMANGAD"},
        {"id": "131", "name": "VAMANAPURAM"}, {"id": "132", "name": "KAZHAKKOOTTAM"},
        {"id": "133", "name": "VATTIYOORKAVU"}, {"id": "134", "name": "THIRUVANANTHAPURAM"},
        {"id": "135", "name": "NEMOM"}, {"id": "136", "name": "ARUVIKKARA"},
        {"id": "137", "name": "PARASSALA"}, {"id": "138", "name": "KATTAKKADA"},
        {"id": "139", "name": "KOVALAM"}, {"id": "140", "name": "NEYYATTINKARA"},
    ],
}

BASE_URL = "http://webapp.ceo.kerala.gov.in/electoralroll/partsListAjax.html"
DOWNLOAD_BASE_DIR = "voter_lists"
HREF_REGEX = re.compile(r'href=[\'"]?([^\'" >]+)')
PDF_URL_REGEX = re.compile(r'id="pdfFileUrlId"\s+value="([^"]+)"')

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

def fetch_and_download_voter_lists(district_id, district_name, constituency_id, constituency_name):
    """
    Fetches and downloads voter lists for a given constituency.
    """
    print(f"\nProcessing Constituency: {constituency_name}")

    params = {
        "currentYear": "2023",
        "distNo": district_id,
        "lacNo": constituency_id,
        "iDisplayLength": "10000", # Request all records to bypass pagination
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("ERROR"):
            print(f"    API returned an error for {constituency_name}: {data.get('errors')}")
            return

        polling_stations = data.get("aaData", [])
        print(f"    Found {len(polling_stations)} polling stations.")

        for station_data in polling_stations:
            polling_station_name = station_data[1]
            final_roll_html = station_data[3]

            href_match = HREF_REGEX.search(final_roll_html)
            if href_match:
                captcha_page_url = href_match.group(1)

                try:
                    # Step 1: Go to the captcha page
                    captcha_page_response = requests.get(captcha_page_url)
                    captcha_page_response.raise_for_status()

                    # Step 2: Extract the final PDF URL from the captcha page
                    pdf_url_match = PDF_URL_REGEX.search(captcha_page_response.text)

                    if pdf_url_match:
                        final_pdf_url = pdf_url_match.group(1)
                        safe_filename = "".join(c for c in polling_station_name if c.isalnum() or c in (' ', '_')).rstrip()
                        pdf_filename = f"{safe_filename}.pdf"
                        download_folder = os.path.join(DOWNLOAD_BASE_DIR, district_name, constituency_name)

                        # Step 3: Download the actual PDF
                        download_pdf(final_pdf_url, download_folder, pdf_filename)
                    else:
                        print(f"    Could not find final PDF URL for {polling_station_name}")

                except requests.exceptions.RequestException as e:
                    print(f"    Error fetching captcha page for {polling_station_name}: {e}")

            else:
                print(f"    Could not find download link for {polling_station_name}")

    except requests.exceptions.RequestException as e:
        print(f"    An error occurred while fetching data for {constituency_name}: {e}")
    except json.JSONDecodeError:
        print(f"    Failed to decode JSON for {constituency_name}")

def main():
    """
    Main function to iterate through all districts and constituencies and download voter lists.
    """
    print("Starting automated voter list download script...")

    # Iterate through all districts, sorted by ID for consistent order
    sorted_districts = sorted(DISTRICTS_DATA.items(), key=lambda item: int(item[0]))
    for district_id, district_name in sorted_districts:
        print(f"\n--- Processing District: {district_name} ---")

        if district_id not in CONSTITUENCIES_DATA:
            print(f"    No constituencies found for {district_name}")
            continue

        # Iterate through all constituencies in the district
        for constituency in CONSTITUENCIES_DATA[district_id]:
            constituency_id = constituency['id']
            constituency_name = constituency['name']

            fetch_and_download_voter_lists(
                district_id,
                district_name,
                constituency_id,
                constituency_name
            )

    print("\nScript finished.")

if __name__ == "__main__":
    main()
