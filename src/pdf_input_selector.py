#!/usr/bin/env python3
"""
PDF INPUT SELECTOR - Simple PDF Path Selector
================================================================================
This script provides an interactive interface to:
1. Show all available PDFs in pdf/ folder
2. Let user select which PDF to process
3. Return the selected PDF path

Usage: python pdf_input_selector.py
"""

import os
import glob

def get_available_pdfs():
    """Get all PDF files from pdf/ folder"""
    pdf_folder = "../pdf"  # Go up one level from src/ to property/, then into pdf/
    if not os.path.exists(pdf_folder):
        print(f"Error: PDF folder '{pdf_folder}' not found!")
        return []
    
    pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    pdf_files = [os.path.basename(pdf) for pdf in pdf_files]  # Get just filenames
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder}/ folder!")
        return []
    
    return pdf_files

def display_pdf_selection(pdf_files):
    """Display available PDFs with numbers"""
    print(f"\nAVAILABLE PDF FILES:")
    print("=" * 50)
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf}")
    print("=" * 50)

def get_user_selection(pdf_files):
    """Get user's PDF selection"""
    while True:
        try:
            choice = input(f"\nSelect PDF to process (1-{len(pdf_files)}): ").strip()
            if not choice:
                print("Please enter a number!")
                continue
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(pdf_files):
                selected_pdf = pdf_files[choice_num - 1]
                print(f"Selected: {selected_pdf}")
                return selected_pdf
            else:
                print(f"Invalid choice! Please enter a number between 1 and {len(pdf_files)}")
        except ValueError:
            print("Invalid input! Please enter a valid number.")

def main():
    """Main PDF input selector - RETURNS PDF PATH"""
    print("PDF INPUT SELECTOR")
    print("=" * 50)
    
    # Get available PDFs
    pdf_files = get_available_pdfs()
    if not pdf_files:
        return None
    
    # Display PDF selection
    display_pdf_selection(pdf_files)
    
    # Get user selection
    selected_pdf = get_user_selection(pdf_files)
    
    # Return the PDF path
    pdf_path = f"pdf/{selected_pdf}"
    print(f"PDF Path: {pdf_path}")
    
    # Write selected path to file for master workflow to read
    with open("selected_pdf_path.txt", "w") as f:
        f.write(pdf_path)
    
    return pdf_path

if __name__ == "__main__":
    selected_path = main()
    if selected_path:
        print(f"\nSelected PDF Path: {selected_path}")
    else:
        print(f"\nNo PDF selected!")
