import os
import re
from datetime import datetime

def read_all_results():
    """Read both PyMuPDF (clean pages) and OCR (problem pages) results"""
    all_pages_text = []
    
    # Read PyMuPDF clean pages results
    clean_file = "clean_pages_results.txt"
    if os.path.exists(clean_file):
        print(f"Reading PyMuPDF clean pages from: {clean_file}")
        with open(clean_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract PyMuPDF text content
        page_sections = re.findall(r'PAGE (\d+):.*?TEXT CONTENT:\n(.*?)\n={80}', content, re.DOTALL)
        
        for page_num, page_text in page_sections:
            all_pages_text.append({
                'page_num': int(page_num),
                'text': page_text.strip(),
                'source': 'PyMuPDF'
            })
        
        print(f"  Extracted {len(page_sections)} clean pages from PyMuPDF")
    else:
        print("Warning: Clean pages file not found!")
    
    # Read OCR problem pages results
    ocr_file = "ocr_all_pages_results.txt"
    if os.path.exists(ocr_file):
        print(f"Reading OCR problem pages from: {ocr_file}")
        with open(ocr_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract OCR text content
        page_sections = re.findall(r'PAGE (\d+):.*?OCR EXTRACTED TEXT:.*?----------------------------------------\n(.*?)\n={80}', content, re.DOTALL)
        
        for page_num, page_text in page_sections:
            all_pages_text.append({
                'page_num': int(page_num),
                'text': page_text.strip(),
                'source': 'OCR'
            })
        
        print(f"  Extracted {len(page_sections)} problem pages from OCR")
    else:
        print("Error: OCR results file not found!")
        print("Please run Phase 2A first to generate OCR results.")
        return []
    
    # Sort pages by page number
    all_pages_text.sort(key=lambda x: x['page_num'])
    
    print(f"\nCombined text from {len(all_pages_text)} total pages")
    
    return all_pages_text

def create_combined_file(all_pages):
    """Create a combined file with all extracted text"""
    combined_file = "combined_all_pages.txt"  # Fixed filename for LLM script
    
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write("COMBINED PDF EXTRACTION RESULTS - ALL PAGES\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Pages: {len(all_pages)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Count pages by source
        pymupdf_pages = [p for p in all_pages if p['source'] == 'PyMuPDF']
        ocr_pages = [p for p in all_pages if p['source'] == 'OCR']
        
        f.write("EXTRACTION SUMMARY:\n")
        f.write("-" * 30 + "\n")
        f.write(f"PyMuPDF (Clean Pages): {len(pymupdf_pages)} pages\n")
        f.write(f"OCR (Problem Pages): {len(ocr_pages)} pages\n")
        f.write(f"Total Pages: {len(all_pages)} pages\n")
        f.write("=" * 80 + "\n\n")
        
        # Write each page
        for page in all_pages:
            f.write(f"PAGE {page['page_num']} ({page['source']}):\n")
            f.write("-" * 50 + "\n")
            f.write(f"Source: {page['source']}\n")
            f.write(f"Characters: {len(page['text']):,}\n")
            f.write(f"Lines: {len([line for line in page['text'].split(chr(10)) if line.strip()])}\n")
            f.write("\nTEXT CONTENT:\n")
            f.write("-" * 30 + "\n")
            f.write(page['text'])
            f.write("\n" + "=" * 80 + "\n\n")
    
    return combined_file

def generate_summary(all_pages):
    """Generate console summary"""
    print(f"\n{'='*80}")
    print("COMBINED EXTRACTION SUMMARY")
    print(f"{'='*80}")
    
    pymupdf_pages = [p for p in all_pages if p['source'] == 'PyMuPDF']
    ocr_pages = [p for p in all_pages if p['source'] == 'OCR']
    
    print(f"Total Pages: {len(all_pages)}")
    print(f"PyMuPDF Pages: {len(pymupdf_pages)}")
    print(f"OCR Pages: {len(ocr_pages)}")
    
    if pymupdf_pages:
        pymupdf_nums = [p['page_num'] for p in pymupdf_pages]
        print(f"\n[SUCCESS] PyMuPDF (Clean) Pages: {pymupdf_nums}")
    
    if ocr_pages:
        ocr_nums = [p['page_num'] for p in ocr_pages]
        print(f"[SUCCESS] OCR (Problem) Pages: {ocr_nums}")
    
    # Calculate total characters
    total_chars = sum(len(p['text']) for p in all_pages)
    pymupdf_chars = sum(len(p['text']) for p in pymupdf_pages)
    ocr_chars = sum(len(p['text']) for p in ocr_pages)
    
    print(f"\nTEXT STATISTICS:")
    print(f"  Total Characters: {total_chars:,}")
    print(f"  PyMuPDF Characters: {pymupdf_chars:,}")
    print(f"  OCR Characters: {ocr_chars:,}")
    
    # Show page details
    print(f"\nPAGE DETAILS:")
    for page in all_pages:
        chars = len(page['text'])
        lines = len([line for line in page['text'].split(chr(10)) if line.strip()])
        print(f"  Page {page['page_num']:2d} ({page['source']:8s}): {chars:5,} chars, {lines:3d} lines")

if __name__ == "__main__":
    print("STEP 1: COMBINING ALL EXTRACTION RESULTS")
    print("=" * 80)
    
    # Read all results
    all_pages = read_all_results()
    if not all_pages:
        print("No pages found to combine!")
        exit(1)
    
    # Create combined file
    combined_file = create_combined_file(all_pages)
    
    # Generate summary
    generate_summary(all_pages)
    
    print(f"\n{'='*80}")
    print("FILE GENERATED:")
    print(f"{'='*80}")
    print(f"Combined file: {combined_file}")
    print(f"\nThis file contains ALL extracted text from both PyMuPDF and OCR.")
    print(f"Ready for Step 2: LLM processing in 3-page chunks.")
