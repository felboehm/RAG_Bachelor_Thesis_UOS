from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pandas as pd 
from datetime import datetime
import streamlit as st

#Authenticate using the service account
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_DICT = st.secrets["credentials"]

credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_DICT, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)

def upload_txt_to_drive(file_name, content):
    #Create a temp file to upload
    with open(file_name, 'w')as f:
        f.write(content)

    file_metadata = {
            'name': file_name,
            'mimeType': 'text/plain',
            'parents': ["15IfFmass58woBrPjVPIcOTJOJ8ZYf7Mk"]
            }
    
    media = MediaFileUpload(file_name, mimetype='text/plain')

    file = drive_service.files().create(
            body = file_metadata,
            media_body = media,
            fields = 'id, parents, name',
           # supportsAllDrives = True
            ).execute()

    print(f"File '{file_name}' has been uploaded with ID: {file['id']} and name: {file['name']} \nTo Folder {file['parents']}")
    os.remove(file_name)

def upload_json_to_drive(file_names):

	for file_name in file_names:

		media = MediaFileUpload(file_name, mimetype='application/json')
		
		file_name = file_name.split('.logs/')[-1]

		file_metadata = {
			'name': file_name,
			'mimeType': 'application/json',
			'parents': ['15IfFmass58woBrPjVPIcOTJOJ8ZYf7Mk']
			}

		file = drive_service.files().create(
			body = file_metadata,
			media_body = media,
			fields = 'id, parents, name',
			supportsAllDrives = True
			).execute()

