#!/usr/bin/env python3
"""
CLEANUP UTILITY: Remove completely empty rows from Google Sheets
Keeps rows where at least ONE carrier has data in LLM Value columns
"""

import gspread
from google.oauth2.service_account import Credentials
import os

def cleanup_empty_rows():
    """Remove rows where all LLM Value columns are empty"""
    
    print("CLEANUP UTILITY: Remove Empty Rows from Google Sheets")
    print("=" * 80)
    
    # 1. DYNAMIC PATH DETECTION
    current_dir = os.getcwd()
    if current_dir.endswith('src'):
        config_dir = '../config'
    else:
        config_dir = 'config'
    
    # 2. SETUP GOOGLE SHEETS
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds_file = f"{config_dir}/credentials.json"
    if not os.path.exists(creds_file):
        print(f"❌ Credentials file not found: {creds_file}")
        return False
    
    creds = Credentials.from_service_account_file(creds_file, scopes=scope)
    client = gspread.authorize(creds)
    
    print("✅ Connected to Google Sheets!")
    
    # 3. OPEN SHEET
    try:
        sheet = client.open("Insurance Fields Data").sheet1
        print("✅ Opened sheet: Insurance Fields Data")
    except Exception as e:
        print(f"❌ Could not open sheet: {e}")
        return False
    
    # 4. GET ALL DATA
    all_data = sheet.get_all_values()
    print(f"✅ Loaded {len(all_data)} rows from sheet")
    
    if not all_data:
        print("❌ No data in sheet!")
        return False
    
    # 5. IDENTIFY COLUMNS
    header = all_data[0]
    print(f"\nHeaders: {header}")
    
    # Find LLM Value column indices (skip "Field Name" and "Source Page")
    llm_columns = []
    for i, col in enumerate(header):
        if "LLM Value" in col:
            llm_columns.append(i)
    
    print(f"✅ Found {len(llm_columns)} LLM Value columns: {llm_columns}")
    
    # 6. IDENTIFY EMPTY ROWS
    rows_to_delete = []
    rows_to_keep = []
    
    for row_idx in range(1, len(all_data)):  # Skip header
        row = all_data[row_idx]
        field_name = row[0] if row else ""
        
        # Check if all LLM Value columns are empty
        all_empty = True
        for col_idx in llm_columns:
            value = row[col_idx].strip() if col_idx < len(row) else ""
            if value:  # If ANY column has data
                all_empty = False
                break
        
        if all_empty:
            rows_to_delete.append(row_idx)
            print(f"  ❌ EMPTY: {field_name}")
        else:
            rows_to_keep.append(row_idx)
            print(f"  ✅ KEEP:  {field_name}")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Total rows: {len(all_data) - 1}")
    print(f"  Rows to DELETE: {len(rows_to_delete)}")
    print(f"  Rows to KEEP: {len(rows_to_keep)}")
    print(f"{'='*80}")
    
    if not rows_to_delete:
        print("✅ No empty rows to delete!")
        return True
    
    # 7. DELETE ROWS (in reverse order to maintain indices)
    print(f"\n🗑️  Deleting {len(rows_to_delete)} empty rows...")
    
    for row_idx in sorted(rows_to_delete, reverse=True):
        sheet.delete_rows(row_idx + 1)  # gspread uses 1-based indexing
        print(f"  ✅ Deleted row {row_idx + 1}")
    
    print(f"\n{'='*80}")
    print("✅ CLEANUP COMPLETE!")
    print("✅ All empty rows have been removed!")
    print(f"{'='*80}")
    
    return True

if __name__ == "__main__":
    cleanup_empty_rows()
