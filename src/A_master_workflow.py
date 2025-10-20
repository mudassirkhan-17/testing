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

def get_pdf_path_from_selector():
    """Get PDF path from PDF input selector"""
    print(f"\nGETTING PDF PATH FROM SELECTOR")
    print("=" * 50)
    
    try:
        # Change to property directory first
        original_dir = os.getcwd()
        property_dir = os.path.join(original_dir, "property")
        os.chdir(property_dir)
        
        # Run the PDF input selector
        result = subprocess.run([sys.executable, "src/pdf_input_selector.py"], 
                              capture_output=True, text=True)
        
        # Change back to original directory
        os.chdir(original_dir)
        
        if result.returncode == 0:
            # Extract PDF path from output
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if "Selected PDF Path:" in line:
                    pdf_path = line.split("Selected PDF Path:")[-1].strip()
                    print(f"PDF Path Selected: {pdf_path}")
                    return pdf_path
            
            print("Could not extract PDF path from selector output")
            return None
        else:
            print("PDF Input Selector failed!")
            print("Error:", result.stderr)
            return None
            
    except Exception as e:
        print(f"Error running PDF Input Selector: {e}")
        return None

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

def update_phase_scripts_with_pdf_path(pdf_path):
    """Update phase scripts with the selected PDF path"""
    print(f"\nUPDATING PHASE SCRIPTS WITH PDF PATH: {pdf_path}")
    print("=" * 50)
    
    # Phase scripts that need PDF path updates
    phase_scripts = [
        "src/A_phase1_Pymupdf.py",
        "src/A_phase2_ocr.py", 
        "src/A_phase3_llm_extraction.py",
        "src/A_phase4_vlm.py"
    ]
    
    original_contents = {}
    
    try:
        for script in phase_scripts:
            if os.path.exists(script):
                # Read current content
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Store original content
                original_contents[script] = content
                
                # Update PDF path
                if 'pdf_file = "pdf/PROPERTY QUOTE.pdf"' in content:
                    new_content = content.replace(
                        'pdf_file = "pdf/PROPERTY QUOTE.pdf"',
                        f'pdf_file = "{pdf_path}"'
                    )
                elif 'pdf_file = "../pdf/PROPERTY QUOTE.pdf"' in content:
                    new_content = content.replace(
                        'pdf_file = "../pdf/PROPERTY QUOTE.pdf"',
                        f'pdf_file = "{pdf_path}"'
                    )
                else:
                    print(f"⚠️  Warning: Could not find PDF path pattern in {script}")
                    continue
                
                # Write updated content
                with open(script, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"Updated: {script}")
        
        return original_contents
        
    except Exception as e:
        print(f"Error updating PDF paths: {e}")
        return {}

def restore_phase_scripts(original_contents):
    """Restore original phase scripts"""
    print(f"\nRESTORING ORIGINAL PHASE SCRIPTS")
    print("=" * 50)
    
    for script, original_content in original_contents.items():
        try:
            with open(script, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"Restored: {script}")
        except Exception as e:
            print(f"Error restoring {script}: {e}")

def main():
    """Main workflow execution - DYNAMIC PDF PATH VERSION"""
    print("MASTER WORKFLOW - INTELLIGENT PDF PROCESSING PIPELINE")
    print("DYNAMIC PDF PATH VERSION")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get PDF path from selector
    pdf_path = get_pdf_path_from_selector()
    if not pdf_path:
        print("\nFailed to get PDF path from selector!")
        return False
    
    # Update phase scripts with selected PDF path
    original_contents = update_phase_scripts_with_pdf_path(pdf_path)
    if not original_contents:
        print("\nFailed to update phase scripts!")
        return False
    
    try:
        # Define the workflow phases
        phases = [
            {
                "name": "PHASE 1: PYMUPDF EXTRACTION",
                "script": "src/A_phase1_Pymupdf.py",
                "description": f"Extract text from {pdf_path} using PyMuPDF and classify page quality"
            },
            {
                "name": "PHASE 2: OCR PROCESSING", 
                "script": "src/A_phase2_ocr.py",
                "description": f"Process all pages of {pdf_path} with OCR for comprehensive coverage"
            },
            {
                "name": "PHASE 2C: SMART LLM SELECTION",
                "script": "src/A_phase2c_smart_selection.py", 
                "description": f"Use GPT-3.5 to select best text source for each page of {pdf_path}"
            },
            {
                "name": "PHASE 2D: INTELLIGENT COMBINING",
                "script": "src/A_phase2d_intelligent_combining.py",
                "description": f"Combine best text from each page of {pdf_path} into final optimized file"
            },
            {
                "name": "PHASE 3: LLM FIELD EXTRACTION",
                "script": "src/A_phase3_llm_extraction.py",
                "description": f"Extract insurance fields from {pdf_path} using GPT-5"
            },
            # {
            #     "name": "PHASE 4: VLM VALIDATION",
            #     "script": "src/A_phase4_vlm.py",
            #     "description": f"Validate fields from {pdf_path} using GPT-4 Vision and create final results"
            # }
            # VLM PHASE COMMENTED OUT TO SAVE COSTS - UNCOMMENT WHEN NEEDED
            {
                "name": "PHASE 4: GOOGLE SHEETS INTEGRATION",
                "script": "src/A_phase5_simple_sheets.py",
                "description": f"Push extracted fields from {pdf_path} to Google Sheets automatically"
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
            else:
                failed_phases.append(phase['name'])
                print(f"\nPHASE FAILED: {phase['name']}")
                print("Stopping workflow due to phase failure.")
                break
        
        # Final summary
        print(f"\n{'='*80}")
        print("WORKFLOW SUMMARY")
        print(f"{'='*80}")
        print(f"Selected PDF: {pdf_path}")
        print(f"Total Phases: {len(phases)}")
        print(f"Successful Phases: {len(successful_phases)}")
        print(f"Failed Phases: {len(failed_phases)}")
        
        if successful_phases:
            print("\nSuccessful Phases:")
            for phase in successful_phases:
                print(f"   - {phase}")
        
        if failed_phases:
            print("\nFailed Phases:")
            for phase in failed_phases:
                print(f"   - {phase}")
        
        if len(successful_phases) == len(phases):
            print(f"\nALL PHASES COMPLETED SUCCESSFULLY!")
            print(f"Processed PDF: {pdf_path}")
            print("Data has been extracted and processed")
            print("Check the results/ folder for detailed outputs")
            print("Data pushed to Google Sheets")
            print("Data is now live in Google Sheets!")
            return True
        else:
            print(f"\nWORKFLOW COMPLETED WITH ISSUES")
            print("Some phases failed. Check the output above for details.")
            return False
    
    finally:
        # Always restore original phase scripts
        restore_phase_scripts(original_contents)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
