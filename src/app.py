import time

from src.web_scraper import WebScraper
from src.config import get_settings

def main():
    cfg = get_settings()
    sleep_time = cfg.run_every_in_hour * 3600
    web_scraper = WebScraper(cfg)
    while True:
        response = web_scraper.handle()
        print(f"response: {response}")
        print(f"Program will operate in {cfg.run_every_in_hour} hour")
        time.sleep(sleep_time)
    
if __name__ == "__main__":
    main()