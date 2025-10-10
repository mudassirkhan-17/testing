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

Usage: python A_master_workflow.py
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def run_phase(phase_name, script_name, description):
    """Run a phase and handle errors"""
    print(f"\n{'='*80}")
    print(f"STARTING {phase_name}")
    print(f"{description}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    try:
        # Run the phase script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
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

def check_prerequisites():
    """Check if all required files exist"""
    required_files = [
        "A_phase1_Pymupdf.py",
        "A_phase2_ocr.py", 
        "A_phase2c_smart_selection.py",
        "A_phase2d_intelligent_combining.py",
        "A_phase3_llm_extraction.py",
        "A_phase4_vlm.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("MISSING REQUIRED FILES:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    # Check if PDF exists
    if not os.path.exists("pdf/PROPERTY QUOTE.pdf"):
        print("MISSING PDF FILE: pdf/PROPERTY QUOTE.pdf")
        return False
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("MISSING .env FILE: Please create .env with your OpenAI API key")
        return False
    
    return True

def main():
    """Main workflow execution"""
    print("MASTER WORKFLOW - INTELLIGENT PDF PROCESSING PIPELINE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check prerequisites
    print("\nCHECKING PREREQUISITES...")
    if not check_prerequisites():
        print("\nPREREQUISITES NOT MET. Please fix the issues above.")
        return False
    
    print("All prerequisites met!")
    
    # Define the workflow phases
    phases = [
        {
            "name": "PHASE 1: PYMUPDF EXTRACTION",
            "script": "A_phase1_Pymupdf.py",
            "description": "Extract text using PyMuPDF and classify page quality"
        },
        {
            "name": "PHASE 2: OCR PROCESSING", 
            "script": "A_phase2_ocr.py",
            "description": "Process all pages with OCR for comprehensive coverage"
        },
        {
            "name": "PHASE 2C: SMART LLM SELECTION",
            "script": "A_phase2c_smart_selection.py", 
            "description": "Use GPT-3.5 to select best text source for each page"
        },
        {
            "name": "PHASE 2D: INTELLIGENT COMBINING",
            "script": "A_phase2d_intelligent_combining.py",
            "description": "Combine best text from each page into final optimized file"
        },
        {
            "name": "PHASE 3: LLM FIELD EXTRACTION",
            "script": "A_phase3_llm_extraction.py",
            "description": "Extract insurance fields using GPT-4"
        },
        # {
        #     "name": "PHASE 4: VLM VALIDATION",
        #     "script": "A_phase4_vlm.py",
        #     "description": "Validate fields using GPT-4 Vision and create final results"
        # }
        # VLM PHASE COMMENTED OUT TO SAVE COSTS - UNCOMMENT WHEN NEEDED
        {
            "name": "PHASE 4: GOOGLE SHEETS INTEGRATION",
            "script": "A_phase5_simple_sheets.py",
            "description": "Push extracted fields to Google Sheets automatically"
        }
    ]
    
    # Track successful phases
    successful_phases = []
    failed_phases = []
    
    # Run each phase
    for i, phase in enumerate(phases, 1):
        print(f"\nPHASE {i}/{len(phases)}: {phase['name']}")
        
        success = run_phase(phase['name'], phase['script'], phase['description'])
        
        if success:
            successful_phases.append(phase['name'])
            print(f"Phase {i} completed successfully!")
        else:
            failed_phases.append(phase['name'])
            print(f"Phase {i} failed!")
            
            # Continue automatically (non-interactive)
            print(f"\nPhase {i} failed. Continuing with remaining phases...")
        
        # Small delay between phases
        time.sleep(2)
    
    # Final summary
    print(f"\n{'='*80}")
    print("WORKFLOW SUMMARY")
    print(f"{'='*80}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Successful phases: {len(successful_phases)}/6")
    print(f"Failed phases: {len(failed_phases)}/6")
    
    if successful_phases:
        print("\nSUCCESSFUL PHASES:")
        for phase in successful_phases:
            print(f"   - {phase}")
    
    if failed_phases:
        print("\nFAILED PHASES:")
        for phase in failed_phases:
            print(f"   - {phase}")
    
    # Check for final output
    if os.path.exists("final_validated_fields.json"):
        print(f"\nFINAL RESULTS AVAILABLE:")
        print(f"   final_validated_fields.json - Complete insurance field extraction")
        print(f"   extraction_report.txt - LLM extraction summary")
        if os.path.exists("vlm_validation_report.txt"):
            print(f"   vlm_validation_report.txt - Detailed validation report")
    
    # Check if Google Sheets was successful
    google_sheets_success = any("GOOGLE SHEETS" in phase for phase in successful_phases)
    if google_sheets_success:
        print(f"\nGOOGLE SHEETS INTEGRATION:")
        print(f"   Data automatically pushed to 'Insurance Fields Data' sheet")
        print(f"   Check your Google Drive for live results!")
    
    if len(successful_phases) == len(phases):
        print(f"\nWORKFLOW COMPLETED SUCCESSFULLY!")
        print("All phases completed. Your insurance document has been fully processed!")
        if google_sheets_success:
            print("Data is now live in Google Sheets!")
    else:
        print(f"\nWORKFLOW COMPLETED WITH ISSUES")
        print("Some phases failed. Check the output above for details.")
    
    return len(successful_phases) == len(phases)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
