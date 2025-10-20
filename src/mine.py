#!/usr/bin/env python3
"""
MINE.PY - INTELLIGENT PDF PROCESSING PIPELINE
================================================================================
Complete PDF processing pipeline with direct function calls for maximum reliability.
Processes insurance quotes from PDF to Google Sheets automatically.

Features:
- Smart text extraction (PyMuPDF + OCR)
- LLM-powered page selection
- Intelligent text combining
- GPT-5 field extraction
- Automatic Google Sheets integration

Usage: python mine.py
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Import all phase functions
from pdf_input_selector import get_available_pdfs, display_pdf_selection, get_user_selection
from A_phase1_Pymupdf import process_all_pages, save_results, generate_summary as generate_phase1_summary
from A_phase2_ocr import process_all_pages_with_ocr, save_ocr_results, generate_summary as generate_phase2_summary
from A_phase2_ocr import get_all_pages_from_phase1
from A_phase2c_smart_selection import process_all_pages_selection, save_selection_results, generate_summary as generate_phase2c_summary
from A_phase2c_smart_selection import read_pymupdf_clean_pages as read_pymupdf_clean_pages_2c, read_ocr_all_pages as read_ocr_all_pages_2c
from A_phase2d_intelligent_combining import create_intelligent_combined_file, read_smart_selection_results, read_pymupdf_clean_pages as read_pymupdf_clean_pages_2d, read_ocr_all_pages as read_ocr_all_pages_2d, generate_selection_summary
from A_phase3_llm_extraction import read_combined_file, create_chunks, extract_with_llm, merge_extraction_results, save_extraction_results, generate_summary as generate_phase3_summary
from A_phase5_simple_sheets import push_to_sheets

class Config:
    """Configuration management"""
    def __init__(self):
        self.chunk_size = 4
        self.max_retries = 3
        self.api_timeout = 30
        self.enable_vlm = False
        self.enable_debug = False

class ProgressTracker:
    """Progress tracking and timing"""
    def __init__(self, total_phases):
        self.start_time = time.time()
        self.total_phases = total_phases
        self.current_phase = 0
    
    def start_phase(self, phase_name):
        self.phase_start = time.time()
        print(f"\nStarting {phase_name}...")
    
    def end_phase(self, phase_name):
        elapsed = time.time() - self.phase_start
        total_elapsed = time.time() - self.start_time
        self.current_phase += 1
        
        print(f"{phase_name} completed in {elapsed:.1f}s")
        print(f"Progress: {self.current_phase}/{self.total_phases} phases")
        
        if self.current_phase < self.total_phases:
            remaining = self.total_phases - self.current_phase
            avg_time = total_elapsed / self.current_phase
            eta = remaining * avg_time
            print(f"Estimated time remaining: {eta:.1f}s")

def setup_environment():
    """Setup environment and prerequisites"""
    print("Setting up environment...")
    
    # Try multiple paths for .env file
    env_paths = [
        'config/.env',
        '../config/.env', 
        'property/config/.env'
    ]
    
    api_key = None
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                print(f"API key loaded from: {env_path}")
                break
    
    if not api_key:
        raise Exception("OPENAI_API_KEY not found! Please check your .env file")
    
    print("Environment setup complete")

def update_pdf_paths_in_scripts(selected_pdf):
    """Update PDF paths in all phase scripts"""
    print(f"Updating PDF paths to: {selected_pdf}")
    
    # List of phase scripts to update
    phase_scripts = [
        'A_phase1_Pymupdf.py',
        'A_phase2_ocr.py', 
        'A_phase3_llm_extraction.py'
    ]
    
    for script in phase_scripts:
        script_path = script
        if os.path.exists(script_path):
            # Read current content
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update PDF paths
            updated_content = content
            
            # Update different path patterns
            if 'pdf_file = "pdf/PROPERTY QUOTE.pdf"' in content:
                updated_content = updated_content.replace(
                    'pdf_file = "pdf/PROPERTY QUOTE.pdf"',
                    f'pdf_file = "pdf/{selected_pdf}"'
                )
            elif 'pdf_file = "../pdf/PROPERTY QUOTE.pdf"' in content:
                updated_content = updated_content.replace(
                    'pdf_file = "../pdf/PROPERTY QUOTE.pdf"',
                    f'pdf_file = "../pdf/{selected_pdf}"'
                )
            
            # Write updated content
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"  Updated {script}")

def select_pdf():
    """Handle PDF selection"""
    print("\nPDF Selection")
    print("=" * 50)
    
    pdf_files = get_available_pdfs()
    if not pdf_files:
        raise Exception("No PDF files found!")
    
    display_pdf_selection(pdf_files)
    selected_pdf = get_user_selection(pdf_files)
    
    print(f"Selected: {selected_pdf}")
    
    # Update PDF paths in all phase scripts
    update_pdf_paths_in_scripts(selected_pdf)
    
    return selected_pdf

def run_phase_with_retry(phase_func, phase_name, max_retries=3):
    """Run phase with automatic retry"""
    for attempt in range(max_retries):
        try:
            return phase_func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"{phase_name} failed, retrying... (Attempt {attempt + 1})")
            time.sleep(2)

def run_phase1_pymupdf(pdf_file, tracker):
    """Run Phase 1: PyMuPDF extraction"""
    tracker.start_phase("Phase 1: PyMuPDF Extraction")
    
    def phase1_func():
        phase1_results = process_all_pages(pdf_file)
        save_results(phase1_results)
        generate_phase1_summary(phase1_results)
        return phase1_results
    
    result = run_phase_with_retry(phase1_func, "Phase 1")
    tracker.end_phase("Phase 1")
    return result

def run_phase2_ocr(pdf_file, tracker):
    """Run Phase 2: OCR processing"""
    tracker.start_phase("Phase 2: OCR Processing")
    
    def phase2_func():
        all_pages = get_all_pages_from_phase1()
        if not all_pages:
            raise Exception("No pages found from Phase 1")
        
        phase2_results = process_all_pages_with_ocr(pdf_file, all_pages)
        save_ocr_results(phase2_results)
        generate_phase2_summary(phase2_results)
        return phase2_results
    
    result = run_phase_with_retry(phase2_func, "Phase 2")
    tracker.end_phase("Phase 2")
    return result

def run_phase2c_smart_selection(tracker):
    """Run Phase 2C: Smart LLM selection"""
    tracker.start_phase("Phase 2C: Smart LLM Selection")
    
    def phase2c_func():
        pymupdf_pages = read_pymupdf_clean_pages_2c()
        ocr_pages = read_ocr_all_pages_2c()
        phase2c_results = process_all_pages_selection(pymupdf_pages, ocr_pages)
        save_selection_results(phase2c_results)
        generate_phase2c_summary(phase2c_results)
        return phase2c_results
    
    result = run_phase_with_retry(phase2c_func, "Phase 2C")
    tracker.end_phase("Phase 2C")
    return result

def run_phase2d_combining(tracker):
    """Run Phase 2D: Intelligent combining"""
    tracker.start_phase("Phase 2D: Intelligent Combining")
    
    def phase2d_func():
        selection_results = read_smart_selection_results()
        pymupdf_pages = read_pymupdf_clean_pages_2d()
        ocr_pages = read_ocr_all_pages_2d()
        combined_file = create_intelligent_combined_file(selection_results, pymupdf_pages, ocr_pages)
        generate_selection_summary(selection_results)
        return combined_file
    
    result = run_phase_with_retry(phase2d_func, "Phase 2D")
    tracker.end_phase("Phase 2D")
    return result

def run_phase3_extraction(tracker):
    """Run Phase 3: LLM field extraction"""
    tracker.start_phase("Phase 3: LLM Field Extraction")
    
    def phase3_func():
        all_pages = read_combined_file()
        if not all_pages:
            raise Exception("No combined file found!")
        
        chunks = create_chunks(all_pages, chunk_size=4)
        all_results = []
        
        for chunk in chunks:
            print(f"Processing Chunk {chunk['chunk_num']}/{len(chunks)}...")
            result = extract_with_llm(chunk, chunk['chunk_num'], len(chunks))
            all_results.append(result)
        
        merged_result = merge_extraction_results(all_results)
        save_extraction_results(merged_result, all_results)
        generate_phase3_summary(merged_result)
        
        # Create final_validated_fields.json for Google Sheets
        from A_phase3_llm_extraction import create_final_validated_fields
        create_final_validated_fields(merged_result)
        
        return merged_result
    
    result = run_phase_with_retry(phase3_func, "Phase 3")
    tracker.end_phase("Phase 3")
    return result

def run_phase4_sheets(tracker):
    """Run Phase 4: Google Sheets integration"""
    tracker.start_phase("Phase 4: Google Sheets Integration")
    
    def phase4_func():
        push_to_sheets()
        return True
    
    result = run_phase_with_retry(phase4_func, "Phase 4")
    tracker.end_phase("Phase 4")
    return result

def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("INTELLIGENT PDF PROCESSING PIPELINE")
    print("=" * 80)
    print("PDF -> AI -> Google Sheets")
    print("=" * 80)

def print_success_summary():
    """Print completion summary"""
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("Results:")
    print("  - Text extracted and optimized")
    print("  - Insurance fields identified")
    print("  - Data pushed to Google Sheets")
    print("  - Ready for analysis!")
    print("=" * 80)

def main():
    """Main pipeline execution"""
    print_banner()
    
    # Store original directory FIRST
    original_dir = os.getcwd()
    
    try:
        # Setup
        setup_environment()
        selected_pdf = select_pdf()
        
        # Change to property directory
        # We're already in property/src, so go up one level to property/
        property_dir = os.path.join(original_dir, "..")
        os.chdir(property_dir)
        
        # Initialize progress tracker
        tracker = ProgressTracker(5)
        
        # Run phases with error handling and progress tracking
        pdf_file = f"pdf/{selected_pdf}"
        
        if not os.path.exists(pdf_file):
            raise Exception(f"PDF file '{pdf_file}' not found!")
        
        # Execute all phases
        run_phase1_pymupdf(pdf_file, tracker)
        run_phase2_ocr(pdf_file, tracker)
        run_phase2c_smart_selection(tracker)
        run_phase2d_combining(tracker)
        run_phase3_extraction(tracker)
        run_phase4_sheets(tracker)
        
        print_success_summary()
        return True
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        return False
    finally:
        if original_dir:
            os.chdir(original_dir)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)