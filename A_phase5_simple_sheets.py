#!/usr/bin/env python3
"""
PHASE 5: SIMPLE GOOGLE SHEETS CONNECTION
Just push data to Google Sheets - NO BULLSHIT!
"""

import json
import gspread
from google.oauth2.service_account import Credentials
import os

def push_to_sheets():
    """Push data to Google Sheets - SIMPLE!"""
    
    print("Starting Google Sheets push...")
    
    # 1. READ THE DATA
    with open('final_validated_fields.json', 'r') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} fields from JSON")
    
    # 2. SETUP GOOGLE SHEETS (you provide credentials.json)
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    
    print("Connected to Google Sheets!")
    
    # 3. OPEN YOUR SHEET (you provide sheet name)
    sheet = client.open("Insurance Fields Data").sheet1
    
    print("Opened sheet: Insurance Fields Data")
    
    # 4. CLEAR AND PUSH DATA
    sheet.clear()
    print("Cleared existing data")
    
    # Prepare all data at once (BATCH UPDATE)
    all_rows = []
    
    # Header row
    all_rows.append(["Field Name", "LLM Value", "VLM Value", "Final Value", "Confidence", "Source Page"])
    
    # Data rows
    for field_name, field_data in data.items():
        row = [
            field_name,
            field_data.get('llm_value', 'null'),
            field_data.get('vlm_value', 'null'), 
            field_data.get('final_value', 'null'),
            field_data.get('confidence', 'unknown'),
            field_data.get('source_page', '')
        ]
        all_rows.append(row)
    
    # Push ALL data in ONE API call (no rate limit issues!)
    sheet.update('A1', all_rows)
    print(f"Added {len(all_rows)} rows in single batch update")
    
    print(f"DONE! Pushed {len(all_rows)} rows to Google Sheets!")
    print("Check your Google Sheet: Insurance Fields Data")

if __name__ == "__main__":
    push_to_sheets()
