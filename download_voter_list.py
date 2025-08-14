import argparse
import requests
import os
import re
import json

# Data decoded from http://webapp.ceo.kerala.gov.in/scripts/lacSearch.js
DISTRICTS = {
    "1": "KASARAGOD", "2": "KANNUR", "3": "WAYANAD", "4": "KOZHIKODE", "5": "MALAPPURAM",
    "6": "PALAKKAD", "7": "THRISSUR", "8": "ERNAKULAM", "9": "IDUKKI", "10": "KOTTAYAM",
    "11": "ALAPPUZHA", "12": "PATHANAMTHITTA", "13": "KOLLAM", "14": "THIRUVANANTHAPURAM"
}

ASSEMBLIES = {
    '1': ['1.MANJESHWAR', '2.KASARAGOD', '3.UDMA', '4.KANHANGAD', '5.TRIKARIPUR'],
    '2': ['6.PAYYANNUR', '7.KALLIASSERI', '8.TALIPARAMBA', '9.IRIKKUR', '10.AZHIKODE', '11.KANNUR', '12.DHARMADAM', '13.THALASSERY', '14.KUTHUPARAMBA', '15.MATTANNUR', '16.PERAVOOR'],
    '3': ['17.MANANTHAVADY', '18.SULTHANBATHERY', '19.KALPETTA'],
    '4': ['20.VADAKARA', '21.KUTTIADI', '22.NADAPURAM', '23.QUILANDY', '24.PERAMBRA', '25.BALUSSERI', '26.ELATHUR', '27.KOZHIKODE NORTH', '28.KOZHIKODE SOUTH', '29.BEYPORE', '30.KUNNAMANGALAM', '31.KODUVALLY', '32.THIRUVAMBADY'],
    '5': ['33.KONDOTTY', '34.ERANAD', '35.NILAMBUR', '36.WANDOOR', '37.MANJERI', '38.PERINTHALMANNA', '39.MANKADA', '40.MALAPPURAM', '41.VENGARA', '42.VALLIKKUNNU', '43.TIRURANGADI', '44.TANUR', '45.TIRUR', '46.KOTTAKKAL', '47.THAVANUR', '48.PONNANI'],
    '6': ['49.THRITHALA', '50.PATTAMBI', '51.SHORNUR', '52.OTTAPALAM', '53.KONGAD', '54.MANNARKAD', '55.MALAMPUZHA', '56.PALAKKAD', '57.TARUR', '58.CHITTUR', '59.NENMARA', '60.ALATHUR'],
    '7': ['61.CHELAKKARA', '62.KUNNAMKULAM', '63.GURUVAYOOR', '64.MANALUR', '65.WADAKKANCHERY', '66.OLLUR', '67.THRISSUR', '68.NATTIKA', '69.KAIPAMANGALAM', '70.IRINJALAKKUDA', '71.PUTHUKKAD', '72.CHALAKKUDY', '73.KODUNGALLUR'],
    '8': ['74.PERUMBAVOOR', '75.ANGAMALY', '76.ALUVA', '77.KALAMASSERY', '78.PARAVUR', '79.VYPEN', '80.KOCHI', '81.THRIPUNITHURA', '82.ERNAKULAM', '83.THRIKKAKARA', '84.KUNNATHUNAD', '85.PIRAVOM', '86.MUVATTUPUZHA', '87.KOTHAMANGALAM'],
    '9': ['88.DEVIKULAM', '89.UDUMBANCHOLA', '90.THODUPUZHA', '91.IDUKKI', '92.PEERUMADE'],
    '10': ['93.PALA', '94.KADUTHURUTHY', '95.VAIKOM', '96.ETTUMANOOR', '97.KOTTAYAM', '98.PUTHUPPALLY', '99.CHANGANASSERY', '100.KANJIRAPPALLY', '101.POONJAR'],
    '11': ['102.AROOR', '103.CHERTHALA', '104.ALAPPUZHA', '105.AMBALAPUZHA', '106.KUTTANAD', '107.HARIPAD', '108.KAYAMKULAM', '109.MAVELIKARA', '110.CHENGANNUR'],
    '12': ['111.THIRUVALLA', '112.RANNI', '113.ARANMULA', '114.KONNI', '115.ADOOR'],
    '13': ['116.KARUNAGAPPALLY', '117.CHAVARA', '118.KUNNATHUR', '119.KOTTARAKKARA', '120.PATHANAPURAM', '121.PUNALUR', '122.CHADAYAMANGALAM', '123.KUNDARA', '124.KOLLAM', '125.ERAVIPURAM', '126.CHATHANNUR'],
    '14': ['127.VARKALA', '128.ATTINGAL', '129.CHIRAYINKEEZHU', '130.NEDUMANGAD', '131.VAMANAPURAM', '132.KAZHAKKOOTTAM', '133.VATTIYOORKAVU', '134.THIRUVANANTHAPURAM', '135.NEMOM', '136.ARUVIKKARA', '137.PARASSALA', '138.KATTAKKADA', '139.KOVALAM', '140.NEYYATTINKARA']
}

def download_voter_lists(district_name: str, assembly_name: str, limit: int):
    """
    Fetches and downloads voter lists using the requests library.
    """
    print("Initializing...")
    # Find district ID
    dist_id = None
    for did, dname in DISTRICTS.items():
        if district_name.lower() in dname.lower():
            dist_id = did
            break

    if not dist_id:
        print(f"Error: District '{district_name}' not found.")
        return

    # Find assembly ID
    lac_id = None
    if dist_id in ASSEMBLIES:
        for aname in ASSEMBLIES[dist_id]:
            if assembly_name.lower() in aname.lower():
                lac_id = aname.split('.')[0]
                break

    if not lac_id:
        print(f"Error: Assembly '{assembly_name}' not found in district '{DISTRICTS[dist_id]}'.")
        return

    print(f"Found District: {DISTRICTS[dist_id]} (ID: {dist_id})")
    print(f"Found Assembly: {assembly_name} (ID: {lac_id})")

    # Make request to get booth list data
    ajax_url = "http://webapp.ceo.kerala.gov.in/electoralroll/partsListAjax.html"
    params = {
        "currentYear": "2023",
        "distNo": dist_id,
        "lacNo": lac_id
    }

    print(f"\nFetching booth data from {ajax_url}...")
    try:
        response = requests.get(ajax_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching booth data: {e}")
        return
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response from server.")
        return

    # Parse the response and download PDFs
    booth_data = data.get("aaData")
    if not booth_data:
        print("No booth data found in the response.")
        return

    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)

    print("\n--- Booth Information & Download Status ---")
    download_count = 0
    for booth in booth_data:
        if limit > 0 and download_count >= limit:
            print(f"\nDownload limit of {limit} reached. Stopping.")
            break

        booth_num = booth[0]
        station_name = booth[1]
        download_html = booth[3] # Final Electoral Roll link

        match = re.search(r'href="([^"]+)"', download_html)
        if not match:
            print(f"Booth #: {booth_num}, Station: {station_name}")
            print("  -> No download link found.")
            continue

        relative_url = match.group(1)
        base_url = "http://webapp.ceo.kerala.gov.in/electoralroll/"
        pdf_url = requests.compat.urljoin(base_url, relative_url)

        print(f"Booth #: {booth_num}, Station: {station_name}")
        print(f"  -> Downloading from {pdf_url}")

        try:
            pdf_response = requests.get(pdf_url, stream=True)
            pdf_response.raise_for_status()

            sanitized_station_name = re.sub(r'[\\/*?:"<>|]', "", station_name).strip()
            filename = f"booth_{booth_num}_{sanitized_station_name}.pdf"
            filepath = os.path.join(download_dir, filename)

            with open(filepath, 'wb') as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"  -> Successfully downloaded to {filepath}")
            download_count += 1

        except requests.exceptions.RequestException as e:
            print(f"  -> Failed to download PDF: {e}")

    print("\nDownload process complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download voter list data from CEO Kerala website."
    )
    parser.add_argument(
        "--district",
        type=str,
        required=True,
        help='The name of the district (e.g., "Ernakulam").',
    )
    parser.add_argument(
        "--assembly",
        type=str,
        required=True,
        help='The name of the assembly (e.g., "Thripunithura").',
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of files to download (0 for no limit).",
    )
    args = parser.parse_args()

    download_voter_lists(args.district, args.assembly, args.limit)
