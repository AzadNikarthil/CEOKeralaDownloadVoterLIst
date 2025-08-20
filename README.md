# Voter List PDF Extraction and Database Loading

This project contains a Python script (`process_voter_lists.py`) designed to extract voter information from PDF electoral rolls from the Kerala CEO website, parse the data using Optical Character Recognition (OCR), and load it into a PostgreSQL database.

The script is designed to handle the specific format of these PDFs, where voter data is stored as images rather than selectable text.

## Features

- **PDF Processing**: Converts PDF pages into high-resolution images for OCR.
- **Data Extraction**:
    - Extracts contextual metadata (constituency info, polling station, etc.) from the first page.
    - Extracts individual voter details (EPIC ID, name, age, gender, etc.) from subsequent pages by slicing the page grid.
- **OCR Support**: Uses Tesseract OCR with the Malayalam language pack.
- **Database Integration**: Loads the extracted data into a PostgreSQL database.
- **Efficient & Robust**: Uses batch database insertion for efficiency and is designed to be idempotent (won't create duplicate voters on re-runs).
- **File Management**: Moves processed PDFs to a separate directory to prevent reprocessing.

## Prerequisites

Before running the script, you must have the following dependencies installed on your system.

### 1. Tesseract OCR Engine

Tesseract is used to perform OCR on the images. You also need the Malayalam language pack.

**On Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-mal
```

### 2. Poppler

The `pdf2image` library requires `poppler-utils` to convert PDFs to images.

**On Debian/Ubuntu:**
```bash
sudo apt-get install -y poppler-utils
```

### 3. PostgreSQL Database

You need a running instance of PostgreSQL. The script also uses the `pg_trgm` extension for fuzzy string matching, which is highly recommended.

## Setup

### 1. Clone the Repository

Clone this repository to your local machine.

### 2. Install Python Dependencies

It is recommended to use a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Database Connection

The script reads database connection details from environment variables to keep credentials secure. Please set the following variables:

```bash
export DB_HOST="your_db_host"         # Default: "localhost"
export DB_PORT="5432"                 # Default: "5432"
export DB_NAME="voters_db"            # The name of your database
export DB_USER="your_db_user"         # Your PostgreSQL username
export DB_PASSWORD="your_db_password" # Your PostgreSQL password
```

The script will automatically create the `voters` table and all necessary indexes on its first run.

## Usage

Run the script from the command line, providing the directory containing your source PDFs and the directory where you want processed files to be moved.

The script will recursively search for all `.pdf` files within the input directory.

### Example Command

```bash
python process_voter_lists.py \
    --input-dir ./voter_lists \
    --output-dir ./processed_pdfs
```

- `--input-dir`: Path to the folder containing the electoral roll PDFs.
- `--output-dir`: Path to the folder where successfully processed PDFs will be moved. This directory will be created if it doesn't exist.

The script will log its progress to the console, including details about which file is being processed, the data found, and the status of the database operations.
