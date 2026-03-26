import io
import os
import mimetypes

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


SCOPES = ["https://www.googleapis.com/auth/drive.file"]

TOKEN_FILE = "drive/token.json"
CREDENTIALS_FILE =  "drive/client_secret.json"

def get_drive_service():
    try:
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    except Exception as e:
        print("❌ Google Drive Error:", str(e))
        return None





def upload_file_to_drive(file_bytes: bytes, filename: str):

    service = get_drive_service()   # ✅ lazy load

    mime_type, _ = mimetypes.guess_type(filename)

    if mime_type is None:
        mime_type = "application/octet-stream"

    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=mime_type
    )

    file_metadata = {
        "name": filename
    }

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = file.get("id")

    service.permissions().create(
        fileId=file_id,
        body={
            "type": "anyone",
            "role": "reader"
        }
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view"