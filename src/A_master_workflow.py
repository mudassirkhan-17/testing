#!/usr/bin/env python3
"""
MASTER WORKFLOW - COMPLETE PDF PROCESSING PIPELINE
================================================================================
This script runs the entire intelligent PDF processing pipeline automatically:
Phase 1: PyMuPDF extraction and page classification
Phase 2: OCR processing of all pages
Phase 2C: Smart LLM selection (best source per page)
Phase 2D: Intelligent combining (creates final optimized text)
Phase 3: LLM field extraction
Phase 4: VLM validation and final results

ENHANCED VERSION: Processes ALL PDFs in pdf/ folder automatically

Usage: python A_master_workflow.py
"""

import subprocess
import sys
import os
import time
import glob
import json
from datetime import datetime

def run_phase(phase_name, script_name, description):
    """Run a phase and handle errors"""
    print(f"\n{'='*80}")
    print(f"STARTING {phase_name}")
    print(f"{description}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    try:
        # Run the phase script from root directory
        result = subprocess.run([sys.executable, f"src/{script_name}"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{phase_name} COMPLETED SUCCESSFULLY!")
            print("Output:")
            print(result.stdout)
            return True
        else:
            print(f"{phase_name} FAILED!")
            print("Error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"{phase_name} FAILED WITH EXCEPTION!")
        print(f"Error: {e}")
        return False

def get_all_pdfs():
    """Get all PDF files from pdf/ folder"""
    pdf_folder = "pdf"
    if not os.path.exists(pdf_folder):
        print(f"Error: PDF folder '{pdf_folder}' not found!")
        return []
    
    pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    pdf_files = [os.path.basename(pdf) for pdf in pdf_files]  # Get just filenames
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder}/ folder!")
        return []
    
    print(f"Found {len(pdf_files)} PDF files:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf}")
    
    return pdf_files

def check_prerequisites():
    """Check if all required files exist"""
    # Change to src directory for file checks
    original_dir = os.getcwd()
    os.chdir("src")
    
    required_files = [
        "A_phase1_Pymupdf.py",
        "A_phase2_ocr.py", 
        "A_phase2c_smart_selection.py",
        "A_phase2d_intelligent_combining.py",
        "A_phase3_llm_extraction.py",
        "A_phase4_vlm.py",
        "A_phase5_simple_sheets.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("MISSING REQUIRED FILES:")
        for file in missing_files:
            print(f"   - {file}")
        os.chdir(original_dir)
        return False
    
    # Check if any PDFs exist
    pdf_files = glob.glob("../pdf/*.pdf")
    if not pdf_files:
        print("MISSING PDF FILES: No PDF files found in pdf/ folder")
        print("Please add PDF files to the pdf/ subdirectory.")
        os.chdir(original_dir)
        return False
    
    # Check if .env exists
    if not os.path.exists("../config/.env"):
        print("MISSING ENVIRONMENT FILE: ../config/.env")
        print("Please create ../config/.env with your API key")
        os.chdir(original_dir)
        return False
    
    # Return to original directory
    os.chdir(original_dir)
    return True

def process_single_pdf(pdf_name):
    """Process a single PDF through the entire pipeline"""
    print(f"\n{'='*80}")
    print(f"PROCESSING PDF: {pdf_name}")
    print(f"{'='*80}")
    
    # Update PDF path in phase scripts temporarily
    original_pdf_paths = {}
    
    try:
        # Modify phase scripts to use specific PDF
        phase_scripts = [
            "src/A_phase1_Pymupdf.py",
            "src/A_phase2_ocr.py", 
            "src/A_phase4_vlm.py"
        ]
        
        for script in phase_scripts:
            if os.path.exists(script):
                # Read current content
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Store original path
                original_pdf_paths[script] = content
                
                # Replace PDF path
                new_content = content.replace(
                    'pdf_file = "pdf/PROPERTY QUOTE.pdf"',
                    f'pdf_file = "pdf/{pdf_name}"'
                )
                
                # Write modified content
                with open(script, 'w', encoding='utf-8') as f:
                    f.write(new_content)
        
        # Run the pipeline phases
        phases = [
            {
                "name": "PHASE 1: PYMUPDF EXTRACTION",
                "script": "A_phase1_Pymupdf.py",
                "description": f"Extract text from {pdf_name} using PyMuPDF"
            },
            {
                "name": "PHASE 2: OCR PROCESSING", 
                "script": "A_phase2_ocr.py",
                "description": f"Process all pages of {pdf_name} with OCR"
            },
            {
                "name": "PHASE 2C: SMART LLM SELECTION",
                "script": "A_phase2c_smart_selection.py", 
                "description": f"Use GPT-3.5 to select best text source for {pdf_name}"
            },
            {
                "name": "PHASE 2D: INTELLIGENT COMBINING",
                "script": "A_phase2d_intelligent_combining.py",
                "description": f"Combine best text from {pdf_name} pages"
            },
            {
                "name": "PHASE 3: LLM FIELD EXTRACTION",
                "script": "A_phase3_llm_extraction.py",
                "description": f"Extract insurance fields from {pdf_name}"
            }
        ]
        
        success = True
        for phase in phases:
            if not run_phase(phase["name"], phase["script"], phase["description"]):
                success = False
                break
        
        return success
        
    finally:
        # Restore original PDF paths
        for script, original_content in original_pdf_paths.items():
            with open(script, 'w', encoding='utf-8') as f:
                f.write(original_content)

def merge_all_results():
    """Merge results from all processed PDFs"""
    print(f"\n{'='*80}")
    print("MERGING RESULTS FROM ALL PDFs")
    print(f"{'='*80}")
    
    # Read all individual results
    results_folder = "results"
    all_results = {}
    
    # Find all extracted_insurance_fields.json files
    result_files = glob.glob(os.path.join(results_folder, "*_extracted_insurance_fields.json"))
    
    if not result_files:
        print("No individual results found to merge!")
        return False
    
    print(f"Found {len(result_files)} result files to merge:")
    for file in result_files:
        print(f"   - {os.path.basename(file)}")
    
    # Load all results
    for result_file in result_files:
        pdf_name = os.path.basename(result_file).replace("_extracted_insurance_fields.json", "")
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results[pdf_name] = data
                print(f"Loaded results from {pdf_name}")
        except Exception as e:
            print(f"Error loading {result_file}: {e}")
    
    # Merge results intelligently
    merged_results = {}
    
    for pdf_name, pdf_results in all_results.items():
        for field_name, field_data in pdf_results.items():
            if field_name not in merged_results:
                merged_results[field_name] = {
                    'llm_value': field_data.get('llm_value', ''),
                    'source_pdf': pdf_name,
                    'source_page': field_data.get('source_page', ''),
                    'confidence': field_data.get('confidence', 'medium')
                }
            else:
                # Choose best value based on completeness and confidence
                current_value = merged_results[field_name]['llm_value']
                new_value = field_data.get('llm_value', '')
                
                # If current value is empty/blank, use new value
                if not current_value or current_value.strip() == '' or current_value == 'null':
                    merged_results[field_name] = {
                        'llm_value': new_value,
                        'source_pdf': pdf_name,
                        'source_page': field_data.get('source_page', ''),
                        'confidence': field_data.get('confidence', 'medium')
                    }
                # If new value is more complete, use it
                elif new_value and len(new_value) > len(current_value):
                    merged_results[field_name] = {
                        'llm_value': new_value,
                        'source_pdf': pdf_name,
                        'source_page': field_data.get('source_page', ''),
                        'confidence': field_data.get('confidence', 'medium')
                    }
    
    # Save merged results
    merged_file = os.path.join(results_folder, "merged_all_pdfs_results.json")
    with open(merged_file, 'w', encoding='utf-8') as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)
    
    print(f"Merged results saved to: {merged_file}")
    
    # Create final validated fields file for Google Sheets
    final_file = os.path.join(results_folder, "final_validated_fields.json")
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)
    
    print(f"Final results saved to: {final_file}")
    
    return True

def main():
    """Main workflow execution - Enhanced for multiple PDFs"""
    print("MASTER WORKFLOW - INTELLIGENT PDF PROCESSING PIPELINE")
    print("ENHANCED VERSION: Processes ALL PDFs in pdf/ folder")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check prerequisites
    print("\nCHECKING PREREQUISITES...")
    if not check_prerequisites():
        print("\nPREREQUISITES NOT MET. Please fix the issues above.")
        return False
    
    print("All prerequisites met!")
    
    # Get all PDFs to process
    print("\nSCANNING PDF FOLDER...")
    pdf_files = get_all_pdfs()
    
    if not pdf_files:
        print("No PDF files found to process!")
        return False
    
    print(f"\nWill process {len(pdf_files)} PDF files:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf}")
    
    # Process each PDF individually
    successful_pdfs = 0
    failed_pdfs = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*80}")
        print(f"PROCESSING PDF {i}/{len(pdf_files)}: {pdf_file}")
        print(f"{'='*80}")
        
        if process_single_pdf(pdf_file):
            successful_pdfs += 1
            print(f"✅ Successfully processed: {pdf_file}")
        else:
            failed_pdfs.append(pdf_file)
            print(f"❌ Failed to process: {pdf_file}")
    
    # Merge all results
    print(f"\n{'='*80}")
    print("MERGING RESULTS FROM ALL PDFs")
    print(f"{'='*80}")
    
    if successful_pdfs > 0:
        if merge_all_results():
            print("✅ Successfully merged all results!")
        else:
            print("❌ Failed to merge results!")
    
    # Push to Google Sheets
    print(f"\n{'='*80}")
    print("PUSHING TO GOOGLE SHEETS")
    print(f"{'='*80}")
    
    if successful_pdfs > 0:
        if run_phase("GOOGLE SHEETS INTEGRATION", "A_phase5_simple_sheets.py", "Push merged data to Google Sheets"):
            print("✅ Successfully pushed to Google Sheets!")
        else:
            print("❌ Failed to push to Google Sheets!")
    
    # Final summary
    print(f"\n{'='*80}")
    print("WORKFLOW SUMMARY")
    print(f"{'='*80}")
    print(f"Total PDFs Found: {len(pdf_files)}")
    print(f"Successfully Processed: {successful_pdfs}")
    print(f"Failed PDFs: {len(failed_pdfs)}")
    
    if failed_pdfs:
        print("\nFailed PDFs:")
        for pdf in failed_pdfs:
            print(f"   - {pdf}")
    
    if successful_pdfs > 0:
        print(f"\n🎉 SUCCESSFULLY PROCESSED {successful_pdfs} PDF(s)!")
        print("📊 Data has been extracted and merged")
        print("📁 Check the results/ folder for detailed outputs")
        print("📈 Data pushed to Google Sheets with source tracking")
        return True
    else:
        print(f"\n❌ NO PDFs PROCESSED SUCCESSFULLY!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
