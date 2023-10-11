from pydantic import BaseSettings
from functools import lru_cache
from pathlib import Path
from datetime import datetime

class Settings(BaseSettings):
    """App's config settings class"""
    # Website URL to scrape
    url: str = 'http://pgddamha.edu.vn/vanbancuaphong.aspx'
    
    # Specify the path to the Chrome WebDriver executable
    chrome_driver_path: str = '/usr/bin/chromedriver'
    wait_time: int = 10
    table_tag: str = 'taglib-search-iterator'
    page_btn_id = 'ctl00_webPartManager_wp1514173958_wp1868015730_rptPages_ctl{page_num}_btnPage'
    
    drive_root_url: str = "https://drive.google.com/open?id="
    max_new_data: int = 10
    
    # Environment
    project_root: str = str(Path(__file__).parent.parent.absolute())
    run_every_in_hour: float = 1
    date_time_format: str = "%d/%m/%Y"
    start_date = datetime.strptime(f"31/12/{datetime.now().year-1}", 
                                    date_time_format)
    
    # Google Sheet
    sheet_id = "1mFV1Rfq0g2eLr3W2L9lv4-eT6Vd3cetnzN06Dn3RsSI"   # PLACE_HERE
    
    
@lru_cache
def get_settings() -> Settings:
    """get_settings

    Returns:
        Settings: app's config settings
    """
    return Settings()