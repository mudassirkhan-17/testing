#!/usr/bin/env python3
"""
TEST GOOGLE CREDENTIALS
"""

import gspread
from google.oauth2.service_account import Credentials
import os

def test_credentials():
    """Test if credentials work"""
    
    # Check if file exists
    if not os.path.exists('credentials.json'):
        print("[ERROR] credentials.json file NOT FOUND!")
        print("Put your downloaded JSON file in this folder and rename it to 'credentials.json'")
        return False
    
    try:
        # Setup credentials
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Test connection
        print("[SUCCESS] Credentials loaded successfully!")
        
        # List your sheets
        sheets = client.openall()
        print(f"[SUCCESS] Found {len(sheets)} sheets in your account")
        
        for sheet in sheets:
            print(f"  - {sheet.title}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    test_credentials()
