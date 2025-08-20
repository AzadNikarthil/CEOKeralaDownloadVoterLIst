"""
Voter List PDF Processing Script

This script automates the extraction of voter data from electoral roll PDFs from the
Kerala CEO website. It is designed to handle PDFs where the content is image-based.

Main functionalities:
1.  Converts PDF pages to high-resolution images.
2.  Uses Tesseract OCR with Malayalam language support to extract text.
3.  Parses contextual information (constituency, polling station) from the first page.
4.  Parses individual voter data from subsequent pages by slicing the page into a grid.
5.  Connects to a PostgreSQL database and loads the extracted data.
6.  Moves processed PDFs to a specified output directory.

Setup and execution instructions can be found in the README.md file.
"""
import os
import shutil
import argparse
import logging
import re
import pytesseract
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
from pdf2image import convert_from_path
from PIL import Image

# Global database connection object
DB_CONN = None

# --- Constants for Data Extraction ---
CONTEXT_FIELD_MAP = {
    "assembly_constituency_name": ["നിയമസഭാ മണ്ഡലം"],
    "assembly_constituency_no": ["നിയമസഭാ മണ്ഡലം നമ്പർ"],
    "lok_sabha_constituency_name": ["ലോക്സഭാ മണ്ഡലം"],
    "part_no": ["ഭാഗം നമ്പർ"],
    "publication_date": ["പ്രസിദ്ധീകരിച്ച തീയതി"],
    "qualification_date": ["യോഗ്യതാ നിർണ്ണയ തീയതി"],
    "district_name": ["ജില്ല"],
    "polling_station_name": ["വോട്ടെടുപ്പ് കേന്ദ്രം പേര്"],
    "polling_station_address": ["വോട്ടെടുപ്പ് കേന്ദ്രം വിലാസം"],
    "pincode": ["പിൻകോഡ്"],
    # Section name/no can be more complex, will handle separately
}

def setup_logging():
    """Sets up basic logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def initialize_database():
    """
    Initializes the database connection and creates the voters table if it doesn't exist.
    Reads connection details from environment variables.
    """
    global DB_CONN
    try:
        logging.info("Connecting to PostgreSQL database...")
        DB_CONN = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=os.environ.get("DB_PORT", "5432"),
            dbname=os.environ.get("DB_NAME", "voters_db"),
            user=os.environ.get("DB_USER", "user"),
            password=os.environ.get("DB_PASSWORD", "password")
        )
        with DB_CONN.cursor() as cursor:
            logging.info("Enabling pg_trgm extension for fuzzy search...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

            logging.info("Creating 'voters' table if it does not exist...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voters (
                    epic_id VARCHAR(20) PRIMARY KEY,
                    voter_name VARCHAR(255) NOT NULL,
                    guardian_name VARCHAR(255),
                    guardian_relation VARCHAR(50),
                    age INTEGER,
                    gender VARCHAR(50),
                    house_details TEXT,
                    full_address TEXT,
                    pincode VARCHAR(10),
                    section_no INTEGER,
                    section_name VARCHAR(255),
                    part_no INTEGER,
                    polling_station_name TEXT,
                    assembly_constituency_no INTEGER,
                    assembly_constituency_name VARCHAR(255),
                    district_name VARCHAR(255),
                    publication_date DATE,
                    data_source_file VARCHAR(255)
                );
            """)
            # Add indexes for faster queries
            logging.info("Creating indexes for key columns...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_voter_name ON voters (voter_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_guardian_name ON voters (guardian_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pincode ON voters (pincode);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_district ON voters (district_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ac_no ON voters (assembly_constituency_no);")
            # Create a GIN index on full_address for fuzzy search
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_full_address_trgm ON voters USING gin (full_address gin_trgm_ops);")

        DB_CONN.commit()
        logging.info("Database initialized successfully.")
        return True
    except psycopg2.Error as e:
        logging.error(f"Database initialization failed: {e}")
        return False

def _parse_value_from_text(text: str, labels: List[str]) -> Optional[str]:
    """
    A helper function to find a label in OCR'd text and extract the value that follows it.
    It's designed to be flexible against common OCR errors.
    """
    for label in labels:
        # Regex to find the label, followed by an optional colon, and capture the rest of the line.
        # This handles cases like "Label: Value", "Label Value", "Label  :  Value"
        pattern = re.compile(f"{label}\\s*[:.]?\\s*(.+)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            # Clean up the extracted value
            value = match.group(1).strip()
            # Remove any trailing junk if it seems to be another label
            if '  ' in value:
                value = value.split('  ')[0]
            return value
    return None

def extract_context_data_from_page_1(image_path: str) -> Dict[str, Any]:
    """
    Extracts contextual data from the first page of the PDF using OCR.
    """
    logging.info(f"Extracting contextual data from image: {image_path}")

    context_data = {key: None for key in CONTEXT_FIELD_MAP.keys()}

    try:
        # Perform OCR on the first page image
        img = Image.open(image_path)
        ocr_text = pytesseract.image_to_string(img, lang='mal')

        logging.debug("OCR Text from Page 1:\n" + ocr_text)

        # Parse each field using the map
        for field_name, labels in CONTEXT_FIELD_MAP.items():
            value = _parse_value_from_text(ocr_text, labels)
            if value:
                context_data[field_name] = value
                logging.info(f"  - Found {field_name}: {value}")
            else:
                logging.warning(f"  - Could not find {field_name} on page 1.")

        # Special handling for numeric fields
        for field in ["assembly_constituency_no", "part_no", "pincode"]:
            if context_data.get(field):
                # Extract digits from the string
                digits = re.findall(r'\d+', context_data[field])
                if digits:
                    context_data[field] = int("".join(digits))
                else:
                    context_data[field] = None # Set to None if no digits found

        # TODO: Add specific logic for section_name and section_no, as they are often
        # found in a table-like structure which is harder to parse with simple regex.

    except Exception as e:
        logging.error(f"An error occurred during OCR or parsing of page 1: {e}")

    logging.info("Finished extracting contextual data.")
    return context_data

def _parse_voter_card(card_image: Image.Image, serial_no_prefix: int) -> Optional[Dict[str, Any]]:
    """
    Parses a single voter card image using OCR to extract voter details.
    """
    try:
        ocr_text = pytesseract.image_to_string(card_image, lang='mal')

        # If OCR text is very short, it's likely an empty slot.
        if len(ocr_text.strip()) < 15:
            return None

        voter_data = {}

        # 1. EPIC ID (usually a pattern like ABC1234567)
        epic_match = re.search(r'[A-Z]{3}\d{7}', ocr_text)
        voter_data['epic_id'] = epic_match.group(0) if epic_match else None

        # 2. Name
        name_match = re.search(r'പേര്\s*[:.]?\s*([^\n]+)', ocr_text)
        voter_data['voter_name'] = name_match.group(1).strip() if name_match else None

        # 3. Guardian Name & Relation
        guardian_match = re.search(r'(?:അച്ഛന്റെ|ഭർത്താവിന്റെ)\s*പേര്\s*[:.]?\s*([^\n]+)', ocr_text)
        voter_data['guardian_name'] = guardian_match.group(1).strip() if guardian_match else None
        voter_data['guardian_relation'] = 'Husband' if guardian_match and 'ഭർത്താവിന്റെ' in guardian_match.group(0) else 'Father'

        # 4. House Details
        house_match = re.search(r'വീട്ടു\s*നമ്പർ\s*[:.]?\s*([^\n]+)', ocr_text)
        voter_data['house_details'] = house_match.group(1).strip() if house_match else None

        # 5. Age
        age_match = re.search(r'വയസ്സ്\s*[:.]?\s*(\d+)', ocr_text)
        voter_data['age'] = int(age_match.group(1)) if age_match else None

        # 6. Gender
        gender_match = re.search(r'ലിംഗം\s*[:.]?\s*(\S+)', ocr_text)
        voter_data['gender'] = gender_match.group(1).strip() if gender_match else None

        # 7. Serial Number (derived from position)
        voter_data['serial_no_in_part'] = serial_no_prefix

        # A basic check to see if we extracted anything meaningful
        if voter_data['epic_id'] and voter_data['voter_name']:
            return voter_data

    except Exception as e:
        logging.error(f"Error parsing voter card: {e}")

    return None

def extract_voter_data_from_page(image_path: str, page_num: int) -> List[Dict[str, Any]]:
    """
    Extracts individual voter data from a given page image by slicing it into a grid.
    """
    logging.info(f"Extracting voter data from page {page_num}...")
    voters = []
    try:
        img = Image.open(image_path)
        width, height = img.size

        # --- Configuration for slicing the image grid ---
        # These values might need tuning based on different PDF layouts
        HEADER_HEIGHT = 250  # Estimated pixels to skip at the top
        FOOTER_HEIGHT = 150 # Estimated pixels to skip at the bottom
        NUM_ROWS = 10
        NUM_COLS = 3

        grid_height = height - HEADER_HEIGHT - FOOTER_HEIGHT
        cell_width = width // NUM_COLS
        cell_height = grid_height // NUM_ROWS

        base_serial_no = ((page_num - 3) * (NUM_ROWS * NUM_COLS)) + 1

        for i in range(NUM_ROWS):
            for j in range(NUM_COLS):
                left = j * cell_width
                top = HEADER_HEIGHT + (i * cell_height)
                right = left + cell_width
                bottom = top + cell_height

                # Crop the voter card from the page image
                card_image = img.crop((left, top, right, bottom))

                # Calculate the serial number based on grid position
                serial_no = base_serial_no + (i * NUM_COLS) + j

                voter = _parse_voter_card(card_image, serial_no)
                if voter:
                    voters.append(voter)
                    logging.info(f"  - Extracted voter: S/N {voter['serial_no_in_part']}, EPIC {voter['epic_id']}")

    except Exception as e:
        logging.error(f"Failed to process page {page_num} at {image_path}: {e}")

    logging.info(f"Found {len(voters)} voters on page {page_num}.")
    return voters

def save_voters_to_db(voters: List[Dict[str, Any]]):
    """
    Saves a list of voter records to the database using an efficient batch method.
    """
    if not voters or DB_CONN is None:
        if not voters:
            logging.info("No new voter records to save.")
        else:
            logging.error("Database connection is not available. Cannot save voters.")
        return

    logging.info(f"Preparing to save {len(voters)} voter records to the database...")

    # Define the columns in the order they will be inserted
    columns = [
        'epic_id', 'voter_name', 'guardian_name', 'guardian_relation', 'age', 'gender',
        'house_details', 'full_address', 'pincode', 'section_no', 'section_name',
        'part_no', 'polling_station_name', 'assembly_constituency_no',
        'assembly_constituency_name', 'district_name', 'publication_date', 'data_source_file'
    ]

    records_to_insert = []
    for voter in voters:
        # Construct the full_address field, handling None values gracefully
        address_parts = [
            voter.get('house_details'),
            voter.get('section_name'), # Note: section_name extraction is a TODO
            voter.get('polling_station_address'),
            voter.get('district_name')
        ]
        full_address = ", ".join(filter(None, address_parts))
        if voter.get('pincode'):
            full_address += f" {voter.get('pincode')}"
        voter['full_address'] = full_address.strip()

        # Ensure publication_date is a valid date or None
        pub_date = voter.get('publication_date')
        try:
            # Attempt to parse date format like DD-MM-YYYY
            if pub_date:
                parts = re.split(r'[-/.]', pub_date)
                voter['publication_date'] = f"{parts[2]}-{parts[1]}-{parts[0]}"
            else:
                 voter['publication_date'] = None
        except (IndexError, TypeError):
            voter['publication_date'] = None

        # Ensure all columns are present in the record tuple
        record = tuple(voter.get(col) for col in columns)
        records_to_insert.append(record)

    insert_query = f"""
        INSERT INTO voters ({', '.join(columns)})
        VALUES %s
        ON CONFLICT (epic_id) DO NOTHING;
    """

    with DB_CONN.cursor() as cursor:
        try:
            psycopg2.extras.execute_values(
                cursor, insert_query, records_to_insert, template=None, page_size=100
            )
            DB_CONN.commit()
            logging.info(f"Successfully saved or updated {len(records_to_insert)} records.")
        except psycopg2.Error as e:
            logging.error(f"Database error during batch insert: {e}")
            DB_CONN.rollback()


def convert_pdf_to_images(pdf_path: str, temp_dir: str) -> List[str]:
    """
    Converts each page of a PDF file to a high-resolution PNG image.
    """
    logging.info(f"Converting PDF to images: {pdf_path}")
    image_paths = []
    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,
            fmt='png',
            output_folder=temp_dir,
            thread_count=4  # Use multiple threads for speed
        )
        image_paths = [img.filename for img in images]
        logging.info(f"Successfully converted PDF to {len(image_paths)} images.")
    except Exception as e:
        logging.error(f"Failed to convert PDF '{pdf_path}' to images: {e}")
    return image_paths


def process_pdf_file(pdf_path: str, output_dir: str):
    """
    Processes a single PDF file, extracting and saving its data.
    """
    logging.info(f"Processing PDF: {pdf_path}")

    # Create a temporary directory for this specific PDF's images
    pdf_filename = os.path.basename(pdf_path)
    temp_image_dir = os.path.join('/tmp', 'pdf_processing', os.path.splitext(pdf_filename)[0])
    os.makedirs(temp_image_dir, exist_ok=True)

    image_paths = []
    try:
        # Step 1: Convert PDF to images
        image_paths = convert_pdf_to_images(pdf_path, temp_image_dir)

        if not image_paths:
            logging.error(f"Could not convert PDF to images: {pdf_path}")
            return

        # Step 2: Extract contextual data from Page 1
        context_data = extract_context_data_from_page_1(image_paths[0])

        # Step 3: Process subsequent pages for voter data
        all_voters = []
        # Typically, voter data starts from page 3. Page 2 is often a map or blank.
        # We check if there are enough pages to process.
        if len(image_paths) >= 3:
            for i, image_path in enumerate(image_paths[2:], start=3):
                voters_on_page = extract_voter_data_from_page(image_path, page_num=i)
                for voter in voters_on_page:
                    # Combine voter data with the context from page 1
                    voter.update(context_data)
                all_voters.extend(voters_on_page)
        else:
            logging.warning(f"PDF '{pdf_filename}' has fewer than 3 pages, skipping voter data extraction.")


        # Step 4: Save all extracted data to the database
        save_voters_to_db(all_voters)

        # Step 5: Move the processed file
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        shutil.move(pdf_path, os.path.join(output_dir, pdf_filename))
        logging.info(f"Successfully processed and moved {pdf_path}")

    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {pdf_path}: {e}")
    finally:
        # Step 6: Clean up the temporary image directory
        if os.path.exists(temp_image_dir):
            shutil.rmtree(temp_image_dir)
            logging.info(f"Cleaned up temporary directory: {temp_image_dir}")


def main():
    """
    Main function to run the PDF processing script.
    """
    setup_logging()

    parser = argparse.ArgumentParser(description="Process voter list PDFs and load data into a database.")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing the PDF files to process."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where processed PDFs will be moved."
    )
    args = parser.parse_args()

    # --- Pre-flight Checks ---
    if not os.path.isdir(args.input_dir):
        logging.error(f"Input directory not found: {args.input_dir}")
        return

    logging.info(f"Starting PDF processing for directory: {args.input_dir}")

    if not initialize_database():
        logging.error("Failed to initialize database. Exiting.")
        return

    try:
        # Find all PDF files in the input directory
        # We need to process files in subdirectories of the input directory
        pdf_files = []
        for root, _, files in os.walk(args.input_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))

        logging.info(f"Found {len(pdf_files)} PDF file(s) to process.")

        for pdf_path in pdf_files:
            process_pdf_file(pdf_path, args.output_dir)
    finally:
        # Ensure the database connection is closed
        if DB_CONN:
            DB_CONN.close()
            logging.info("Database connection closed.")

    logging.info("All files processed. Script finished.")

if __name__ == "__main__":
    main()
