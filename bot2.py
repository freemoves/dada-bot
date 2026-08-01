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
import json

# --- Logging Setup ---
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds',
    'https://spreadsheets.google.com/auth/spreadsheets'
]

FOLDER_ID = '1qQrJbihELRD89ERudZIZoAoagVp_QeyT'
SPREADSHEET_ID = '1fXl3zUmJn6JTbGS15dtGpG5u0o23_-Gx8lFd7gdp3BM'
LOCAL_DOWNLOAD_PATH = tempfile.gettempdir()

PAGE_TOKENS = [
    os.getenv('FB_TOKEN_1'),
    os.getenv('FB_TOKEN_2')
]

def authenticate_google():
    # Direct teri di gayi service account credentials yahan set hain bhai
    creds_dict = {
      "type": "service_account",
      "project_id": "cogent-dragon-502615-v5",
      "private_key_id": "9c2f66477dcdc2389bd758eadf076577afd1102a",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC2IeAHSQNWKI8c\n0SFAliX3vaKVc4TRNfp8jr4koEZSl1BqRIsJMdcS9QhfRYZZ4bDUEmNTC+pMcLx0\nxdvZiUfHOsc8Glm03U0oMdazmEvCdWY6UFWzMWF59fCZYxEXMucP5pc4EkFdXCz0\n7IeKeGSG4Ku1WfaORFmG+lyx6SRL8zy4GQozAz2JmaoFF+q/cnXL2LSewFRP4AcK\nP0b4wrLRz8bb/GxXHmFjtes77BOTRsO4G+snTkR+Bt0Xz2JUmsPKNqw2FXEx0lqA\nwRV4BK9Msu8+oGhxG71acXiFlZzIU8FlB6OZUBs7nG5YvDUv7u9rPaejrNH2fwoC\noI67hHVnAgMBAAECggEAOfRxix/qleH2GB9by2d70Wdgctn9a20XtcbeLl1pwyIv\nDoGdFGHtpDSgY2CGLdepIvJu9KAYABbngOjs2j3av0Su3SstXGYHBUFGpoNRqCEf\nVHL3sjuGXv6pfsWNTKp/6AliGQ+GCSUpkQ4q2x8QLfMT8HMeB4ssSc0k7d/YEupb\nhqxRpj6MpWG3JZ9U8A/p3Y3pMi8ahNEepshZA/DLDyV/YI/HYqP6NVUd5ecfgHaR\ndVhhWQ+oFXJjEMLpxEubqcHnYahvNfG+/j6HlkBJGwa7t/4bjTasf+W6yx9m4BH\njLpSu724R3YFqmPq8zfccpyptZ4uLyJrPyD1pGdMMQKBgQDqeN/AHEJRl5x8BkpT\ndqLrAGYjhiZuFUYfgHAZzoAn9xq94ciHyYOyE+PWKSFPOWZDL1z7IFQedRcO03NB\nEIKxLnA3Vo5Bfjt6CyCQmTRXLugxle7Fi6QOfM2C8+DGKtm3l+vfAKLz6MlENfkG\nwxHfMj1hE8hcmndfhEygaPzrFQKBgQDG2sjv513R/roS0yT2oDqKA/4iOD6bkX5w\nC/H+PkviYbW3UV8UbHejojlns6RTkN8s4bu6sQycdwVv6hnK3gwStXA0DMxbe8oX\n+UxH/ZZ7dAbNVd6/B8Zic1pXmDH+N5Bw598O8B+v0PFl/NXS+yFewe+/mSZVOtQm\5vblMm3NiwKBgQCeocann7bSouNRGaRhkWsp2OxBbnpDkgsONwQgwY/8+fZSrxXP\noGuEKGbFtq/9fJUOMVYT5Mxkis1dz3szcuso2oU7O0klUDUHHc4bZjt+HJMlMQ4J\nAq+syYz04vCYwdbomlUPW8vjfwPkLSvdAk7uFXxnWE3/MNZAfi6lfEJY/QKBgQCF\J4NdgWPFdfhLGq+ppWkNedb2OwtRSH+Nr7H/ON+/WwY/FnHAT1FddQdTdWsXue53\nM0Btpph3PQubAPr8aOtUq8HSWK+OormUjA6UNi5JxEu5u0JIUIB69BsOhI8VV0eV\nEu6+JfRR2muKi17yw854kQxlE7wjXh0pX4b7umTkOQKBgGINQM26mcCNbLrK+nXt\nmFAd4sMQ4l43wZ/dDPxoKvjZqfEIzxmBjxd5L3iwaaOsni30aQObGyTTDJeEerxw\nCr+yQquZ+aRXcms97Pa+6dDg42O8kTED4ExwOvq9DBf4yyfQ3Izs+NBk9ikIW53g\ntE2ln4E0WkLLWrT+M8dwDh+j\n-----END PRIVATE KEY-----\n",
      "client_email": "my-bit@cogent-dragon-502615-v5.iam.gserviceaccount.com",
      "client_id": "117485684752432754899",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/my-bit%40cogent-dragon-502615-v5.iam.gserviceaccount.com",
      "universe_domain": "googleapis.com"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_creds:
        json.dump(creds_dict, temp_creds)
        temp_creds_path = temp_creds.name
        
    creds_drive = service_account.Credentials.from_service_account_file(
        temp_creds_path, scopes=['https://www.googleapis.com/auth/drive']
    )
    creds_sheet = service_account.Credentials.from_service_account_file(
        temp_creds_path, scopes=SCOPES
    )
    sheet_client = gspread.authorize(creds_sheet)
    
    try:
        os.remove(temp_creds_path)
    except:
        pass
        
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
        
