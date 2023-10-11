import re
from typing import List
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.g_suite import GoogleDriveService
from src.g_suite import GoogleSheetService
from src.config import Settings
from src.utils import postprocess


class WebScraper:
    def __init__(self, cfg: Settings):
        self.page: int = 1
        self.cfg: Settings = cfg
        
        # Setup chrome options & chromedriver 
        chrome_options = Options()
        chrome_options.add_argument("--headless") # Ensure GUI is off
        chrome_options.add_argument("--no-sandbox")

        # Set path to chromedriver as per your configuration
        webdriver_service = Service(self.cfg.chrome_driver_path)

        # Choose Chrome Browser
        self.driver = webdriver.Chrome(service=webdriver_service, 
                                options=chrome_options)

        self.g_drive_service = GoogleDriveService()
        self.folder_id = self.g_drive_service.get_folder_id_by_name(
            "test-web-crawler")
        self.g_sheet_service = GoogleSheetService(self.cfg)

    def handle(self):
        new_datas = []
        latest_doc_id, latest_doc_date = self.g_sheet_service.get_newest_doc_id()
        found_prev_latest = False
        reach_start_of_year = False
        
        while(True):
            if len(new_datas) >= self.cfg.max_new_data:
                break
            datas = self.fetch(self.page)
            
            for data in datas:
                doc_id, doc_date = data[1], data[0]
                if (latest_doc_id is None and 
                    latest_doc_date is None):
                    if doc_date == " ":
                        new_datas.append(data)
                    else:
                        doc_date_obj = datetime.strptime(doc_date, 
                                                        self.cfg.date_time_format)
                        if doc_date_obj > self.cfg.start_date:
                            reach_start_of_year = True
                            break
                elif (latest_doc_id == doc_id and 
                      doc_date == latest_doc_date):
                    found_prev_latest = True
                    break
                else:
                    new_datas.append(data)
                    
            if found_prev_latest or reach_start_of_year:
                break
            
            print(f"Total {len(new_datas)} new data added")
        
        response = self.handle_once(new_datas)
        return response

    def handle_once(self, datas: List):
        export_datas = self.upload(datas)
        response = self.export(export_datas)
        
        return response
        
    def fetch(self, page_num: int) -> List:
        self.driver.get(self.cfg.url)
        page_num = f"{page_num - 1:02d}"
        button = self.driver.find_element(
            By.ID, 
            self.cfg.page_btn_id.replace("{page_num}", page_num)
        )
        button.click()
        
        table_locator = (By.CLASS_NAME, self.cfg.table_tag)
        wait = WebDriverWait(self.driver, self.cfg.wait_time)
        table = wait.until(EC.presence_of_element_located(table_locator))

        rows = table.find_elements(By.TAG_NAME, 'tr')  # Find all table rows 
        datas=[]

        for row_id, row in enumerate(rows):
            if row_id == 0:
                continue
            
            cells = row.find_elements(By.TAG_NAME, 'td')
            cols = []
            for cell_id, cell in enumerate(cells):
                if cell_id == len(cells)-1:
                    cols.append(cell.find_element(
                        By.CLASS_NAME, 
                        'a-block').get_attribute('href'))
                else:
                    cols.append(cell.text)
            
            ngay_ban_hanh = postprocess(cols[3])
            so_hieu = postprocess(cols[1])
            ten_tai_lieu = postprocess(cols[2])
            link_tai_lieu = cols[4]
            
            datas.append([ngay_ban_hanh, so_hieu, ten_tai_lieu, link_tai_lieu])
        
        return datas
        
    def upload(self, datas: List) -> List:
        export_datas = []
        
        for data in datas:
            ten_va_link_tai_lieu = self.get_hyperlink(data[-2], data[-1])
            export_data: List = [data[0], data[1], ten_va_link_tai_lieu]
            file_id = self.g_drive_service.upload_file(data[-1], 
                                                       self.folder_id)
            file_hyperlink = self.get_hyperlink(file_id, self.cfg.drive_root_url + file_id)
            export_data.append(file_hyperlink)
            export_datas.append(export_data)
        
        return export_datas
    
    def export(self, export_datas: List):
        if len(export_datas) <= 0 or len(export_datas[0]) != 4:
            return
        
        response = self.g_sheet_service.insert(export_datas)
        return response
    
    def get_hyperlink(self, text, url):
        text = re.sub(r' +', ' ', text)
        text = text.replace('"', '""')
        return f'=HYPERLINK("{url}";"{text}")'
    
    def teardown(self):
        self.driver.quit()