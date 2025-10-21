#!/usr/bin/env python3
"""
MASTER MULTI-CARRIER INSURANCE EXTRACTION PIPELINE
===============================================================================
This script orchestrates the processing of ALL THREE insurance types:
1. Property Insurance
2. General Liability Insurance  
3. Liquor Insurance

For each carrier, the user selects 3 PDFs (one for each insurance type).
All results are combined into a single stacked Google Sheet.

Usage: python multi_carrier_master.py
"""

import os
import glob
import re
import json
from datetime import datetime

# Import functions from pdf_input_selector
from pdf_input_selector import get_available_pdfs, display_pdf_selection, get_user_selection

# Import Phase 1 functions
from A_phase1_Pymupdf import process_all_pages, save_results

# Import Phase 2 functions
from A_phase2_ocr import process_all_pages_with_ocr, save_ocr_results, get_all_pages_from_phase1

# Import Phase 2C functions
from A_phase2c_smart_selection import process_all_pages_selection, save_selection_results
from A_phase2c_smart_selection import read_pymupdf_clean_pages, read_ocr_all_pages

# Import Phase 2D functions
from A_phase2d_intelligent_combining import create_intelligent_combined_file

# Import Phase 3 functions for all three insurance types
from A_phase3_llm_extraction import read_combined_file, create_chunks, extract_with_llm, merge_extraction_results, save_extraction_results, create_final_validated_fields
from A_phase3_llm_GeneralLiability import read_combined_file as read_gl_combined_file, create_chunks as create_gl_chunks, extract_with_llm as extract_gl_with_llm, merge_extraction_results as merge_gl_extraction_results, save_extraction_results as save_gl_extraction_results, create_final_validated_fields as create_gl_final_validated_fields
from A_phase3_llm_Liqour import read_combined_file as read_liq_combined_file, create_chunks as create_liq_chunks, extract_with_llm as extract_liq_with_llm, merge_extraction_results as merge_liq_extraction_results, save_extraction_results as save_liq_extraction_results, create_final_validated_fields as create_liq_final_validated_fields

# Import Phase 4 functions
from A_phase5_simple_sheets import push_to_sheets

def get_user_pdf_selection(pdf_files, insurance_type):
    """Get user's PDF selection for specific insurance type"""
    print(f"\nPDF Selection for {insurance_type}:")
    display_pdf_selection(pdf_files)
    selected_pdf = get_user_selection(pdf_files)
    pdf_path = f"pdf/{selected_pdf}"
    print(f"Path: {pdf_path}")
    return selected_pdf, pdf_path

def get_carrier_setup():
    """Get carrier setup from user with all three insurance types"""
    print("=" * 80)
    print("MASTER CARRIER SETUP - ALL INSURANCE TYPES")
    print("=" * 80)
    
    # Ask number of carriers
    while True:
        try:
            num_carriers = int(input("How many carriers do you want to process? (1, 2, 3, etc.): "))
            if num_carriers >= 1:
                break
            print("Please enter 1 or more carriers")
        except ValueError:
            print("Please enter a valid number")
    
    # Get available PDFs
    pdf_files = get_available_pdfs()
    if not pdf_files:
        print("No PDF files available!")
        return []
    
    # Get carrier names and PDF selections for all insurance types
    carriers = []
    for i in range(num_carriers):
        print(f"\n{'='*80}")
        print(f"CARRIER {i+1} SETUP")
        print(f"{'='*80}")
        
        # Get carrier name
        while True:
            carrier_name = input(f"Enter name for Carrier {i+1}: ").strip()
            if carrier_name:
                break
            print("Please enter a valid carrier name")
        
        # Get PDF selections for all three insurance types
        print(f"\nPDF Selection for {carrier_name}:")
        print("You need to select 3 PDFs - one for each insurance type:")
        
        carrier_pdfs = {}
        insurance_types = ["Property", "General Liability", "Liquor"]
        
        for insurance_type in insurance_types:
            selected_pdf, pdf_path = get_user_pdf_selection(pdf_files, insurance_type)
            carrier_pdfs[insurance_type.lower().replace(" ", "_")] = {
                'pdf_file': selected_pdf,
                'pdf_path': pdf_path
            }
        
        carriers.append({
            'name': carrier_name,
            'property': carrier_pdfs['property'],
            'general_liability': carrier_pdfs['general_liability'],
            'liquor': carrier_pdfs['liquor']
        })
    
    print(f"\nCarriers setup complete!")
    return carriers

def process_carrier_insurance_type(carrier, insurance_type, pdf_info):
    """Process a single insurance type for a single carrier"""
    print(f"\n{'='*60}")
    print(f"PROCESSING {carrier['name'].upper()} - {insurance_type.upper()}")
    print(f"{'='*60}")
    
    # Store original directory
    original_dir = os.getcwd()
    print(f"DEBUG: original_dir in process_carrier_insurance_type: {original_dir}")

    try:
        # Change to property directory (one level up from src/)
        property_dir = os.path.join(original_dir, "..")
        print(f"DEBUG: calculated property_dir: {property_dir}")
        print(f"DEBUG: property_dir exists: {os.path.exists(property_dir)}")
        os.chdir(property_dir)
        print(f"Changed to directory: {os.getcwd()}")
        
        # PHASE 1: Process all pages using existing function
        print(f"\nPhase 1: PyMuPDF Extraction for {carrier['name']} - {insurance_type}")
        phase1_results = process_all_pages(pdf_info['pdf_path'])
        save_results(phase1_results)
        rename_files_with_carrier_prefix(carrier['name'], insurance_type, "phase1")
        
        # PHASE 2: OCR processing
        print(f"\nPhase 2: OCR Processing for {carrier['name']} - {insurance_type}")
        all_pages = get_all_pages_from_carrier_report(carrier['name'], insurance_type)
        if all_pages:
            phase2_results = process_all_pages_with_ocr(pdf_info['pdf_path'], all_pages)
            save_ocr_results(phase2_results)
            rename_files_with_carrier_prefix(carrier['name'], insurance_type, "phase2")
        else:
            print(f"No pages found from Phase 1 for {carrier['name']} - {insurance_type}")
            phase2_results = None
        
        # PHASE 2C: Smart LLM selection
        print(f"\nPhase 2C: Smart LLM Selection for {carrier['name']} - {insurance_type}")
        if phase2_results:
            pymupdf_pages = read_carrier_pymupdf_pages(carrier['name'], insurance_type)
            ocr_pages = read_carrier_ocr_pages(carrier['name'], insurance_type)
            
            if pymupdf_pages and ocr_pages:
                phase2c_results = process_all_pages_selection(pymupdf_pages, ocr_pages)
                save_selection_results(phase2c_results)
                rename_files_with_carrier_prefix(carrier['name'], insurance_type, "phase2c")
            elif ocr_pages and not pymupdf_pages:
                # No PyMuPDF clean pages, use OCR for all pages
                print(f"No PyMuPDF clean pages for {carrier['name']} - {insurance_type}, using OCR for all pages")
                phase2c_results = {}
                for page_num in ocr_pages.keys():
                    phase2c_results[str(page_num)] = {
                        'selected_source': 'OCR',
                        'reason': 'No PyMuPDF clean pages available - using OCR',
                        'confidence': 'high'
                    }
                save_selection_results(phase2c_results)
                rename_files_with_carrier_prefix(carrier['name'], insurance_type, "phase2c")
            else:
                print(f"Could not read PyMuPDF or OCR pages for {carrier['name']} - {insurance_type}")
                phase2c_results = None
        else:
            print(f"No OCR results for Phase 2C for {carrier['name']} - {insurance_type}")
            phase2c_results = None
        
        # PHASE 2D: Intelligent combining
        print(f"\nPhase 2D: Intelligent Combining for {carrier['name']} - {insurance_type}")
        if phase2c_results:
            pymupdf_pages_2d = read_carrier_pymupdf_pages(carrier['name'], insurance_type)
            ocr_pages_2d = read_carrier_ocr_pages(carrier['name'], insurance_type)
            
            if ocr_pages_2d:  # Only need OCR pages since PyMuPDF might be empty
                pymupdf_text_only = {k: v['text'] for k, v in pymupdf_pages_2d.items()} if pymupdf_pages_2d else {}
                ocr_text_only = {k: v['text'] for k, v in ocr_pages_2d.items()}
                
                carrier_combined_file = create_carrier_combined_file(carrier['name'], insurance_type, phase2c_results, pymupdf_text_only, ocr_text_only)
                phase2d_results = carrier_combined_file
            else:
                print(f"Could not read OCR pages for Phase 2D for {carrier['name']} - {insurance_type}")
                phase2d_results = None
        else:
            print(f"No Phase 2C results for Phase 2D for {carrier['name']} - {insurance_type}")
            phase2d_results = None
        
        # PHASE 3: LLM Field Extraction (using appropriate extraction function)
        print(f"\nPhase 3: LLM Field Extraction for {carrier['name']} - {insurance_type}")
        if phase2d_results:
            carrier_combined_file = f"{carrier['name']}_{insurance_type}_intelligent_combined_all_pages.txt"
            all_pages = read_carrier_combined_file(carrier_combined_file)
            
            if all_pages:
                # Convert carrier data format to match Phase 3 expectations
                pages_list = []
                for page_num, page_text in all_pages.items():
                    pages_list.append({
                        'page_num': page_num,
                        'text': page_text,
                        'source': 'Combined'
                    })
                
                # Use appropriate extraction function based on insurance type
                if insurance_type == "property":
                    chunks = create_chunks(pages_list, chunk_size=4)
                    extract_func = extract_with_llm
                    merge_func = merge_extraction_results
                    save_func = save_extraction_results
                    create_func = create_final_validated_fields
                elif insurance_type == "general_liability":
                    chunks = create_gl_chunks(pages_list, chunk_size=4)
                    extract_func = extract_gl_with_llm
                    merge_func = merge_gl_extraction_results
                    save_func = save_gl_extraction_results
                    create_func = create_gl_final_validated_fields
                elif insurance_type == "liquor":
                    chunks = create_liq_chunks(pages_list, chunk_size=4)
                    extract_func = extract_liq_with_llm
                    merge_func = merge_liq_extraction_results
                    save_func = save_liq_extraction_results
                    create_func = create_liq_final_validated_fields
                
                all_results = []
                for chunk in chunks:
                    print(f"Processing Chunk {chunk['chunk_num']}/{len(chunks)} for {carrier['name']} - {insurance_type}...")
                    result = extract_func(chunk, chunk['chunk_num'], len(chunks))
                    all_results.append(result)
                
                merged_result = merge_func(all_results)
                save_carrier_extraction_results(carrier['name'], insurance_type, merged_result, all_results)
                create_carrier_final_validated_fields(carrier['name'], insurance_type, merged_result)
                phase3_results = merged_result
            else:
                print(f"Could not read combined file for {carrier['name']} - {insurance_type}")
                phase3_results = None
        else:
            print(f"No Phase 2D results for Phase 3 for {carrier['name']} - {insurance_type}")
            phase3_results = None
        
        print(f"\n{carrier['name']} - {insurance_type} processing completed!")
        return {
            'phase1': phase1_results,
            'phase2': phase2_results,
            'phase2c': phase2c_results,
            'phase2d': phase2d_results,
            'phase3': phase3_results
        }
        
    except Exception as e:
        print(f"Processing failed for {carrier['name']} - {insurance_type}: {e}")
        return None
    finally:
        # Always return to original directory
        os.chdir(original_dir)

def get_all_pages_from_carrier_report(carrier_name, insurance_type):
    """Get all pages from carrier-specific Phase 1 report"""
    import re
    
    # DYNAMIC PATH DETECTION
    results_paths = [
        'results',  # When run from property/ (via mine.py)
        '../results'  # When run from property/src/ (alone)
    ]
    
    results_dir = None
    for path in results_paths:
        if os.path.exists(path) or os.path.exists(os.path.dirname(path) if os.path.dirname(path) else '.'):
            results_dir = path
            break
    
    if not results_dir:
        results_dir = 'results'  # Default fallback
    
    report_file = f"{results_dir}/{carrier_name}_{insurance_type}_phase1_report.txt"
    
    if not os.path.exists(report_file):
        print(f"Error: Carrier Phase 1 report '{report_file}' not found!")
        return []
    
    print(f"Reading total pages from: {report_file}")
    
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'Total Pages Processed: (\d+)', content)
        if match:
            total_pages = int(match.group(1))
            return list(range(1, total_pages + 1))
        else:
            print("Error: Could not find total pages in carrier Phase 1 report.")
            return []

def read_carrier_pymupdf_pages(carrier_name, insurance_type):
    """Read PyMuPDF clean pages for specific carrier and insurance type"""
    import re
    
    # DYNAMIC PATH DETECTION
    results_paths = [
        'results',  # When run from property/ (via mine.py)
        '../results'  # When run from property/src/ (alone)
    ]
    
    results_dir = None
    for path in results_paths:
        if os.path.exists(path) or os.path.exists(os.path.dirname(path) if os.path.dirname(path) else '.'):
            results_dir = path
            break
    
    if not results_dir:
        results_dir = 'results'  # Default fallback
    
    clean_file = f"{results_dir}/{carrier_name}_{insurance_type}_pymupdf_clean_pages_only.txt"
    
    if not os.path.exists(clean_file):
        print(f"Error: Carrier PyMuPDF clean pages '{clean_file}' not found!")
        return {}
    
    print(f"Reading PyMuPDF clean pages from: {clean_file}")
    
    clean_pages = {}
    with open(clean_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Extract clean pages
        page_sections = re.findall(r'PAGE (\d+):.*?TEXT CONTENT:\n(.*?)\n={80}', content, re.DOTALL)
        
        for page_num, page_text in page_sections:
            clean_pages[int(page_num)] = {
                'text': page_text.strip(),
                'source': 'PyMuPDF'
            }
    
    print(f"Found {len(clean_pages)} PyMuPDF clean pages: {list(clean_pages.keys())}")
    return clean_pages

def read_carrier_ocr_pages(carrier_name, insurance_type):
    """Read OCR pages for specific carrier and insurance type"""
    import re
    
    # DYNAMIC PATH DETECTION
    results_paths = [
        'results',  # When run from property/ (via mine.py)
        '../results'  # When run from property/src/ (alone)
    ]
    
    results_dir = None
    for path in results_paths:
        if os.path.exists(path) or os.path.exists(os.path.dirname(path) if os.path.dirname(path) else '.'):
            results_dir = path
            break
    
    if not results_dir:
        results_dir = 'results'  # Default fallback
    
    ocr_file = f"{results_dir}/{carrier_name}_{insurance_type}_ocr_all_pages_results.txt"
    
    if not os.path.exists(ocr_file):
        print(f"Error: Carrier OCR results '{ocr_file}' not found!")
        return {}
    
    print(f"Reading OCR pages from: {ocr_file}")
    
    ocr_pages = {}
    with open(ocr_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Extract OCR pages
        page_sections = re.findall(r'PAGE (\d+):.*?OCR EXTRACTED TEXT:.*?----------------------------------------\n(.*?)\n={80}', content, re.DOTALL)
        
        for page_num, page_text in page_sections:
            ocr_pages[int(page_num)] = {
                'text': page_text.strip(),
                'source': 'OCR'
            }
    
    print(f"Found {len(ocr_pages)} OCR pages: {list(ocr_pages.keys())}")
    return ocr_pages

def create_carrier_combined_file(carrier_name, insurance_type, selection_results, pymupdf_pages, ocr_pages):
    """Create carrier-specific intelligent combined file"""
    # DYNAMIC PATH DETECTION
    current_dir = os.getcwd()
    if current_dir.endswith('src'):
        results_dir = '../results'
    else:
        results_dir = 'results'
    
    # Create carrier-specific filename
    combined_file = f"{results_dir}/{carrier_name}_{insurance_type}_intelligent_combined_all_pages.txt"
    
    print("PHASE 2D: INTELLIGENT COMBINING")
    print("=" * 80)
    print(f"Creating carrier-specific combined file: {combined_file}")
    print("=" * 80)
    
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write(f"INTELLIGENT COMBINED PDF EXTRACTION RESULTS - {carrier_name.upper()} CARRIER - {insurance_type.upper()}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Carrier: {carrier_name}\n")
        f.write(f"Insurance Type: {insurance_type}\n")
        f.write("=" * 80 + "\n\n")
        
        # Selection summary
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
            page_num = int(page_num_str)
            selection = selection_results[page_num_str]
            selected_source = selection['selected_source']
            reason = selection['reason']
            confidence = selection['confidence']
            
            # Get the best text for this page
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
            f.write("\n\n" + "=" * 80 + "\n\n")
    
    print(f"✅ Created carrier-specific combined file: {combined_file}")
    return combined_file

def read_carrier_combined_file(carrier_combined_file):
    """Read carrier-specific combined file for Phase 3"""
    # DYNAMIC PATH DETECTION
    current_dir = os.getcwd()
    if current_dir.endswith('src'):
        results_dir = '../results'
    else:
        results_dir = 'results'
    
    combined_file_path = f"{results_dir}/{carrier_combined_file}"
    
    if not os.path.exists(combined_file_path):
        print(f"Error: Carrier combined file '{combined_file_path}' not found!")
        return {}
    
    print(f"Reading carrier combined file from: {combined_file_path}")
    
    # Read the combined file and extract pages
    all_pages = {}
    with open(combined_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Extract pages using regex
        page_sections = re.findall(r'PAGE (\d+) \(.*?\):\n.*?TEXT CONTENT:\n(.*?)(?=\nPAGE \d+|\n={80}\n\n$)', content, re.DOTALL)
        
        for page_num, page_text in page_sections:
            all_pages[int(page_num)] = page_text.strip()
    
    print(f"Found {len(all_pages)} pages in carrier combined file: {list(all_pages.keys())}")
    return all_pages

def save_carrier_extraction_results(carrier_name, insurance_type, merged_result, all_results):
    """Save carrier-specific extraction results"""
    # DYNAMIC PATH DETECTION
    current_dir = os.getcwd()
    if current_dir.endswith('src'):
        results_dir = '../results'
    else:
        results_dir = 'results'
    
    # Save main extraction results
    extraction_file = f"{results_dir}/{carrier_name}_{insurance_type}_extracted_insurance_fields.json"
    with open(extraction_file, 'w', encoding='utf-8') as f:
        json.dump(merged_result, f, indent=2, ensure_ascii=False)
    
    # Save chunk results
    chunks_file = f"{results_dir}/{carrier_name}_{insurance_type}_extraction_chunks.json"
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved carrier extraction results: {extraction_file}")

def create_carrier_final_validated_fields(carrier_name, insurance_type, merged_result):
    """Create carrier-specific final validated fields for Google Sheets"""
    # DYNAMIC PATH DETECTION
    current_dir = os.getcwd()
    if current_dir.endswith('src'):
        results_dir = '../results'
    else:
        results_dir = 'results'
    
    final_file = f"{results_dir}/{carrier_name}_{insurance_type}_final_validated_fields.json"
    
    # Extract field sources from metadata
    field_sources = {}
    if '_extraction_summary' in merged_result and 'field_sources' in merged_result['_extraction_summary']:
        field_sources = merged_result['_extraction_summary']['field_sources']
    
    # Create final validated fields structure
    final_fields = {}
    for field_name, field_value in merged_result.items():
        # Skip metadata fields
        if field_name.startswith('_'):
            continue
        
        # Get source page(s) for this field
        source_pages = field_sources.get(field_name, [])
        if source_pages:
            source_page = f"Page {source_pages[0]}"
        else:
            source_page = ""
            
        final_fields[field_name] = {
            "value": field_value if field_value is not None else "",
            "confidence": "high",
            "source_page": source_page,
            "carrier": carrier_name,
            "insurance_type": insurance_type
        }
    
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(final_fields, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created carrier final validated fields: {final_file}")

def apply_sheets_formatting(sheet, total_rows, total_cols, insurance_types, carriers):
    """Apply professional formatting to the Google Sheet in a SINGLE API CALL"""
    try:
        print("🎨 Applying professional formatting to Google Sheets (SINGLE BATCH CALL)...")
        
        # Merge company header row
        company_header_range = f'A1:{chr(64 + total_cols)}1'
        sheet.merge_cells(company_header_range)
        print(f"  Merged company header cells: {company_header_range}")
        
        # Get all sheet values to find actual section boundaries
        all_values = sheet.get_all_values()
        
        # Find sections by looking for section headers
        section_starts = {}
        section_ends = {}
        
        for row_idx, row in enumerate(all_values):
            if row and len(row) > 0:
                cell_value = str(row[0]).strip()
                
                if "Property Coverages" in cell_value:
                    section_starts["property"] = row_idx + 1
                    print(f"Found Property Coverages section at row {section_starts['property']}")
                    
                elif "General Liability Coverages" in cell_value:
                    section_starts["general_liability"] = row_idx + 1
                    print(f"Found General Liability Coverages section at row {section_starts['general_liability']}")
                    
                elif "Liquor Coverages" in cell_value:
                    section_starts["liquor"] = row_idx + 1
                    print(f"Found Liquor Coverages section at row {section_starts['liquor']}")
        
        # Calculate section ends
        sorted_starts = sorted([(k, v) for k, v in section_starts.items()], key=lambda x: x[1])
        for idx in range(len(sorted_starts)):
            insurance_type, start_row = sorted_starts[idx]
            col_header_row = start_row + 3
            
            if idx < len(sorted_starts) - 1:
                # For non-last sections, scan backwards from next section to find last data row
                next_section_header = sorted_starts[idx + 1][1]
                end_row = col_header_row  # Default
                
                # Scan backwards from the next section header
                for row_idx in range(next_section_header - 1, col_header_row, -1):
                    row = all_values[row_idx - 1] if row_idx - 1 < len(all_values) else []  # Convert to 0-indexed
                    # Check if first column has data
                    if row and len(row) > 0 and str(row[0]).strip():
                        end_row = row_idx  # Found last data row
                        break
            else:
                # For last section, find the actual last row with data
                end_row = col_header_row  # Default to column header row
                
                # Scan down to find last row with data in first column
                for row_idx in range(col_header_row + 1, len(all_values)):
                    row = all_values[row_idx] if row_idx < len(all_values) else []
                    # Check if first column has data
                    if row and len(row) > 0 and str(row[0]).strip():
                        end_row = row_idx + 1  # Convert to 1-indexed
                    elif end_row > col_header_row:
                        # We found data before, now it's empty - stop here
                        break
            
            section_ends[insurance_type] = end_row
            print(f"{insurance_type}: rows {start_row} to {end_row}")
        
        # Build batch format requests - ALL formatting in ONE API call
        batch_requests = []
        
        # Company header formatting - GREEN background with BLACK text
        batch_requests.append({
            'range': f'A1:{chr(64 + total_cols)}1',
            'format': {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2},  # GREEN
                'textFormat': {'bold': True, 'fontSize': 18, 'foregroundColor': {'red': 0, 'green': 0, 'blue': 0}},  # BLACK
                'horizontalAlignment': 'CENTER',
                'verticalAlignment': 'MIDDLE'
            }
        })
        print(f"📋 Queuing company header formatting")
        
        # First, merge cells for headers and underlines (must be done before formatting)
        for insurance_type in ["property", "general_liability", "liquor"]:
            if insurance_type not in section_starts:
                continue
            
            header_row = section_starts[insurance_type]
            header_range = f'A{header_row}:{chr(64 + total_cols)}{header_row}'
            sheet.merge_cells(header_range)
            print(f"  Merged header cells: {header_range}")
            
            underline_row = header_row + 1
            underline_range = f'A{underline_row}:{chr(64 + total_cols)}{underline_row}'
            sheet.merge_cells(underline_range)
            print(f"  Merged underline cells: {underline_range}")
        
        # Now build formatting requests
        for insurance_type in ["property", "general_liability", "liquor"]:
            if insurance_type not in section_starts:
                print(f"Skipping {insurance_type} - not found in sheet")
                continue
            
            header_row = section_starts[insurance_type]
            end_row = section_ends[insurance_type]
            last_col = total_cols - 1  # 0-indexed for API
            
            print(f"📋 Queuing {insurance_type} section (rows {header_row}-{end_row})")
            
            # Main header (coverage type) - BLACK background with white text
            batch_requests.append({
                'range': f'A{header_row}:{chr(64 + total_cols)}{header_row}',
                'format': {
                    'backgroundColor': {'red': 0.15, 'green': 0.15, 'blue': 0.15},
                    'textFormat': {'bold': True, 'fontSize': 16, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'horizontalAlignment': 'CENTER'
                }
            })
            
            # Underline row
            underline_row = header_row + 1
            batch_requests.append({
                'range': f'A{underline_row}:{chr(64 + total_cols)}{underline_row}',
                'format': {
                    'borders': {'bottom': {'style': 'SOLID', 'width': 3, 'color': {'red': 0.7, 'green': 0.7, 'blue': 0.7}}}
                }
            })
            
            # Column headers (Field Name, LLM Value, Source Page) - Light gray
            col_header_row = header_row + 3
            batch_requests.append({
                'range': f'A{col_header_row}:{chr(64 + total_cols)}{col_header_row}',
                'format': {
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                    'textFormat': {'bold': True, 'fontSize': 12},
                    'borders': {
                        'top': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.7, 'green': 0.7, 'blue': 0.7}},
                        'bottom': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.7, 'green': 0.7, 'blue': 0.7}},
                        'left': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.7, 'green': 0.7, 'blue': 0.7}},
                        'right': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.7, 'green': 0.7, 'blue': 0.7}}
                    },
                    'horizontalAlignment': 'CENTER'
                }
            })
            
            # Data rows - ONLY borders and light gray on Column A (Field Name)
            data_start = col_header_row + 1
            batch_requests.append({
                'range': f'A{data_start}:A{end_row}',
                'format': {
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
                    'borders': {
                        'top': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
                        'bottom': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
                        'left': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
                        'right': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}
                    }
                }
            })
            
            # Data rows in other columns - NO formatting (explicitly white/clean)
            other_cols_range = f'B{data_start}:{chr(64 + total_cols)}{end_row}'
            batch_requests.append({
                'range': other_cols_range,
                'format': {
                    'backgroundColor': {'red': 1, 'green': 1, 'blue': 1}  # White background
                }
            })
        
        # Execute ALL formatting in a single API call
        print(f"🚀 Executing {len(batch_requests)} formatting requests in 1 API call...")
        sheet.batch_format(batch_requests)
        
        print("✅ Applied professional formatting to ALL sections in 1 API call!")
    
    except Exception as e:
        print(f"❌ Error applying formatting: {e}")
        import traceback
        traceback.print_exc()

def push_master_to_sheets(carriers):
    """Push master multi-carrier data to Google Sheets with stacked output"""
    import gspread
    from google.oauth2.service_account import Credentials
    
    print("PHASE 4: MASTER GOOGLE SHEETS INTEGRATION")
    print("=" * 80)
    
    # 1. DYNAMIC PATH DETECTION
    current_dir = os.getcwd()
    if current_dir.endswith('src'):
        results_dir = '../results'
        config_dir = '../config'
    else:
        results_dir = 'results'
        config_dir = 'config'
    
    # 2. LOAD ALL CARRIER DATA FOR PROPERTY AND LIQUOR ONLY
    all_carrier_data = {}
    insurance_types = ["property", "general_liability", "liquor"]
    
    for carrier in carriers:
        carrier_name = carrier['name']
        all_carrier_data[carrier_name] = {}
        
        for insurance_type in insurance_types:
            data_file = f"{results_dir}/{carrier_name}_{insurance_type}_final_validated_fields.json"
            
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    all_carrier_data[carrier_name][insurance_type] = json.load(f)
                print(f"✅ Loaded {insurance_type} data for {carrier_name}: {len(all_carrier_data[carrier_name][insurance_type])} fields")
            else:
                print(f"❌ No {insurance_type} data file found for {carrier_name}: {data_file}")
                all_carrier_data[carrier_name][insurance_type] = {}
    
    # 3. SETUP GOOGLE SHEETS
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
    
    # 4. OPEN SHEET
    try:
        sheet = client.open("Insurance Fields Data").sheet1
        print("✅ Opened sheet: Insurance Fields Data")
    except:
        # If sheet doesn't exist, try to create it
        try:
            spreadsheet = client.create("Insurance Fields Data")
            sheet = spreadsheet.sheet1
            print("✅ Created new sheet: Insurance Fields Data")
        except Exception as e:
            print(f"❌ Could not open or create sheet: {e}")
            return False
    
    # 5. CLEAR EXISTING DATA
    sheet.clear()
    print("✅ Cleared existing data")
    
    # 6. PREPARE STACKED DATA
    all_rows = []
    
    # Add company header as first row
    all_rows.append(["Mckinney & Co. Insurance"])
    
    # Process each insurance type
    for insurance_type in insurance_types:
        coverage_type_names = {
            "property": "Property Coverages",
            "general_liability": "General Liability Coverages",
            "liquor": "Liquor Coverages"
        }
        
        coverage_type = coverage_type_names[insurance_type]
        
        # Add coverage type header
        all_rows.append([coverage_type])
        all_rows.append(["=" * len(coverage_type)])  # Underline
        all_rows.append([])  # Empty row for spacing
        
        # Create field header row
        header = ["Field Name"]
        for carrier in carriers:
            carrier_name = carrier['name']
            header.extend([f"LLM Value ({carrier_name})", f"Source Page ({carrier_name})"])
        all_rows.append(header)
        
        # Get all unique field names from all carriers for this insurance type
        all_fields = set()
        for carrier_name in all_carrier_data:
            if insurance_type in all_carrier_data[carrier_name]:
                all_fields.update(all_carrier_data[carrier_name][insurance_type].keys())
        
        # Get fields in original order from first carrier's data
        sorted_fields = []
        for carrier in carriers:
            carrier_name = carrier['name']
            if carrier_name in all_carrier_data and insurance_type in all_carrier_data[carrier_name]:
                for field_name in all_carrier_data[carrier_name][insurance_type].keys():
                    if field_name not in sorted_fields:
                        sorted_fields.append(field_name)
                break  # Only use first carrier's order
        
        # Create data rows for this insurance type
        for field_name in sorted_fields:
            row = [field_name]
            
            for carrier in carriers:
                carrier_name = carrier['name']
                if (carrier_name in all_carrier_data and 
                    insurance_type in all_carrier_data[carrier_name] and 
                    field_name in all_carrier_data[carrier_name][insurance_type]):
                    
                    field_data = all_carrier_data[carrier_name][insurance_type][field_name]
                    row.extend([
                        field_data.get('value', ''),
                        field_data.get('source_page', '')
                    ])
                else:
                    row.extend(['', ''])  # Empty values for missing fields
            
            all_rows.append(row)
        
        # Add spacing between insurance types
        all_rows.append([])  # Empty row
        all_rows.append([])  # Another empty row
    
    # 7. PUSH ALL DATA IN ONE BATCH
    try:
        sheet.update('A1', all_rows)  # Don't store the response!
        print(f"✅ Pushed {len(all_rows)} rows to Google Sheets!")
        print(f"✅ Insurance Types: {len(insurance_types)}")
        print(f"✅ Carriers: {len(carriers)}")

        # 8. APPLY PROFESSIONAL FORMATTING
        apply_sheets_formatting(sheet, len(all_rows), len(header), insurance_types, carriers)

        print("\n" + "=" * 80)
        print("MASTER GOOGLE SHEETS INTEGRATION COMPLETE!")
        print("=" * 80)
        print("Check your Google Sheet: Insurance Fields Data")
        print("Format: Stacked sections for Property, General Liability, and Liquor")

        return True
    except Exception as e:
        print(f"❌ Error pushing to Google Sheets: {e}")
        return False

def rename_files_with_carrier_prefix(carrier_name, insurance_type, phase_type):
    """Rename existing files with carrier and insurance type prefix"""
    # DYNAMIC PATH DETECTION
    results_paths = [
        'results',  # When run from property/ (via mine.py)
        '../results'  # When run from property/src/ (alone)
    ]
    
    results_dir = None
    for path in results_paths:
        if os.path.exists(path) or os.path.exists(os.path.dirname(path) if os.path.dirname(path) else '.'):
            results_dir = path
            break
    
    if not results_dir:
        results_dir = 'results'  # Default fallback
    
    # List of files to rename based on phase
    if phase_type == "phase1":
        files_to_rename = [
            'clean_pages_results.txt',
            'problem_pages_list.txt', 
            'phase1_report.txt',
            'all_pages_results.txt',
            'pymupdf_clean_pages_only.txt'
        ]
    elif phase_type == "phase2":
        files_to_rename = [
            'ocr_all_pages_results.txt',
            'ocr_processing_log.txt'
        ]
    elif phase_type == "phase2c":
        files_to_rename = [
            'smart_selection_results.txt',
            'phase2c_report.txt'
        ]
    elif phase_type == "phase2d":
        files_to_rename = [
            'intelligent_combined_text.txt',
            'phase2d_report.txt'
        ]
    else:
        files_to_rename = []
    
    for filename in files_to_rename:
        old_path = f"{results_dir}/{filename}"
        new_path = f"{results_dir}/{carrier_name}_{insurance_type}_{filename}"
        
        if os.path.exists(old_path):
            # Remove target file if it exists
            if os.path.exists(new_path):
                os.remove(new_path)
            # Rename the file
            os.rename(old_path, new_path)
            print(f"  Renamed: {filename} -> {carrier_name}_{insurance_type}_{filename}")

def main():
    """Main function"""
    print("MASTER MULTI-CARRIER INSURANCE EXTRACTION PIPELINE")
    print("=" * 80)
    
    carriers = get_carrier_setup()
    
    print("\n" + "=" * 80)
    print("SETUP COMPLETE!")
    print("=" * 80)
    print(f"Total carriers: {len(carriers)}")
    
    for carrier in carriers:
        print(f"\n{carrier['name']}:")
        print(f"  Property PDF: {carrier['property']['pdf_file']}")
        print(f"  General Liability PDF: {carrier['general_liability']['pdf_file']}")
        print(f"  Liquor PDF: {carrier['liquor']['pdf_file']}")
    
    print("=" * 80)
    
    # Process each carrier's PDFs for all insurance types
    print("\n" + "=" * 80)
    print("STARTING MASTER PROCESSING - ALL INSURANCE TYPES")
    print("=" * 80)
    
    all_results = {}
    insurance_types = ["property", "general_liability", "liquor"]
    
    for carrier in carriers:
        carrier_name = carrier['name']
        all_results[carrier_name] = {}
        
        for insurance_type in insurance_types:
            pdf_info = carrier[insurance_type]
            result = process_carrier_insurance_type(carrier, insurance_type, pdf_info)
            all_results[carrier_name][insurance_type] = result
    
    # Final summary
    print("\n" + "=" * 80)
    print("ALL CARRIERS AND INSURANCE TYPES PROCESSED!")
    print("=" * 80)
    for carrier_name, carrier_results in all_results.items():
        print(f"\n{carrier_name}:")
        for insurance_type, result in carrier_results.items():
            if result:
                phase1_pages = len(result['phase1']['clean_pages']) if result['phase1'] else 0
                phase2_pages = len(result['phase2']['successful_pages']) if result['phase2'] else 0
                phase2c_pages = len(result['phase2c']) if result['phase2c'] else 0
                phase2d_success = "✅" if result['phase2d'] else "❌"
                phase3_fields = len(result['phase3']) if result['phase3'] else 0
                print(f"  ✅ {insurance_type}: Phase1({phase1_pages} clean), Phase2({phase2_pages} OCR), Phase2C({phase2c_pages} decisions), Phase2D({phase2d_success}), Phase3({phase3_fields} fields)")
            else:
                print(f"  ❌ {insurance_type}: FAILED")
    
    print("=" * 80)
    
    # PHASE 4: MASTER GOOGLE SHEETS INTEGRATION
    print("\n" + "=" * 80)
    print("STARTING PHASE 4: MASTER GOOGLE SHEETS INTEGRATION")
    print("=" * 80)
    
    sheets_success = push_master_to_sheets(carriers)
    if sheets_success:
        print("✅ PHASE 4 COMPLETE: Master data pushed to Google Sheets!")
        print("📊 Check your Google Sheet: Insurance Fields Data")
        print("📋 Format: Stacked sections for Property, General Liability, and Liquor")
    else:
        print("❌ PHASE 4 FAILED: Master Google Sheets integration failed")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
