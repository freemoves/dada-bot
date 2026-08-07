import os
import io
import tempfile
import logging
import random
import time
import requests
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# --- Logging Setup ---
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds',
    'https://spreadsheets.google.com/auth/spreadsheets'
]

FOLDER_ID = '1qQrJbihELRD89ERudZIZoAoagVp_QeyT'
SPREADSHEET_ID = '1fXl3zUmJn6JTbGS15dtGpG5u0o23_-Gx8lFd7gdp3BM'
LOCAL_DOWNLOAD_PATH = tempfile.gettempdir()

# GitHub Secrets se token aur Page IDs uthana
SHARED_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
PAGES = [
    {'id': os.getenv('FB_PAGE_ID_1'), 'name': 'Page 1'},
    {'id': os.getenv('FB_PAGE_ID_2'), 'name': 'Page 2'}
]

def authenticate_google():
    creds_json_env = os.getenv('GOOGLE_CREDENTIALS_JSON') or os.getenv('GOOGLE_CREDENTIALS')
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

def get_smart_caption_and_tags(clean_name):
    captions = [
        f"Zindagi ka naya kissa aur purane tajurbe! Suno Dada Ji ki zubani: {clean_name}",
        f"Kuch baatein dil ko chu jaati hain... Suniye yeh khaas kissa: {clean_name}",
        f"Purane dino ki yaad aur kuch naye rang: {clean_name}",
        f"Sahi baat toh yeh hai ki tajurba sabse bada ustad hota hai! {clean_name}"
    ]
    
    hashtag_pools = [
        "#DadaJi #ViralReels #DesiComedy #OldIsGold #TrendingReels #LucknowChef",
        "#DesiVibes #LifeLessons #DadaJiStories #ViralVideos #ReelsInstagram #DesiHumor",
        "#ClassicWisdom #IndianReels #TrendingNow #DesiVines #GoodOldDays #LucknowVibes"
    ]
    
    return random.choice(captions), random.choice(hashtag_pools)

def run_automation():
    print("--- Dada Ji Automation Started ---")
    logging.info("Dada Ji Automation Started")
    
    try:
        if not SHARED_TOKEN:
            print("Error: PAGE_ACCESS_TOKEN GitHub Secrets me nahi mila!")
            return

        drive_service, sheet_client = authenticate_google()
        
        sheet = sheet_client.open_by_key(SPREADSHEET_ID).sheet1
        list_of_rows = sheet.get_all_values()
        existing_names = [row[0] for row in list_of_rows[1:]] if len(list_of_rows) > 1 else []

        # Drive se saari 500+ videos nikalne ke liye Pagination
        items = []
        page_token = None
        query = f"'{FOLDER_ID}' in parents and mimeType contains 'video/' and trashed = false"

        while True:
            response = drive_service.files().list(
                q=query,
                pageSize=100,
                pageToken=page_token,
                fields="nextPageToken, files(id, name)"
            ).execute()
            
            items.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break

        if not items:
            print("Google Drive folder me koi video nahi mili!")
            return

        target_file = None
        cleaned_existing = [str(name).strip().lower() for name in existing_names]

        for item in items:
            item_name_clean = item['name'].strip().lower()
            if item_name_clean not in cleaned_existing:
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

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if not file_name.lower().endswith('.mp4') or file_size_mb > 500:
            print(f"File validation fail ho gayi ({file_name})")
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        clean_name = os.path.splitext(file_name)[0]
        description, hashtags = get_smart_caption_and_tags(clean_name)
        full_caption = f"{description}\n\n{hashtags}"

        sheet.append_row([file_name, description, hashtags, "Processing"])

        success_count = 0
        for index, page in enumerate(PAGES, start=1):
            page_id = page['id']
            page_label = page['name']

            if not page_id:
                print(f"{page_label} ID missing hai, skip kar rahe hain.")
                continue

            delay_seconds = random.randint(10, 20)
            print(f"{page_label} par upload karne se pehle wait ho raha hai ({delay_seconds}s)...")
            time.sleep(delay_seconds)

            print(f"Uploading video to {page_label} (Page ID: {page_id})...")
            url = f"https://graph-video.facebook.com/v25.0/{page_id}/videos"
            payload = {
                'description': full_caption,
                'access_token': SHARED_TOKEN
            }
            
            with open(file_path, 'rb') as video_file:
                files = {'source': video_file}
                response = requests.post(url, data=payload, files=files)
                result = response.json()

            if 'id' in result:
                print(f"{page_label} par Successfully Uploaded! Video ID: {result['id']}")
                success_count += 1
            else:
                print(f"{page_label} upload fail! Error: {result}")

        updated_rows_count = len(sheet.get_all_values())
        sheet.update_cell(updated_rows_count, 4, f"Uploaded to {success_count}/2 Pages")

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        print(f"Automation script me unexpected error aa gaya: {str(e)}")

if __name__ == "__main__":
    run_automation()
        
