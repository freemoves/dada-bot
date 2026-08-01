import os
import io
import tempfile
import logging
import random
import time
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import json

# --- Logging Setup ---
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

FOLDER_ID = '1qQrJbihELRD89ERudZIZoAoagVp_QeyT'
SPREADSHEET_ID = '1fXl3zUmJn6JTbGS15dtGpG5u0o23_-Gx8lFd7gdp3BM'
LOCAL_DOWNLOAD_PATH = tempfile.gettempdir()

PAGE_TOKENS = [
    os.getenv('FB_TOKEN_1'),
    os.getenv('FB_TOKEN_2')
]

def authenticate_google():
    creds_json_string = os.getenv('GOOGLE_CREDENTIALS')
    if not creds_json_string:
        raise ValueError("GitHub Secrets me GOOGLE_CREDENTIALS nahi mila!")
        
    creds_dict = json.loads(creds_json_string)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_creds:
        json.dump(creds_dict, temp_creds)
        temp_creds_path = temp_creds.name
        
    creds = service_account.Credentials.from_service_account_file(
        temp_creds_path, scopes=SCOPES
    )
    
    try:
        os.remove(temp_creds_path)
    except:
        pass
        
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    return drive_service, sheets_service

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

        drive_service, sheets_service = authenticate_google()
        sheet_api = sheets_service.spreadsheets()
        
        # Google Sheet se saare purane uploaded/processed filenames nikal lo
        result_range = sheet_api.values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1!A:D').execute()
        list_of_rows = result_range.get('values', [])
        
        # Column A ke saare names jo pehle se sheet me hain
        existing_names = [row[0].strip().lower() for row in list_of_rows[1:] if len(row) > 0]

        query = f"'{FOLDER_ID}' in parents and mimeType contains 'video/' and trashed = false"
        results = drive_service.files().list(q=query, pageSize=50, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print("Google Drive folder me koi video nahi mili!")
            logging.info("Google Drive folder me koi video nahi mili.")
            return

        target_file = None
        for item in items:
            item_name_clean = item['name'].strip().lower()
            # Agar file ka naam sheet me nahi hai, tabhi use target banayenge
            if item_name_clean not in existing_names:
                target_file = item
                break

        if not target_file:
            print("Sabhi videos pehle hi processed/uploaded hain! Koi nayi video nahi mili.")
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

        # Pehle hi sheet me entry daal do taaki agli baar yeh video dobara na uthe
        append_body = {'values': [[file_name, description, hashtags, "Processing"]]}
        sheet_api.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:D',
            valueInputOption='RAW',
            body=append_body
        ).execute()

        # Ab row index pata karo jo abhi add hui hai
        updated_range = sheet_api.values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1!A:D').execute()
        total_rows = len(updated_range.get('values', []))

        success_count = 0
        for index, token in enumerate(PAGE_TOKENS, start=1):
            if not token:
                print(f"Account {index} ka token missing hai, skip kar rahe hain.")
                continue

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
                success_count += 1
            else:
                error_msg = f"Account {index} upload fail! Error: {result}"
                print(error_msg)
                logging.error(error_msg)

        # Status update karo sheet me
        final_status = "Uploaded to Both FBs" if success_count == 2 else f"Uploaded to {success_count}/2 FBs"
        update_body = {'values': [[final_status]]}
        sheet_api.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'Sheet1!D{total_rows}',
            valueInputOption='RAW',
            body=update_body
        ).execute()

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        critical_error = f"Automation script me unexpected error aa gaya: {str(e)}"
        print(critical_error)
        logging.critical(critical_error)

if __name__ == "__main__":
    run_automation()
    
