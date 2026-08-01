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

# --- Logging Setup (Advanced Logging Feature) ---
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets'
]

FOLDER_ID = '1BN7fZofdfYg3BK9MLZrPWWaIdzdumP7j'
SPREADSHEET_ID = '1RL-3OTylVKG6HpqrzubAqqWZcqET6FXCbca1r-Ov9Rs'
LOCAL_DOWNLOAD_PATH = tempfile.gettempdir()

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
PAGE_ID = '1290868640770104'

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

def get_smart_caption_and_tags(clean_name):
    """Smart Caption & Hashtag Rotation Feature"""
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
    
    selected_caption = random.choice(captions)
    selected_tags = random.choice(hashtag_pools)
    return selected_caption, selected_tags

def run_automation():
    print("--- Automation Process Started ---")
    logging.info("Automation Process Started")
    
    try:
        drive_service, sheet_client = authenticate_google()
        
        sheet = sheet_client.open_by_key(SPREADSHEET_ID).sheet1
        list_of_rows = sheet.get_all_values()
        existing_names = [row[0] for row in list_of_rows[1:]] if len(list_of_rows) > 1 else []

        query = f"'{FOLDER_ID}' in parents and mimeType contains 'video/' and trashed = false"
        results = drive_service.files().list(q=query, pageSize=50, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print("Google Drive folder me koi video nahi mili!")
            logging.info("Google Drive folder me koi video nahi mili.")
            return

        target_file = None
        # Clean existing names for strict comparison (strip spaces and lowercase)
        cleaned_existing = [str(name).strip().lower() for name in existing_names]

        for item in items:
            item_name_clean = item['name'].strip().lower()
            if item_name_clean not in cleaned_existing:
                target_file = item
                break

        if not target_file:
            print("Sabhi videos pehle hi processed/uploaded hain!")
            logging.info("Sabhi videos pehle hi processed/uploaded hain.")
            return

        file_id = target_file['id']
        file_name = target_file['name']
        print(f"Nayi video mili: {file_name}")
        logging.info(f"Nayi video mili: {file_name}")

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

        # --- Media Validation Check Feature ---
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if not file_name.lower().endswith('.mp4'):
            error_msg = f"Invalid file format for {file_name}. Only MP4 is supported."
            print(error_msg)
            logging.error(error_msg)
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        if file_size_mb > 500:
            error_msg = f"Video file {file_name} is too large ({file_size_mb:.2f} MB)."
            print(error_msg)
            logging.error(error_msg)
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        clean_name = os.path.splitext(file_name)[0]
        description, hashtags = get_smart_caption_and_tags(clean_name)

        sheet.append_row([file_name, description, hashtags, "Downloaded"])

        # --- Natural Human-like Delay Feature ---
        delay_seconds = random.randint(15, 40)
        print(f"Insaan jaisa natural wait ho raha hai ({delay_seconds} seconds)...")
        time.sleep(delay_seconds)

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
            success_msg = f"Successfully Uploaded to Facebook! Video ID: {result['id']}"
            print(success_msg)
            logging.info(success_msg)
            updated_rows_count = len(sheet.get_all_values())
            sheet.update_cell(updated_rows_count, 4, "Uploaded to FB")
        else:
            error_msg = f"Facebook upload fail ho gaya! Error: {result}"
            print(error_msg)
            logging.error(error_msg)

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        critical_error = f"Automation script me unexpected error aa gaya: {str(e)}"
        print(critical_error)
        logging.critical(critical_error)

if __name__ == "__main__":
    run_automation()
    
