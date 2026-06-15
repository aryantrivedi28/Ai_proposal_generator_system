"""Google Docs integration - Step 1 of production build"""

import os
import pickle
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class GoogleDocsExporter:
    """Export proposals to Google Docs for collaborative editing"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, credentials_path: str = "config/google_credentials.json"):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path("config/token.pickle")
        self.docs_service = None
        self.drive_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google APIs"""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
                print("✅ Loaded existing credentials")
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                print("✅ Refreshed credentials")
            else:
                if not self.credentials_path.exists():
                    print(f"❌ Credentials file not found: {self.credentials_path}")
                    print("\n📋 Setup Instructions:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a new project")
                    print("3. Enable Google Docs API and Google Drive API")
                    print("4. Create OAuth 2.0 credentials (Desktop app)")
                    print("5. Download JSON and save as config/google_credentials.json")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("✅ New authentication successful")
            
            # Save token
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build services
        self.docs_service = build('docs', 'v1', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
        print("✅ Google Docs service ready")
    
    def upload_proposal(self, docx_path: str, title: str = None) -> dict:
        """Upload DOCX to Google Docs"""
        
        if not self.docs_service:
            return {"success": False, "error": "Not authenticated"}
        
        docx_path = Path(docx_path)
        if not docx_path.exists():
            return {"success": False, "error": f"File not found: {docx_path}"}
        
        if not title:
            title = f"Proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Upload to Drive
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            media = MediaFileUpload(
                str(docx_path),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            # Make it editable
            self.drive_service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'writer'}
            ).execute()
            
            doc_url = f"https://docs.google.com/document/d/{file_id}/edit"
            
            return {
                "success": True,
                "file_id": file_id,
                "url": doc_url,
                "title": title
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}