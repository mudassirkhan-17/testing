#!/usr/bin/env python3
"""
PHASE 2D: INTELLIGENT COMBINING
================================================================================
This script combines the best text from each page based on smart selection results
from Phase 2C, creating the final combined file for LLM extraction.

Process:
1. Read smart selection results from Phase 2C
2. Read PyMuPDF clean pages and OCR all pages
3. For each page, select the best text based on LLM decision
4. Create final combined file with optimal text per page
"""

import json
import os
import re
from datetime import datetime

def read_smart_selection_results():
    """Read smart selection results from Phase 2C"""
    selection_file = "smart_selection_results.json"
    
    if not os.path.exists(selection_file):
        print("Error: Smart selection results not found!")
        print("Please run Phase 2C first.")
        return {}
    
    print(f"Reading smart selection results from: {selection_file}")
    
    with open(selection_file, 'r', encoding='utf-8') as f:
        selection_results = json.load(f)
    
    print(f"Found selection results for {len(selection_results)} pages")
    return selection_results

def read_pymupdf_clean_pages():
    """Read PyMuPDF clean pages only"""
    clean_file = "pymupdf_clean_pages_only.txt"
    
    if not os.path.exists(clean_file):
        print("Error: PyMuPDF clean pages file not found!")
        return {}
    
    print(f"Reading PyMuPDF clean pages from: {clean_file}")
    
    clean_pages = {}
    with open(clean_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Extract clean pages
        page_sections = re.findall(r'PAGE (\d+):.*?TEXT CONTENT:\n(.*?)(?=\nPAGE \d+:|$)', content, re.DOTALL)
        
        for page_num, page_text in page_sections:
            clean_pages[int(page_num)] = page_text.strip()
    
    print(f"Found {len(clean_pages)} PyMuPDF clean pages: {list(clean_pages.keys())}")
    return clean_pages

def read_ocr_all_pages():
    """Read OCR all pages results"""
    ocr_file = "ocr_all_pages_results.txt"
    
    if not os.path.exists(ocr_file):
        print("Error: OCR results file not found!")
        return {}
    
    print(f"Reading OCR all pages from: {ocr_file}")
    
    ocr_pages = {}
    with open(ocr_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Extract OCR pages
        page_sections = re.findall(r'PAGE (\d+):.*?OCR EXTRACTED TEXT:.*?----------------------------------------\n(.*?)(?=\nPAGE \d+:|$)', content, re.DOTALL)
        
        for page_num, page_text in page_sections:
            ocr_pages[int(page_num)] = page_text.strip()
    
    print(f"Found {len(ocr_pages)} OCR pages: {list(ocr_pages.keys())}")
    return ocr_pages

def create_intelligent_combined_file(selection_results, pymupdf_pages, ocr_pages):
    """Create final combined file with best text from each page"""
    
    combined_file = "intelligent_combined_all_pages.txt"
    
    print("PHASE 2D: INTELLIGENT COMBINING")
    print("=" * 80)
    print(f"Creating intelligent combined file: {combined_file}")
    print("=" * 80)
    
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write("INTELLIGENT COMBINED PDF EXTRACTION RESULTS - ALL PAGES\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Method: Smart LLM Selection + Intelligent Combining\n")
        f.write(f"Total Pages: {len(selection_results)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Count selections by source
        pymupdf_count = len([s for s in selection_results.values() if s['selected_source'] == 'PyMuPDF'])
        ocr_count = len([s for s in selection_results.values() if s['selected_source'] == 'OCR'])
        
        f.write("INTELLIGENT SELECTION SUMMARY:\n")
        f.write("-" * 40 + "\n")
        f.write(f"PyMuPDF Selected: {pymupdf_count} pages\n")
        f.write(f"OCR Selected: {ocr_count} pages\n")
        f.write(f"Total Pages: {len(selection_results)} pages\n")
        f.write("=" * 80 + "\n\n")
        
        # Process each page in order
        for page_num_str in sorted(selection_results.keys(), key=int):
            page_num = int(page_num_str)  # Convert string to int
            selection = selection_results[page_num_str]
            selected_source = selection['selected_source']
            reason = selection['reason']
            confidence = selection['confidence']
            
            # Get the selected text
            if selected_source == 'PyMuPDF':
                page_text = pymupdf_pages.get(page_num, '')
                source_info = f"PyMuPDF (Clean)"
            else:  # OCR
                page_text = ocr_pages.get(page_num, '')
                source_info = f"OCR (All Pages)"
            
            f.write(f"PAGE {page_num} ({source_info}):\n")
            f.write("-" * 50 + "\n")
            f.write(f"Selected Source: {selected_source}\n")
            f.write(f"Reason: {reason}\n")
            f.write(f"Confidence: {confidence}\n")
            f.write(f"Characters: {len(page_text):,}\n")
            f.write(f"Lines: {len([line for line in page_text.split(chr(10)) if line.strip()])}\n")
            f.write("\nTEXT CONTENT:\n")
            f.write("-" * 30 + "\n")
            f.write(page_text)
            f.write("\n" + "=" * 80 + "\n\n")
    
    return combined_file

def generate_selection_summary(selection_results):
    """Generate detailed selection summary"""
    
    summary_file = "intelligent_combining_summary.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("INTELLIGENT COMBINING SUMMARY - PHASE 2D\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Count by source
        pymupdf_pages = [p for p, s in selection_results.items() if s['selected_source'] == 'PyMuPDF']
        ocr_pages = [p for p, s in selection_results.items() if s['selected_source'] == 'OCR']
        
        f.write("SELECTION BREAKDOWN:\n")
        f.write("-" * 30 + "\n")
        f.write(f"PyMuPDF Selected: {len(pymupdf_pages)} pages\n")
        f.write(f"OCR Selected: {len(ocr_pages)} pages\n")
        f.write(f"Total Pages: {len(selection_results)} pages\n\n")
        
        f.write("PYMUPDF SELECTED PAGES:\n")
        f.write("-" * 30 + "\n")
        for page_num in sorted(pymupdf_pages):
            selection = selection_results[page_num]
            f.write(f"Page {int(page_num):2d}: {selection['reason']} (confidence: {selection['confidence']})\n")
        
        f.write("\nOCR SELECTED PAGES:\n")
        f.write("-" * 30 + "\n")
        for page_num in sorted(ocr_pages):
            selection = selection_results[page_num]
            f.write(f"Page {int(page_num):2d}: {selection['reason']} (confidence: {selection['confidence']})\n")
        
        f.write("\nQUALITY ANALYSIS:\n")
        f.write("-" * 30 + "\n")
        high_conf = len([s for s in selection_results.values() if s['confidence'] == 'high'])
        medium_conf = len([s for s in selection_results.values() if s['confidence'] == 'medium'])
        low_conf = len([s for s in selection_results.values() if s['confidence'] == 'low'])
        
        f.write(f"High Confidence Selections: {high_conf}\n")
        f.write(f"Medium Confidence Selections: {medium_conf}\n")
        f.write(f"Low Confidence Selections: {low_conf}\n")
    
    return summary_file

def generate_console_summary(selection_results):
    """Generate console summary"""
    print(f"\n{'='*80}")
    print("PHASE 2D SUMMARY - INTELLIGENT COMBINING")
    print(f"{'='*80}")
    
    pymupdf_count = len([s for s in selection_results.values() if s['selected_source'] == 'PyMuPDF'])
    ocr_count = len([s for s in selection_results.values() if s['selected_source'] == 'OCR'])
    
    print(f"Total Pages Processed: {len(selection_results)}")
    print(f"PyMuPDF Selected: {pymupdf_count}")
    print(f"OCR Selected: {ocr_count}")
    
    # Show confidence breakdown
    high_conf = len([s for s in selection_results.values() if s['confidence'] == 'high'])
    medium_conf = len([s for s in selection_results.values() if s['confidence'] == 'medium'])
    low_conf = len([s for s in selection_results.values() if s['confidence'] == 'low'])
    
    print(f"\nConfidence Breakdown:")
    print(f"  High: {high_conf}")
    print(f"  Medium: {medium_conf}")
    print(f"  Low: {low_conf}")
    
    print(f"\n[SUCCESS] Intelligent combining completed!")
    print(f"PyMuPDF pages: {sorted([p for p, s in selection_results.items() if s['selected_source'] == 'PyMuPDF'])}")
    print(f"OCR pages: {sorted([p for p, s in selection_results.items() if s['selected_source'] == 'OCR'])}")

if __name__ == "__main__":
    print("PHASE 2D: INTELLIGENT COMBINING")
    print("=" * 80)
    
    # Read smart selection results
    selection_results = read_smart_selection_results()
    
    if not selection_results:
        print("Error: No selection results found!")
        exit(1)
    
    # Read both text sources
    pymupdf_pages = read_pymupdf_clean_pages()
    ocr_pages = read_ocr_all_pages()
    
    # Create intelligent combined file
    combined_file = create_intelligent_combined_file(selection_results, pymupdf_pages, ocr_pages)
    
    # Generate summary
    summary_file = generate_selection_summary(selection_results)
    
    # Generate console summary
    generate_console_summary(selection_results)
    
    print(f"\n{'='*80}")
    print("FILES GENERATED:")
    print(f"{'='*80}")
    print(f"Intelligent combined file: {combined_file}")
    print(f"Combining summary: {summary_file}")
    print(f"\nPhase 2D complete! Ready for Phase 3 (LLM Field Extraction).")
