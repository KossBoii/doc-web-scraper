import os
from datetime import datetime
import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build


class GoogleSheetService:
    def __init__(self, cfg):
        self._scopes=['https://www.googleapis.com/auth/spreadsheets']
        self.cfg = cfg
        
        _base_path = os.path.dirname(__file__)
        self._credential_path = os.path.join(_base_path, 'credential.json')
        self._sheet_id = cfg.sheet_id
        self.cur_year = datetime.now().year
        self._sheet_name = f"Công văn đi {self.cur_year}"
        
        self.newest_doc_id: str = ""
        self.newest_doc_date: str = ""
        
        self.build()
        self.check_sheet_exist()
        self.reload()
        
    def build(self):
        credentials = service_account.Credentials.from_service_account_file(
            self._credential_path, 
            scopes=self._scopes
        )
        
        # Build the Google Sheet service
        self._sheet_service = build('sheets', 'v4', credentials=credentials)
    
    def reload(self):
        old_data, col_names, col_title_idx = self.get_current_sheet()
        
        if len(old_data) <= 0:
            self.newest_doc_id = None
            self.newest_doc_date =  None
        else: 
            self.newest_doc_id = old_data.iloc[0][1]
            self.newest_doc_date = old_data.iloc[0][0]
    
    def check_sheet_exist(self):
        result = self._sheet_service.spreadsheets() \
                                    .get(spreadsheetId=self._sheet_id)\
                                    .execute()
        
        sheet_exists = False
        prev_sheet_id = None
        prev_year_doc_name = f"Công văn đi {self.cur_year - 1}"
        for sheet in result['sheets']:
            if sheet['properties']['title'] == prev_year_doc_name:
                prev_sheet_id = sheet['properties']['sheetId']
            if sheet['properties']['title'] == self._sheet_name:
                sheet_exists = True
                break
        
        if sheet_exists:
            return True
        else:
            try:
                # Create the request to duplicate the sheet
                request = {
                    'destinationSpreadsheetId': self._sheet_id,
                }

                # Duplicate the sheet
                response = self._sheet_service.spreadsheets()\
                                              .sheets()\
                                              .copyTo(spreadsheetId=self._sheet_id,
                                                      sheetId=prev_sheet_id,
                                                      body=request)\
                                              .execute()

                # Get the ID of the newly duplicated sheet
                duplicated_sheet_id = response['sheetId']

                # Rename the duplicated sheet
                request = {
                    'requests': [
                        {
                            'updateSheetProperties': {
                                'properties': {
                                    'sheetId': duplicated_sheet_id,
                                    'title': self._sheet_name,
                                    'index': 0
                                },
                                'fields': 'title, index',
                            },
                        },
                    ],
                }
                self._sheet_service.spreadsheets()\
                                   .batchUpdate(spreadsheetId=self._sheet_id, 
                                                body=request)\
                                   .execute()

                # Clear all rows starting from row 3 in the duplicated sheet
                _, _, col_title_idx = self.get_current_sheet()
                
                clear_range = f"{self._sheet_name}!A{col_title_idx+2}:Z"  # Adjust the range as needed
                self._sheet_service.spreadsheets()\
                                   .values()\
                                   .clear(spreadsheetId=self._sheet_id, 
                                          range=clear_range)\
                                   .execute()


                print(f"The sheet '{self._sheet_name}' has been duplicated "
                      f"with sheet ID {duplicated_sheet_id}.")
            except Exception as e:
                print(f"An error occurred: {e}")

    def get_sheet_id_by_name(self, sheet_name):
        # Execute a request to retrieve the list of sheets in the spreadsheet
        sheets_metadata = self._sheet_service.spreadsheets().get(spreadsheetId=self._sheet_id).execute()
        
        # Extract the list of sheets from the response
        sheets = sheets_metadata.get('sheets', [])
        
        for sheet in sheets:
            title = sheet.get('properties', {}).get('title', '')
            sheet_id = sheet.get('properties', {}).get('sheetId', '')
            
            if title == sheet_name:
                return sheet_id

        # Return None if the sheet with the specified name is not found
        return None

    def get_current_sheet(self):
        result = self._sheet_service.spreadsheets().values().get(
            spreadsheetId=self._sheet_id,
            range=self._sheet_name,
        ).execute()
        all_values = result.get('values', []) 
        df = pd.DataFrame(all_values)

        col_title_idx = 0
        for i, row in df.iterrows():
            if row.loc[0] == 'STT':
                col_title_idx = i
                break
        
        col_names = df.iloc[col_title_idx]
        old_data = df.iloc[col_title_idx+1:].reset_index(drop=True)
        old_data.columns = col_names
        old_data.set_index(col_names[0], inplace=True)

        return old_data, col_names, col_title_idx
    
    def insert(self, datas: list):
        old_data, col_names, col_title_idx = self.get_current_sheet()
        
        df = pd.DataFrame(columns=old_data.columns)
        cols_num = len(old_data.columns)
        
        rows = []
        for data in datas:
            row = data.copy()
            for i in range(cols_num - len(row)):
                row.append("")
            rows.append(row)
            df.loc[len(df)] = row
        
        self.newest_doc_id = df.loc[0][0]
        self.newest_doc_date = df.loc[0][1]

        df = pd.concat([df, old_data], ignore_index=True)
        # df.insert(0, 'STT', range(1, len(df) + 1))
        letter = chr(len(col_names) + 64)
        
        data_range = f"B{col_title_idx+2}:{letter}{len(df)+col_title_idx+1}"
        request = self._sheet_service.spreadsheets().values().update(
            spreadsheetId=self._sheet_id,
            range=f"{self._sheet_name}!{data_range}",
            valueInputOption='USER_ENTERED',
            body={
                'values': df.values.tolist(),
                'majorDimension': 'ROWS',      
            }
        )
        response = request.execute()
        return response
    
    def get_newest_doc_id(self):
        return self.newest_doc_id, self.newest_doc_date
    