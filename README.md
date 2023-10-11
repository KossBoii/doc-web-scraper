# doc-web-scraper

## Installation

### WSL2 (Recommended)

#### 1. Setup Chrome and Chromedriver
```bash
./scripts/install-selenium.sh
```

#### 2. Create conda environment
```bash
conda create -n web_scraper python=3.8
conda activate web_scaper
```

#### 3. Install all required packages
```bash
pip3 install -r ./src/requirements.txt
```

#### 4. Create Google service account and download credential.json
- Follow the instruction in this [link](https://skaaptjop.medium.com/access-gsuite-apis-on-your-domain-using-a-service-account-e2a8dbda287c) to download credential file
- Rename the file to `credential.json`
- Place `credential.json` in `src/g_suite/`

#### 5. Get Google Sheet ID and change it in `src/config.py`

Replace correct Google Sheet ID where it says something like this:
```python
# Google Sheet
sheet_id = "....."  # PLACE_HERE
```

#### 6. Package to complete application

Run the following command to package app to executable. The executable will be available in `./dist/web_crawler`

```bash
pyinstaller web_crawler.spec
```

#### 7. Run and enjoy the executable
```bash
./dist/web_crawler
```