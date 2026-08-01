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

# GitHub Secrets se dono Facebook tokens secure tareeqe se uthayega
PAGE_TOKENS = [
    os.getenv('FB_TOKEN_1'),
    os.getenv('FB_TOKEN_2')
]

def authenticate_google():
    # --- GOOGLE JSON KEY GUIDE ---
    # 1. Google Cloud Console (console.cloud.google.com) par jao.
    # 2. Service Account ki JSON key download karo.
    # 3. Uss JSON file ka poora text copy karke GitHub ke Secrets me 
    #    'GOOGLE_CREDENTIALS_JSON' naam se save karo.
    
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
    print("--- Multi-Account Automation Process Started ---")
    logging.info("Multi-Account Automation Process Started")
    
    try:
        if not PAGE_TOKENS[0] or not PAGE_TOKENS[1]:
            print("Error: Facebook tokens (FB_TOKEN_1 ya FB_TOKEN_2) GitHub Secrets me nahi mile!")
            logging.error("Facebook tokens missing from environment variables.")
            return

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

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if not file_name.lower().endswith('.mp4') or file_size_mb > 500:
            print(f"File validation fail ho gayi ({file_name})")
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        clean_name = os.path.splitext(file_name)[0]
        description, hashtags = get_smart_caption_and_tags(clean_name)
        full_caption = f"{description}\n\n{hashtags}"

        sheet.append_row([file_name, description, hashtags, "Downloaded"])

        for index, token in enumerate(PAGE_TOKENS, start=1):
            delay_seconds = random.randint(10, 25)
            print(f"Account {index} par upload karne se pehle wait ho raha hai ({delay_seconds}s)...")
            time.sleep(delay_seconds)

            print(f"Uploading video to Facebook Account {index}...")
            url = f"https://graph-video.facebook.com/v25.0/me/videos"
            payload = {
                'description': full_caption,
                'access_token': token
            }
            
            with open(file_path, 'rb') as video_file:
                files = {'source': video_file}
                response = requests.post(url, data=payload, files=files)
                result = response.json()
                
            print(f"Facebook API Response (Account {index}): {result}")

            if 'id' in result:
                success_msg = f"Account {index} par Successfully Uploaded! Video ID: {result['id']}"
                print(success_msg)
                logging.info(success_msg)
            else:
                error_msg = f"Account {index} upload fail! Error: {result}"
                print(error_msg)
                logging.error(error_msg)

        updated_rows_count = len(sheet.get_all_values())
        sheet.update_cell(updated_rows_count, 4, "Uploaded to Both FBs")

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        critical_error = f"Automation script me unexpected error aa gaya: {str(e)}"
        print(critical_error)
        logging.critical(critical_error)

if __name__ == "__main__":
    run_automation()
            
