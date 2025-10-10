#!/usr/bin/env python3
"""
PHASE 5: SIMPLE DATA EXPORT
Export final validated fields to CSV and formatted text
"""

import json
import csv
from datetime import datetime

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

def create_csv_export(fields_data):
    """Create CSV export"""
    try:
        with open('insurance_fields_export.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header row
            writer.writerow(["Field Name", "LLM Value", "VLM Value", "Final Value", "Confidence", "Source Page"])
            
            # Data rows
            for field_name, field_data in fields_data.items():
                row = [
                    field_name,
                    format_field_value(field_data.get('llm_value')),
                    format_field_value(field_data.get('vlm_value')),
                    format_field_value(field_data.get('final_value')),
                    field_data.get('confidence', 'unknown'),
                    field_data.get('source_page', '')
                ]
                writer.writerow(row)
        
        print(f"[SUCCESS] CSV export created: insurance_fields_export.csv")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create CSV export: {e}")
        return False

def create_formatted_text_export(fields_data):
    """Create formatted text export"""
    try:
        with open('insurance_fields_formatted.txt', 'w', encoding='utf-8') as f:
            f.write("INSURANCE FIELDS EXTRACTION RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Count statistics
            total_fields = len(fields_data)
            llm_fields = sum(1 for data in fields_data.values() if data.get('llm_value') is not None)
            vlm_fields = sum(1 for data in fields_data.values() if data.get('vlm_value') is not None)
            agreed_fields = sum(1 for data in fields_data.values() 
                              if data.get('llm_value') == data.get('vlm_value') and data.get('llm_value') is not None)
            
            f.write("STATISTICS:\n")
            f.write(f"Total Fields: {total_fields}\n")
            f.write(f"LLM Extracted: {llm_fields} ({llm_fields/total_fields*100:.1f}%)\n")
            f.write(f"VLM Extracted: {vlm_fields} ({vlm_fields/total_fields*100:.1f}%)\n")
            f.write(f"Agreement Rate: {agreed_fields} ({agreed_fields/total_fields*100:.1f}%)\n\n")
            
            f.write("FIELD DETAILS:\n")
            f.write("-" * 80 + "\n")
            
            for field_name, field_data in fields_data.items():
                f.write(f"\nField: {field_name}\n")
                f.write(f"  LLM Value: {format_field_value(field_data.get('llm_value'))}\n")
                f.write(f"  VLM Value: {format_field_value(field_data.get('vlm_value'))}\n")
                f.write(f"  Final Value: {format_field_value(field_data.get('final_value'))}\n")
                f.write(f"  Confidence: {field_data.get('confidence', 'unknown')}\n")
                f.write(f"  Source Page: {field_data.get('source_page', '')}\n")
        
        print(f"[SUCCESS] Formatted text export created: insurance_fields_formatted.txt")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create formatted text export: {e}")
        return False

def create_simple_table_export(fields_data):
    """Create simple table format for easy copying to Google Sheets"""
    try:
        with open('insurance_fields_table.txt', 'w', encoding='utf-8') as f:
            f.write("COPY-PASTE READY FOR GOOGLE SHEETS:\n")
            f.write("=" * 80 + "\n\n")
            
            # Header
            f.write("Field Name\tLLM Value\tVLM Value\tFinal Value\tConfidence\tSource Page\n")
            
            # Data rows (tab-separated for easy copy-paste)
            for field_name, field_data in fields_data.items():
                row = f"{field_name}\t{format_field_value(field_data.get('llm_value'))}\t{format_field_value(field_data.get('vlm_value'))}\t{format_field_value(field_data.get('final_value'))}\t{field_data.get('confidence', 'unknown')}\t{field_data.get('source_page', '')}\n"
                f.write(row)
        
        print(f"[SUCCESS] Table format created: insurance_fields_table.txt")
        print("[INFO] You can copy-paste this directly into Google Sheets!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create table format: {e}")
        return False

def main():
    """Main function"""
    print("PHASE 5: SIMPLE DATA EXPORT")
    print("=" * 80)
    print("Export final validated fields to multiple formats")
    print("=" * 80)
    
    # Read final validated fields
    fields_data = read_final_validated_fields()
    if not fields_data:
        print("[ERROR] No data to process")
        return False
    
    print(f"[INFO] Processing {len(fields_data)} fields")
    
    # Create exports
    success1 = create_csv_export(fields_data)
    success2 = create_formatted_text_export(fields_data)
    success3 = create_simple_table_export(fields_data)
    
    if success1 and success2 and success3:
        print("\n[SUCCESS] All exports completed successfully!")
        print("\nFILES CREATED:")
        print("  - insurance_fields_export.csv (Excel/Google Sheets compatible)")
        print("  - insurance_fields_formatted.txt (Human readable)")
        print("  - insurance_fields_table.txt (Copy-paste ready for Google Sheets)")
        print("\n[INFO] You can now:")
        print("  1. Open CSV in Excel/Google Sheets")
        print("  2. Copy-paste from table.txt to Google Sheets")
        print("  3. View formatted results in formatted.txt")
    else:
        print("\n[WARNING] Some exports failed, check errors above")
    
    return success1 and success2 and success3

if __name__ == "__main__":
    main()
