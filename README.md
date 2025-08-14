# CEO Kerala Voter List Downloader

A Python script to automate the bulk download of voter lists from the Chief Electoral Officer (CEO), Kerala website.

## Description

This script allows you to download all voter list PDFs for a specific district and legislative assembly constituency from the CEO Kerala electoral rolls website. It works by replicating the AJAX calls made by the website, which is faster and more reliable than browser automation.

## Features

*   Downloads all voter lists for a specific district and legislative assembly.
*   Command-line interface for ease of use.
*   Lightweight and fast; does not require a browser.

## Requirements

*   Python 3.x
*   `requests`

You can install the required package using pip:

```bash
pip install requests
```

## Usage

To download the voter lists for a specific district and legislative assembly, run the script from your terminal. The files will be saved in a `downloads` directory.

```bash
python download_voter_list.py --district "District Name" --assembly "Assembly Name"
```

For example:

```bash
python download_voter_list.py --district "Ernakulam" --assembly "Thripunithura"
```

You can also limit the number of files to download for testing purposes:
```bash
python download_voter_list.py --district "Ernakulam" --assembly "Thripunithura" --limit 2
```

## Disclaimer

This script is for informational and educational purposes only. The data downloaded is publicly available on the CEO Kerala website. Please use the downloaded data responsibly and in accordance with the terms of use of the website. The author is not responsible for any misuse of this script or the data it downloads.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
