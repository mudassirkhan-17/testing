
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
        
        # Run the PDF input selector interactively
        result = subprocess.run([sys.executable, "src/pdf_input_selector.py"], 
                              text=True)
        
        # Change back to original directory
        os.chdir(original_dir)
        
        if result.returncode == 0:
            # Read PDF path from file
            try:
                with open("selected_pdf_path.txt", "r") as f:
                    pdf_path = f.read().strip()
                print(f"PDF Path Selected: {pdf_path}")
                return pdf_path
            except FileNotFoundError:
                print("Could not read selected PDF path from file")
                return None
        else:
            print("PDF Input Selector failed!")
            return None
            
    except Exception as e:
        print(f"Error running PDF Input Selector: {e}")
        return None




if __name__ == "__main__":
    result = get_pdf_path_from_selector()
    print(f"\nFinal Result: {result}")