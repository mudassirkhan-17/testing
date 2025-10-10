import fitz
import pytesseract
import os
import json
import re
from datetime import datetime
from PIL import Image
import io

def get_all_pages_from_phase1():
    """Get all pages from Phase 1 results for OCR processing"""
    # Read the all pages report to get total page count
    report_file = "phase1_report.txt"
    
    if not os.path.exists(report_file):
        print("Error: No Phase 1 report found!")
        print("Please run Phase 1 first to generate report.")
        return []
    
    print(f"Reading total pages from: {report_file}")
    
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Extract total pages processed
        total_match = re.search(r'Total Pages Processed: (\d+)', content)
        if total_match:
            total_pages = int(total_match.group(1))
            all_pages = list(range(1, total_pages + 1))
            print(f"Found {total_pages} total pages to OCR: {all_pages}")
            return all_pages
        else:
            print("Error: Could not find total pages count in report")
            return []

def extract_with_tesseract_ocr(pdf_file, page_num):
    """Extract text using Tesseract OCR (in-memory image conversion)"""
    try:
        print(f"  Converting page {page_num} to image...")
        
        # Open PDF and get page
        doc = fitz.open(pdf_file)
        page = doc[page_num - 1]  # PyMuPDF uses 0-based indexing
        
        # Convert page to image (2.0x zoom for better table detection)
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # Create PIL Image from bytes
        image = Image.open(io.BytesIO(img_data))
        
        print(f"  Running Tesseract OCR on page {page_num}...")
        
        # Try multiple OCR configurations with fallback
        configs = [
            '--oem 3 --psm 6',           # Best for tables
            '--oem 3 --psm 3',           # Fallback for mixed content
            ''                           # Basic fallback
        ]
        
        page_text = ""
        ocr_success = False
        
        for i, config in enumerate(configs):
            try:
                if config:
                    print(f"    Trying OCR config {i+1}: {config}")
                    page_text = pytesseract.image_to_string(image, config=config)
                else:
                    print(f"    Trying basic OCR (fallback)")
                    page_text = pytesseract.image_to_string(image)
                
                # Check if we got meaningful text
                if len(page_text.strip()) > 50:
                    ocr_success = True
                    print(f"    [SUCCESS] OCR successful with config {i+1}")
                    break
                else:
                    print(f"    [FAILED] Config {i+1} produced insufficient text")
                    
            except Exception as e:
                print(f"    [ERROR] Config {i+1} failed: {e}")
                continue
        
        if not ocr_success:
            print(f"    [FAILED] All OCR configurations failed")
            page_text = ""
        
        doc.close()
        
        # Analyze OCR quality
        metrics = analyze_ocr_quality(page_text)
        
        return {
            'text': page_text,
            'metrics': metrics,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"  [ERROR] OCR failed on page {page_num}: {e}")
        return {
            'text': '',
            'metrics': {'total_chars': 0, 'readable_words': 0, 'confidence_score': 0},
            'success': False,
            'error': str(e)
        }

def analyze_ocr_quality(text):
    """Analyze OCR text quality"""
    metrics = {
        'total_chars': len(text),
        'readable_words': len([word for word in text.split() if len(word) > 2 and word.isalpha()]),
        'lines': len([line for line in text.split('\n') if line.strip()]),
        'confidence_score': 0
    }
    
    # Calculate confidence score
    confidence = 100
    
    # Penalty for very short text
    if metrics['total_chars'] < 100:
        confidence -= 30
    elif metrics['total_chars'] < 500:
        confidence -= 15
    
    # Penalty for very few readable words
    if metrics['readable_words'] < 20:
        confidence -= 40
    elif metrics['readable_words'] < 50:
        confidence -= 20
    
    # Bonus for good text length
    if metrics['total_chars'] > 1000:
        confidence += 10
    if metrics['readable_words'] > 100:
        confidence += 10
    
    metrics['confidence_score'] = max(confidence, 0)
    
    return metrics

def process_all_pages_with_ocr(pdf_file, all_pages):
    """Process ALL pages with OCR for smart selection"""
    print("PHASE 2: OCR EXTRACTION - ALL PAGES")
    print("=" * 80)
    print(f"Processing {len(all_pages)} ALL pages with Tesseract OCR")
    print(f"PDF File: {pdf_file}")
    print("=" * 80)
    
    results = {
        'successful_pages': [],
        'failed_pages': [],
        'all_results': {}
    }
    
    for page_num in all_pages:
        print(f"\nProcessing Page {page_num}...")
        
        # Extract text with OCR
        ocr_result = extract_with_tesseract_ocr(pdf_file, page_num)
        
        # Store results
        results['all_results'][page_num] = ocr_result
        
        if ocr_result['success']:
            results['successful_pages'].append({
                'page_num': page_num,
                'text': ocr_result['text'],
                'metrics': ocr_result['metrics']
            })
            
            metrics = ocr_result['metrics']
            print(f"  [SUCCESS] - {metrics['total_chars']} chars, {metrics['readable_words']} words, {metrics['confidence_score']:.1f}% confidence")
        else:
            results['failed_pages'].append({
                'page_num': page_num,
                'error': ocr_result['error']
            })
            print(f"  [FAILED] - {ocr_result['error']}")
    
    return results

def save_ocr_results(results):
    """Save OCR results to files"""
    # Save all OCR results in ONE single file
    ocr_file = "ocr_all_pages_results.txt"  # Single file for all pages
    
    with open(ocr_file, 'w', encoding='utf-8') as f:
        f.write("OCR EXTRACTION RESULTS - ALL PAGES\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Method: Tesseract OCR (2.0x zoom) with fallback configs\n")
        f.write(f"Total Pages Processed: {len(results['successful_pages'])}\n")
        f.write("=" * 80 + "\n\n")
        
        for page_result in results['successful_pages']:
            page_num = page_result['page_num']
            f.write(f"PAGE {page_num}:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Characters: {page_result['metrics']['total_chars']}\n")
            f.write(f"Readable Words: {page_result['metrics']['readable_words']}\n")
            f.write(f"Lines: {page_result['metrics']['lines']}\n")
            f.write(f"Confidence Score: {page_result['metrics']['confidence_score']:.1f}%\n")
            f.write("\nOCR EXTRACTED TEXT:\n")
            f.write("-" * 40 + "\n")
            f.write(page_result['text'])
            f.write("\n" + "=" * 80 + "\n\n")
    
    print(f"  Saved ALL OCR results: {ocr_file}")
    ocr_files = [ocr_file]
    
    # Save processing log
    log_file = f"ocr_processing_log.txt"  # Fixed filename - overwrites existing
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("OCR PROCESSING LOG - PHASE 2 (ALL PAGES)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Pages Processed: {len(results['all_results'])}\n")
        f.write(f"Successful Pages: {len(results['successful_pages'])}\n")
        f.write(f"Failed Pages: {len(results['failed_pages'])}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SUCCESSFUL PAGES:\n")
        f.write("-" * 30 + "\n")
        for page_result in results['successful_pages']:
            metrics = page_result['metrics']
            f.write(f"Page {page_result['page_num']:2d}: {metrics['total_chars']:4d} chars | "
                   f"{metrics['readable_words']:3d} words | "
                   f"{metrics['confidence_score']:5.1f}% confidence\n")
        
        if results['failed_pages']:
            f.write("\nFAILED PAGES:\n")
            f.write("-" * 20 + "\n")
            for page_result in results['failed_pages']:
                f.write(f"Page {page_result['page_num']:2d}: {page_result['error']}\n")
        
        f.write(f"\nSUMMARY:\n")
        f.write("-" * 20 + "\n")
        f.write(f"OCR Success Rate: {len(results['successful_pages'])}/{len(results['all_results'])} "
               f"({len(results['successful_pages'])/len(results['all_results'])*100:.1f}%)\n")
        
        if results['successful_pages']:
            avg_chars = sum(p['metrics']['total_chars'] for p in results['successful_pages']) / len(results['successful_pages'])
            avg_words = sum(p['metrics']['readable_words'] for p in results['successful_pages']) / len(results['successful_pages'])
            avg_confidence = sum(p['metrics']['confidence_score'] for p in results['successful_pages']) / len(results['successful_pages'])
            
            f.write(f"Average Characters: {avg_chars:.0f}\n")
            f.write(f"Average Words: {avg_words:.0f}\n")
            f.write(f"Average Confidence: {avg_confidence:.1f}%\n")
    
    return ocr_files, log_file

def generate_summary(results):
    """Generate console summary"""
    print(f"\n{'='*80}")
    print("PHASE 2 SUMMARY - OCR EXTRACTION (ALL PAGES)")
    print(f"{'='*80}")
    print(f"Total Pages Processed: {len(results['all_results'])}")
    print(f"Successful OCR: {len(results['successful_pages'])}")
    print(f"Failed OCR: {len(results['failed_pages'])}")
    
    if results['successful_pages']:
        success_rate = len(results['successful_pages']) / len(results['all_results']) * 100
        print(f"OCR Success Rate: {success_rate:.1f}%")
        
        successful_nums = [p['page_num'] for p in results['successful_pages']]
        print(f"\n[SUCCESS] Successfully processed pages: {successful_nums}")
        
        # Show quality metrics
        total_chars = sum(p['metrics']['total_chars'] for p in results['successful_pages'])
        total_words = sum(p['metrics']['readable_words'] for p in results['successful_pages'])
        avg_confidence = sum(p['metrics']['confidence_score'] for p in results['successful_pages']) / len(results['successful_pages'])
        
        print(f"\nOCR Quality Metrics:")
        print(f"  Total Characters Extracted: {total_chars:,}")
        print(f"  Total Readable Words: {total_words:,}")
        print(f"  Average Confidence: {avg_confidence:.1f}%")
    
    if results['failed_pages']:
        failed_nums = [p['page_num'] for p in results['failed_pages']]
        print(f"\n[FAILED] Failed pages: {failed_nums}")
    
    print(f"\nNext step: Run Phase 2C (Smart LLM Selection)")

if __name__ == "__main__":
    pdf_file = "pdf/PROPERTY QUOTE.pdf"
    
    # Check if PDF exists
    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found!")
        print("Please ensure the PDF file is in the pdf/ subdirectory.")
        exit(1)
    
    # Get all pages from Phase 1
    all_pages = get_all_pages_from_phase1()
    
    if not all_pages:
        print("No pages found. Phase 1 may not have completed successfully.")
        exit(1)
    
    # Process ALL pages with OCR
    results = process_all_pages_with_ocr(pdf_file, all_pages)
    
    # Save results
    ocr_files, log_file = save_ocr_results(results)
    
    # Generate summary
    generate_summary(results)
    
    print(f"\n{'='*80}")
    print("FILES GENERATED:")
    print(f"{'='*80}")
    for ocr_file in ocr_files:
        print(f"OCR results: {ocr_file}")
    print(f"Processing log: {log_file}")
    print(f"\nPhase 2 complete! OCR extraction finished for all pages.")
    print(f"Ready for Phase 2C (Smart LLM Selection).")
