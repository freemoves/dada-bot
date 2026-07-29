import os
import io
import tempfile
import requests
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets'
]

FOLDER_ID = '1BN7fZofdfYg3BK9MLZrPWWaIdzdumP7j'
SPREADSHEET_ID = '1RL-3OTylVKG6HpqrzubAqqWZcqET6FXCbca1r-Ov9Rs'
LOCAL_DOWNLOAD_PATH = tempfile.gettempdir()

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN'EAAj8TeyzlZBcBSOjOXTZBiBNxvIKZBcwGvYTUN2tvFlUAU3kY06pxbkUtiBgG1x0Y4CS42MxnWqyXu6y65BB2F7JzV5VqkwOUQEKbT4g5Qudxxvt7wCZA3Q9jv9IZCu3ZBIJkcV8WwtLiduIntelW9AoZAM4bZBH8j5pfLRQQ6viZChx12b4fcEZCZBVHclF5ZADxW1mIzdCH4nvWruGTrz5YXap3nfb'
')
PAE_ID = '1290868640770104'

def authenticate_google():
    creds_json_env = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json_env:
        import json
        creds_dict = json.loads(creds_json_env)
        creds_drive = service_account.Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/drive'])
        sheet_client = gspread.authorize(service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES))
    else:
        creds_drive = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive']
        )
        creds_sheet = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        sheet_client = gspread.authorize(creds_sheet)
    drive_service = build('drive', 'v3', credentials=creds_drive)
    return drive_service, sheet_client

def run_automation():
    print("--- Automation Process Started ---")
    drive_service, sheet_client = authenticate_google()
    
    sheet = sheet_client.open_by_key(SPREADSHEET_ID).sheet1
    list_of_rows = sheet.get_all_values()
    existing_names = [row[0] for row in list_of_rows[1:]] if len(list_of_rows) > 1 else []

    query = f"'{FOLDER_ID}' in parents and mimeType contains 'video/' and trashed = false"
    results = drive_service.files().list(q=query, pageSize=20, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print("Google Drive folder me koi video nahi mili!")
        return

    target_file = None
    for item in items:
        if item['name'] not in existing_names:
            target_file = item
            break

    if not target_file:
        print("Sabhi videos pehle hi processed/uploaded hain!")
        return

    file_id = target_file['id']
    file_name = target_file['name']
    print(f"Nayi video mili: {file_name}")

    os.makedirs(LOCAL_DOWNLOAD_PATH, exist_ok=True)
    file_path = os.path.join(LOCAL_DOWNLOAD_PATH, file_name)

    print("Downloading video from Drive...")
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    fh.seek(0)
    with open(file_path, 'wb') as f:
        f.write(fh.read())

    clean_name = os.path.splitext(file_name)[0]
    description = f"Zindagi ka naya kissa aur purane tajurbe! Suno Dada Ji ki zubani: {clean_name}"
    hashtags = "#DadaJi #ViralReels #DesiComedy #Thimp #OldIsGold #TrendingReels #LucknowChef"

    sheet.append_row([file_name, description, hashtags, "Downloaded"])

    print("Uploading video to Facebook Page...")
    url = f"https://graph-video.facebook.com/v25.0/{PAGE_ID}/videos"
    full_caption = f"{description}\n\n{hashtags}"
    payload = {
        'description': full_caption,
        'access_token': PAGE_ACCESS_TOKEN
    }
    
    with open(file_path, 'rb') as video_file:
        files = {'source': video_file}
        response = requests.post(url, data=payload, files=files)
        result = response.json()

    if 'id' in result:
        print(f"Successfully Uploaded to Facebook! Video ID: {result['id']}")
        updated_rows_count = len(sheet.get_all_values())
        sheet.update_cell(updated_rows_count, 4, "Uploaded to FB")
    else:
        print(f"Facebook upload fail ho gaya! Error: {result}")

    if os.path.exists(file_path):
        os.remove(file_path)

if __name__ == "__main__":
    run_automation()
  
