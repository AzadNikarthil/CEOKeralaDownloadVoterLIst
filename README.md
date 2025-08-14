# CEO Kerala Voter List Downloader

A Python script to automate the bulk download of voter lists from the Chief Electoral Officer (CEO), Kerala website.

## Description

This script allows you to download voter lists for a specific district and legislative assembly constituency from the CEO Kerala electoral rolls website: [http://webapp.ceo.kerala.gov.in/electoralrolls.html](http://webapp.ceo.kerala.gov.in/electoralrolls.html)

## Features

*   Download voter lists for a specific district and legislative assembly.
*   The script is designed to be easily extensible to download lists for all districts and constituencies.
*   Command-line interface for ease of use.

## Requirements

*   Python 3.x
*   `requests`
*   `beautifulsoup4`

You can install the required packages using pip:

```bash
pip install requests beautifulsoup4
```

## Usage

To download the voter list for a specific district and legislative assembly, run the script from your terminal with the required arguments.

```bash
python download_voter_list.py --district "District Name" --assembly "Assembly Name"
```

For example:

```bash
python download_voter_list.py --district "Thiruvananthapuram" --assembly "Vattiyoorkavu"
```

## Disclaimer

This script is for informational and educational purposes only. The data downloaded is publicly available on the CEO Kerala website. Please use the downloaded data responsibly and in accordance with the terms of use of the website. The author is not responsible for any misuse of this script or the data it downloads.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
