import os
import io
import requests

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload


class GoogleDriveService:
    def __init__(self):
        self._scopes=['https://www.googleapis.com/auth/drive']

        _base_path = os.path.dirname(__file__)
        self._credential_path = os.path.join(_base_path, 'credential.json')
        self.build()
        
    def build(self):
        credentials = service_account.Credentials.from_service_account_file(
            self._credential_path, 
            scopes=self._scopes
        )
        
        # Build the Google Drive service
        self._drive_service = build('drive', 'v3', credentials=credentials)
        
    def create_folder(self, folder_name, parent_folder_id=None):
        """Create a folder in Google Drive and return its ID."""
        folder_metadata = {
            'name': folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            'parents': [parent_folder_id] if parent_folder_id else []
        }

        created_folder = self._drive_service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()

        print(f'Created Folder ID: {created_folder["id"]}')
        return created_folder["id"]

    def list_folder(self, parent_folder_id=None, delete=False):
        """List folders and files in Google Drive."""
        results = self._drive_service.files().list(
            q=f"'{parent_folder_id}' in parents and trashed=false" if parent_folder_id else None,
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])

        if not items:
            print("No folders or files found in Google Drive.")
        else:
            print("Folders and files in Google Drive:")
            for item in items:
                print(f"Name: {item['name']}, ID: {item['id']}, Type: {item['mimeType']}")
                if delete:
                    self.delete_files(item['id'])

    def delete_files(self, file_or_folder_id):
        """Delete a file or folder in Google Drive by ID."""
        try:
            self._drive_service.files().delete(fileId=file_or_folder_id).execute()
            print(f"Successfully deleted file/folder with ID: {file_or_folder_id}")
        except Exception as e:
            print(f"Error deleting file/folder with ID: {file_or_folder_id}")
            print(f"Error details: {str(e)}")

    def download_file(self, file_id, destination_path):
        """Download a file from Google Drive by its ID."""
        request = self._drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(destination_path, mode='wb')
        
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")
            
    def upload_file(self, file_url: str, folder_id: str):
        response = requests.get(file_url)
        file_name = os.path.basename(response.url)
        
        if response.status_code == 200:
            # Create a file on Google Drive
            file_metadata = {'name': file_name,
                             'parents': [folder_id]}

            media_body = MediaIoBaseUpload(io.BytesIO(response.content), 
                                           mimetype=response.headers.get('Content-Type'))
            file = self._drive_service.files().create(
                body=file_metadata, 
                media_body=media_body
            ).execute()
            print('File ID: %s' % file['id'])
            return file['id']
        
    def get_folder_id_by_name(self, folder_name: str):
        # Search for the folder by its name
        results = self._drive_service.files().list(
            q=f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'",
            fields="files(id)"
        ).execute()

        folders = results.get('files', [])

        if folders:
            return folders[0]['id']  # Return the first folder's ID found with the specified name
        else:
            print(f"Folder with name '{folder_name}' not found.")
            return None