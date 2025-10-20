#!/usr/bin/env python3
"""
PHASE 2C: SMART LLM SELECTION
================================================================================
This script uses GPT-3.5 to intelligently select the best text source for each page
by comparing PyMuPDF clean pages vs OCR all pages results.

Strategy:
- PyMuPDF: Only clean pages (high quality)
- OCR: All pages (comprehensive coverage)
- LLM: Decides best source per page
"""

import openai
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../config/.env')

def read_pymupdf_clean_pages():
    """Read PyMuPDF clean pages only"""
    # DYNAMIC PATH DETECTION
    clean_paths = [
        'results/pymupdf_clean_pages_only.txt',  # When run from property/ (via mine.py)
        '../results/pymupdf_clean_pages_only.txt'  # When run from property/src/ (alone)
    ]
    
    clean_file = None
    for path in clean_paths:
        if os.path.exists(path):
            clean_file = path
            break
    
    if not clean_file:
        print("Error: PyMuPDF clean pages file not found!")
        print("Please run Phase 1 first.")
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

def read_ocr_all_pages():
    """Read OCR all pages results"""
    # DYNAMIC PATH DETECTION
    ocr_paths = [
        'results/ocr_all_pages_results.txt',  # When run from property/ (via mine.py)
        '../results/ocr_all_pages_results.txt'  # When run from property/src/ (alone)
    ]
    
    ocr_file = None
    for path in ocr_paths:
        if os.path.exists(path):
            ocr_file = path
            break
    
    if not ocr_file:
        print("Error: OCR results file not found!")
        print("Please run Phase 2 first.")
        return {}
    
    print(f"Reading OCR all pages from: {ocr_file}")
    
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

def get_all_page_numbers(pymupdf_pages, ocr_pages):
    """Get all unique page numbers from both sources"""
    all_pages = set(pymupdf_pages.keys()) | set(ocr_pages.keys())
    return sorted(list(all_pages))

def create_selection_prompt(page_num, pymupdf_text, ocr_text):
    """Create prompt for LLM to select best text source"""
    
    # Truncate texts to focus on key information (first 3000 chars)
    pymupdf_preview = pymupdf_text[:3000] if pymupdf_text else "NOT AVAILABLE"
    ocr_preview = ocr_text[:3000] if ocr_text else "NOT AVAILABLE"
    
    # Add truncation notice if text was cut
    pymupdf_notice = "\n[... text truncated for analysis ...]" if len(pymupdf_text) > 3000 else ""
    ocr_notice = "\n[... text truncated for analysis ...]" if len(ocr_text) > 3000 else ""
    
    prompt = f"""
You are a text quality analyzer for insurance documents. Compare two text extractions for Page {page_num} and decide which one is better.

CRITICAL INSURANCE DOCUMENT CRITERIA:
1. DATA COMPLETENESS - Which text contains actual data values vs blank fields?
2. DATA CORRECTNESS - Which text has accurate data without OCR errors?
3. READABILITY - Which text is more readable and coherent?

IMPORTANT: For insurance documents, DATA COMPLETENESS AND CORRECTNESS are the most critical factors. 
- A form with blank fields (like "Account No. ______________________") is WORSE than a form with actual data values
- A form with incorrect OCR data (like "Account No. 8l7553.l" instead of "817553.1") is WORSE than a form with correct data
- Choose the source that provides the most complete AND accurate data

PYMUPDF EXTRACTION (Page {page_num}):
{pymupdf_preview}{pymupdf_notice}

OCR EXTRACTION (Page {page_num}):
{ocr_preview}{ocr_notice}

SELECTION RULES:
- If PyMuPDF text is NOT AVAILABLE, choose OCR
- If OCR text is NOT AVAILABLE, choose PyMuPDF  
- If PyMuPDF has blank fields (like "______________________") and OCR has actual data, choose OCR
- If OCR has obvious errors and PyMuPDF has correct data, choose PyMuPDF
- If both have data, choose the more complete AND accurate one

SPECIFIC RED FLAGS TO AVOID:
- Blank account numbers, policy numbers, or dollar amounts
- Forms with empty fields where data should be
- OCR character recognition errors (0/O, 1/I, 6/G, 8/B, etc.)

Return ONLY a JSON response with this exact format:
{{
    "page": {page_num},
    "selected_source": "PyMuPDF" or "OCR",
    "reason": "Brief explanation focusing on data completeness and correctness",
    "confidence": "high" or "medium" or "low"
}}

Do not provide any other text, only the JSON response.
"""
    
    return prompt

def select_best_source_with_llm(page_num, pymupdf_text, ocr_text):
    """Use GPT-3.5 to select best text source for a page"""
    
    prompt = create_selection_prompt(page_num, pymupdf_text, ocr_text)
    
    try:
        print(f"  Analyzing Page {page_num} with GPT-3.5...")
        
        # Use OpenAI API
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a text quality analyzer specializing in insurance documents. Your primary focus is DATA COMPLETENESS AND CORRECTNESS - actual data values that are accurate are more important than clean formatting. Watch for OCR character recognition errors. Return ONLY valid JSON responses."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON response
        try:
            result_json = json.loads(result_text)
            return result_json
        except json.JSONDecodeError as e:
            print(f"  [ERROR] Failed to parse JSON response: {e}")
            print(f"  Raw response: {result_text[:100]}...")
            return None
            
    except Exception as e:
        print(f"  [ERROR] LLM processing failed: {e}")
        return None

def process_all_pages_selection(pymupdf_pages, ocr_pages):
    """Process all pages for smart selection"""
    print("PHASE 2C: SMART LLM SELECTION")
    print("=" * 80)
    
    all_pages = get_all_page_numbers(pymupdf_pages, ocr_pages)
    print(f"Processing {len(all_pages)} pages for smart selection")
    print("=" * 80)
    
    selection_results = {}
    
    for page_num in all_pages:
        print(f"\nProcessing Page {page_num}...")
        
        # Get texts from both sources
        pymupdf_text = pymupdf_pages.get(page_num, {}).get('text', '')
        ocr_text = ocr_pages.get(page_num, {}).get('text', '')
        
        # Use LLM to select best source
        selection = select_best_source_with_llm(page_num, pymupdf_text, ocr_text)
        
        if selection:
            selection_results[page_num] = selection
            print(f"  [SUCCESS] Selected {selection['selected_source']} - {selection['reason']}")
        else:
            # Fallback: choose PyMuPDF if available, otherwise OCR
            if pymupdf_text:
                selection_results[page_num] = {
                    "page": page_num,
                    "selected_source": "PyMuPDF",
                    "reason": "Fallback: PyMuPDF available",
                    "confidence": "low"
                }
                print(f"  [FALLBACK] Selected PyMuPDF (fallback)")
            elif ocr_text:
                selection_results[page_num] = {
                    "page": page_num,
                    "selected_source": "OCR",
                    "reason": "Fallback: Only OCR available",
                    "confidence": "low"
                }
                print(f"  [FALLBACK] Selected OCR (fallback)")
            else:
                print(f"  [ERROR] No text available for Page {page_num}")
    
    return selection_results

def save_selection_results(selection_results):
    """Save smart selection results"""
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
    
    # Save selection decisions
    selection_file = f"{results_dir}/smart_selection_results.json"
    with open(selection_file, 'w', encoding='utf-8') as f:
        json.dump(selection_results, f, indent=2, ensure_ascii=False)
    
    # Save summary report
    report_file = f"{results_dir}/smart_selection_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("SMART SELECTION REPORT - PHASE 2C\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Pages Processed: {len(selection_results)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Count selections by source
        pymupdf_count = len([s for s in selection_results.values() if s['selected_source'] == 'PyMuPDF'])
        ocr_count = len([s for s in selection_results.values() if s['selected_source'] == 'OCR'])
        
        f.write("SELECTION SUMMARY:\n")
        f.write("-" * 30 + "\n")
        f.write(f"PyMuPDF selected: {pymupdf_count} pages\n")
        f.write(f"OCR selected: {ocr_count} pages\n")
        f.write(f"Total pages: {len(selection_results)} pages\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("DETAILED SELECTIONS:\n")
        f.write("-" * 30 + "\n")
        for page_num in sorted(selection_results.keys(), key=int):
            selection = selection_results[page_num]
            f.write(f"Page {int(page_num):2d}: {selection['selected_source']:8s} - {selection['reason']} (confidence: {selection['confidence']})\n")
    
    return selection_file, report_file

def generate_summary(selection_results):
    """Generate console summary"""
    print(f"\n{'='*80}")
    print("PHASE 2C SUMMARY - SMART SELECTION")
    print(f"{'='*80}")
    
    pymupdf_count = len([s for s in selection_results.values() if s['selected_source'] == 'PyMuPDF'])
    ocr_count = len([s for s in selection_results.values() if s['selected_source'] == 'OCR'])
    
    print(f"Total Pages Processed: {len(selection_results)}")
    print(f"PyMuPDF Selected: {pymupdf_count}")
    print(f"OCR Selected: {ocr_count}")
    
    print(f"\n[SUCCESS] Smart selection completed!")
    print(f"PyMuPDF pages: {[p for p, s in selection_results.items() if s['selected_source'] == 'PyMuPDF']}")
    print(f"OCR pages: {[p for p, s in selection_results.items() if s['selected_source'] == 'OCR']}")

if __name__ == "__main__":
    # Set OpenAI API key
    # Set OpenAI API key from environment
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai.api_key:
        print("Error: OPENAI_API_KEY not found in environment variables!")
        print("Please set your API key in the .env file")
        exit(1)
    
    print("PHASE 2C: SMART LLM SELECTION")
    print("=" * 80)
    
    # Read both sources
    pymupdf_pages = read_pymupdf_clean_pages()
    ocr_pages = read_ocr_all_pages()
    
    if not pymupdf_pages and not ocr_pages:
        print("Error: No pages found from either source!")
        exit(1)
    
    # Process smart selection
    selection_results = process_all_pages_selection(pymupdf_pages, ocr_pages)
    
    # Save results
    selection_file, report_file = save_selection_results(selection_results)
    
    # Generate summary
    generate_summary(selection_results)
    
    print(f"\n{'='*80}")
    print("FILES GENERATED:")
    print(f"{'='*80}")
    print(f"Selection results: {selection_file}")
    print(f"Selection report: {report_file}")
    print(f"\nPhase 2C complete! Ready for Phase 2D (Intelligent Combining).")
