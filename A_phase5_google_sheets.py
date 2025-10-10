#!/usr/bin/env python3
"""
PHASE 5: GOOGLE SHEETS INTEGRATION
Push final validated fields to Google Sheets with clean format
"""

import json
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def setup_google_sheets():
    """Setup Google Sheets API connection"""
    try:
        # Google Sheets API scope
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Service account credentials (you'll need to create this)
        creds = Credentials.from_service_account_file(
            'google_sheets_credentials.json', scopes=scope
        )
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"[ERROR] Google Sheets setup failed: {e}")
        print("[INFO] You need to create 'google_sheets_credentials.json' file")
        return None

def read_final_validated_fields():
    """Read the final validated fields JSON"""
    try:
        with open('final_validated_fields.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read final_validated_fields.json: {e}")
        return None

def format_field_value(value):
    """Format field value for display"""
    if value is None:
        return "null"
    elif isinstance(value, str):
        return value
    else:
        return str(value)

def create_sheets_data(fields_data):
    """Create data for Google Sheets"""
    sheets_data = []
    
    # Header row
    headers = ["Field Name", "LLM Value", "VLM Value", "Final Value", "Confidence"]
    sheets_data.append(headers)
    
    # Data rows
    for field_name, field_data in fields_data.items():
        row = [
            field_name,
            format_field_value(field_data.get('llm_value')),
            format_field_value(field_data.get('vlm_value')),
            format_field_value(field_data.get('final_value')),
            field_data.get('confidence', 'unknown')
        ]
        sheets_data.append(row)
    
    return sheets_data

def push_to_google_sheets(sheets_data, spreadsheet_name="Insurance Fields Analysis"):
    """Push data to Google Sheets"""
    try:
        client = setup_google_sheets()
        if not client:
            return False
        
        # Create or open spreadsheet
        try:
            spreadsheet = client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)
            print(f"[SUCCESS] Created new spreadsheet: {spreadsheet_name}")
        else:
            print(f"[SUCCESS] Opened existing spreadsheet: {spreadsheet_name}")
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet("Insurance Fields")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="Insurance Fields", rows=100, cols=10)
        
        # Clear existing data
        worksheet.clear()
        
        # Update with new data
        worksheet.update('A1', sheets_data)
        
        # Format header row
        worksheet.format('A1:E1', {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # Auto-resize columns
        worksheet.columns_auto_resize(0, 4)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.update('G1', f"Last Updated: {timestamp}")
        
        print(f"[SUCCESS] Data pushed to Google Sheets successfully!")
        print(f"[INFO] Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to push to Google Sheets: {e}")
        return False

def create_local_csv_backup(sheets_data):
    """Create local CSV backup"""
    try:
        import csv
        
        with open('insurance_fields_export.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(sheets_data)
        
        print(f"[SUCCESS] Local CSV backup created: insurance_fields_export.csv")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create CSV backup: {e}")
        return False

def main():
    """Main function"""
    print("PHASE 5: GOOGLE SHEETS INTEGRATION")
    print("=" * 80)
    print("Push final validated fields to Google Sheets")
    print("=" * 80)
    
    # Read final validated fields
    fields_data = read_final_validated_fields()
    if not fields_data:
        print("[ERROR] No data to process")
        return False
    
    print(f"[INFO] Processing {len(fields_data)} fields")
    
    # Create sheets data
    sheets_data = create_sheets_data(fields_data)
    
    # Create local CSV backup
    create_local_csv_backup(sheets_data)
    
    # Push to Google Sheets
    success = push_to_google_sheets(sheets_data)
    
    if success:
        print("\n[SUCCESS] Google Sheets integration completed!")
        print("[INFO] Check your Google Drive for the spreadsheet")
    else:
        print("\n[INFO] Google Sheets push failed, but CSV backup was created")
    
    return success

if __name__ == "__main__":
    main()
