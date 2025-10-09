#!/usr/bin/env python3
"""
STEP 3: VLM VALIDATION
================================================================================
This script validates LLM extraction results using GPT-4 Vision on specific pages.

VLM Strategy:
- Chunks with 3+ fields: Run VLM on ALL pages in chunk
- Chunks with ≤2 fields: Run VLM ONLY on pages containing fields
"""

import openai
import json
import fitz
import io
import os
from PIL import Image
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def read_extraction_results():
    """Read the LLM extraction results to determine VLM targets"""
    try:
        with open('extraction_chunks.json', 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        with open('extracted_insurance_fields.json', 'r', encoding='utf-8') as f:
            fields = json.load(f)
        
        return chunks, fields
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None

def determine_vlm_targets(chunks):
    """Determine which pages need VLM validation based on field count"""
    vlm_pages = set()
    
    for chunk in chunks:
        if '_metadata' in chunk and 'error' not in chunk.get('_metadata', {}):
            chunk_pages = chunk['_metadata']['page_nums']
            fields_found = len([k for k, v in chunk.items() if v is not None and k != '_metadata'])
            
            print(f"Chunk {chunk['_metadata']['chunk_num']}: {fields_found} fields on pages {chunk_pages}")
            
            if fields_found >= 3:
                # High-value chunk: validate ALL pages
                vlm_pages.update(chunk_pages)
                print(f"  -> High-value chunk: Adding ALL pages {chunk_pages}")
            elif fields_found > 0:
                # Low-value chunk: validate ONLY pages with fields
                individual_pages = chunk['_metadata'].get('individual_page_fields', {})
                for field, pages in individual_pages.items():
                    vlm_pages.update(pages)
                    print(f"  -> Low-value chunk: Adding specific pages {list(individual_pages.values())}")
    
    return sorted(list(vlm_pages))

def convert_page_to_image(pdf_file, page_num):
    """Convert PDF page to image for VLM processing"""
    try:
        doc = fitz.open(pdf_file)
        page = doc[page_num - 1]  # Convert to 0-based index
        
        # High resolution for better VLM analysis
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        doc.close()
        return img_data
    except Exception as e:
        print(f"Error converting page {page_num} to image: {e}")
        return None

def validate_with_vlm(page_num, img_data, existing_fields):
    """Use GPT-4 Vision to independently analyze and extract insurance fields"""
    
    prompt = f"""
    Analyze this insurance document page (Page {page_num}) and extract ALL insurance coverage information you can find.
    
    IMPORTANT: Work independently and thoroughly. Extract EVERYTHING you can see on this page.
    
    THE 31 SPECIFIC FIELDS TO LOOK FOR:
    1. Construction Type - Look for: "FRAME", "Frame", "Joisted Masonry", "Masonry Non-Combustible", any construction type
    2. Valuation and Coinsurance - Look for: "Replacement Cost, 80%", "Replacement Cost, 90%", "Actual Cash Value", any valuation method with percentage
    3. Cosmetic Damage - Look for: "Excluded", "Included", "Cosmetic Damage is Excluded", any cosmetic damage status
    4. Building - Look for: "$500,000", "$600,000", "Coverage not required", "ACV on Roof: Cosmetic Damage is Excluded", any building coverage
    5. Pumps - Look for: "$10,000.00", "$60,000", any pump coverage amount
    6. Canopy - Look for: "$40,000", "$100,000", any canopy coverage amount
    7. ROOF EXCLUSION - Look for: "Included", "Excluded", "Cosmetic Damage is Excluded", any roof exclusion status
    8. Roof Surfacing - Look for: "ACV only applies to roofs that are more than 15 years old", any roof surfacing details
    9. Roof Surfacing -Limitation - Look for: "ACV on Roof", "Cosmetic Damage is Excluded", any roof limitation details
    10. Business Personal Property - Look for: "$50,000.00", "$200,000", "$125,000", any business personal property amount
    11. Business Income - Look for: "$100,000", "$100,000 (1/6)", "$100,000 (1/3)", any business income amount with time periods
    12. Business Income with Extra Expense - Look for: "$100,000", "with Extra Expense", any business income with extra expense
    13. Equipment Breakdown - Look for: "Included", "$225,000", any equipment breakdown coverage
    14. Outdoor Signs - Look for: "$10,000", "$5,000", "Included", "Deductible $250", any outdoor signs coverage
    15. Signs Within 1,000 Feet to Premises - Look for: any signs within 1,000 feet coverage details
    16. Employee Dishonesty - Look for: "$5,000", "Included", "Not Offered", "Not offered", any employee dishonesty coverage
    17. Money & Securities - Look for: "$10,000", "$5,000", "On Premises $2,500 / Off Premises $2,500", any money & securities coverage
    18. Money and Securities (Inside; Outside) - Look for: any separate inside/outside money & securities limits
    19. Spoilage - Look for: "$5,000", "$10,000", "Deductible $250", any spoilage coverage
    20. Theft - Look for: "Sublimit: $5,000", "Ded: $2,500", "Sublimit $10,000", "Deductible $1,000", any theft coverage
    21. Theft Sublimit - Look for: "$5,000", "$15,000", "$10,000", any theft sublimit amount
    22. Theft Deductible - Look for: "$2,500", "$1,000", "$250", any theft deductible amount
    23. Windstorm or Hail - Look for: "$2,500", "2%", "1%", "Min Per Building", any windstorm or hail coverage
    24. Named Storm Deductible - Look for: any named storm deductible amount
    25. Wind and Hail and Named Storm exclusion - Look for: any wind/hail/named storm exclusion details
    26. All Other Perils Deductible - Look for: "$2,500", "$1,000", any other perils deductible amount
    27. Fire Station Alarm - Look for: "$2,500.00", "Local", "Central", any fire station alarm details
    28. Burglar Alarm - Look for: "Local", "Central", "Active Central Station", any burglar alarm details
    29. Terrorism - Look for: "APPLIES", "Excluded", "Included", "Can be added", any terrorism coverage status
    30. Protective Safeguards Requirements - Look for: any protective safeguards requirements listed
    31. Minimum Earned Premium (MEP) - Look for: "25%", "MEP: 25%", "35%", "MEP: 35%", any percentage
    
    EXTRACTION RULES - FOCUS ON VALUES NOT DESCRIPTIONS:
    - Extract SPECIFIC VALUES, not field descriptions or headers
    - Look for ACTUAL DATA VALUES: dollar amounts, percentages, specific terms
    - For Construction Type: Extract the actual type (Frame, Masonry, Brick, etc.) NOT "Construction Type:"
    - For Valuation: Extract the actual method + percentage (Replacement Cost Value 80%) NOT "Valuation:"
    - For Dollar Amounts: Extract the actual amount ($100,000) NOT "Business Personal Property:"
    - For Percentages: Extract the actual percentage (25%) NOT "Minimum Earned Premium:"
    - For Deductibles: Extract the actual deductible amount ($2,500 Min Per Building) NOT "Windstorm Deductible:"
    - For Coverage Status: Extract the actual status (Included, Excluded, $100) NOT the field name
    - For Business Income: Extract the actual amount + time period ($100,000 per month) NOT "Business Income:"
    - PRIORITIZE: Specific dollar amounts, percentages, and actual coverage terms
    - AVOID: Field names, headers, descriptions, or generic text
    - If field is not found, set to null
    - Do NOT hallucinate or make up values
    - Do NOT extract field names or descriptions
    - Look for the DATA VALUE, not the field label
    - Extract what the field CONTAINS, not what the field IS CALLED
    
    CRITICAL: Return ONLY valid JSON with this format:
    {{
        "Construction Type": {{"value": "FRAME", "confidence": "high", "source": "vlm"}},
        "Building": {{"value": "$500,000", "confidence": "medium", "source": "vlm"}},
        "Minimum Earned Premium (MEP)": {{"value": "25%", "confidence": "high", "source": "vlm"}}
    }}
    
    If field not found, use: {{"value": null, "confidence": "none", "source": "vlm"}}
    
    Be thorough and independent in your analysis. Extract everything you can see!
    """
    
    try:
        # Encode image to base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        # Use OpenAI API
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
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
            print(f"  [ERROR] Failed to parse VLM JSON response: {e}")
            print(f"  Raw response: {result_text[:200]}...")
            return None
            
    except Exception as e:
        print(f"  [ERROR] VLM processing failed: {e}")
        return None

def calculate_llm_confidence(llm_value):
    """Calculate confidence score for LLM value based on specificity"""
    if llm_value is None:
        return 0
    
    llm_value_str = str(llm_value).strip()
    
    # High confidence: Specific dollar amounts, percentages, exact terms
    if (llm_value_str.startswith('$') and any(c.isdigit() for c in llm_value_str)) or \
       ('%' in llm_value_str and any(c.isdigit() for c in llm_value_str)) or \
       llm_value_str.lower() in ['included', 'excluded', 'applies', 'not offered']:
        return 3
    
    # Medium confidence: Contains numbers or specific terms
    elif any(c.isdigit() for c in llm_value_str) or \
         any(term in llm_value_str.lower() for term in ['min', 'max', 'per', 'deductible']):
        return 2
    
    # Low confidence: Generic text
    else:
        return 1

def calculate_vlm_confidence(vlm_value):
    """Calculate confidence score for VLM value based on specificity"""
    if vlm_value is None:
        return 0
    
    vlm_value_str = str(vlm_value).strip()
    
    # High confidence: Specific dollar amounts, percentages, exact terms
    if (vlm_value_str.startswith('$') and any(c.isdigit() for c in vlm_value_str)) or \
       ('%' in vlm_value_str and any(c.isdigit() for c in vlm_value_str)) or \
       vlm_value_str.lower() in ['included', 'excluded', 'applies', 'not offered']:
        return 3
    
    # Medium confidence: Contains numbers or specific terms
    elif any(c.isdigit() for c in vlm_value_str) or \
         any(term in vlm_value_str.lower() for term in ['min', 'max', 'per', 'deductible']):
        return 2
    
    # Low confidence: Generic text or field descriptions
    else:
        return 1

def merge_vlm_results(llm_results, vlm_results):
    """Merge LLM and VLM results with independent VLM analysis"""
    merged = {}
    
    # Start with LLM results
    for field, value in llm_results.items():
        if not field.startswith('_'):
            merged[field] = {
                "llm_value": value,
                "vlm_value": None,
                "final_value": value,
                "confidence": "llm_only"
            }
    
    # Add VLM results
    for page_num, page_results in vlm_results.items():
        for field, data in page_results.items():
            if isinstance(data, dict) and 'value' in data:
                vlm_value = data['value']
                confidence = data.get('confidence', 'unknown')
                
                # Only process non-null VLM values
                if vlm_value is not None:
                    if field not in merged:
                        # VLM found new field
                        merged[field] = {
                            "llm_value": None,
                            "vlm_value": vlm_value,
                            "final_value": vlm_value,
                            "confidence": f"vlm_{confidence}"
                        }
                        print(f"  {field}: VLM only (new discovery)")
                    else:
                        # Update existing field with VLM validation
                        merged[field]["vlm_value"] = vlm_value
                        merged[field]["confidence"] = f"llm+vlm_{confidence}"
                        
                        # Use confidence scoring to decide between LLM and VLM
                        llm_conf = calculate_llm_confidence(merged[field]["llm_value"])
                        vlm_conf = calculate_vlm_confidence(vlm_value)
                        
                        if merged[field]["llm_value"] != vlm_value:
                            if llm_conf > vlm_conf:
                                merged[field]["final_value"] = merged[field]["llm_value"]
                                print(f"  {field}: LLM wins (conf: {llm_conf} vs {vlm_conf}) - LLM='{merged[field]['llm_value']}' vs VLM='{vlm_value}'")
                            elif vlm_conf > llm_conf:
                                merged[field]["final_value"] = vlm_value
                                print(f"  {field}: VLM wins (conf: {vlm_conf} vs {llm_conf}) - LLM='{merged[field]['llm_value']}' vs VLM='{vlm_value}'")
                            else:
                                # Equal confidence, prefer LLM for consistency
                                merged[field]["final_value"] = merged[field]["llm_value"]
                                print(f"  {field}: LLM preferred (equal conf: {llm_conf}) - LLM='{merged[field]['llm_value']}' vs VLM='{vlm_value}'")
                        else:
                            print(f"  {field}: VLM confirmed LLM result")
    
    return merged

def save_vlm_results(vlm_results, merged_results):
    """Save VLM validation results"""
    
    # Save detailed VLM results
    with open('vlm_validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(vlm_results, f, indent=2, ensure_ascii=False)
    
    # Save VLM-only extracted fields (similar to LLM extraction format)
    vlm_only_fields = {}
    for page_num, page_results in vlm_results.items():
        for field, data in page_results.items():
            if isinstance(data, dict) and 'value' in data and data['value'] is not None:
                vlm_only_fields[field] = data['value']
    
    with open('vlm_extracted_fields.json', 'w', encoding='utf-8') as f:
        json.dump(vlm_only_fields, f, indent=2, ensure_ascii=False)
    
    # Save merged results
    with open('final_validated_fields.json', 'w', encoding='utf-8') as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)
    
    # Save summary report
    with open('vlm_validation_report.txt', 'w', encoding='utf-8') as f:
        f.write("VLM VALIDATION REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("PAGES PROCESSED:\n")
        for page_num in sorted(vlm_results.keys()):
            f.write(f"  Page {page_num}\n")
        
        f.write(f"\nVLM-ONLY FIELDS FOUND: {len(vlm_only_fields)}\n")
        f.write(f"FIELDS VALIDATED: {len([f for f, data in merged_results.items() if data['final_value'] is not None])}\n")
        f.write(f"FIELDS WITH VLM CONFIRMATION: {len([f for f, data in merged_results.items() if 'vlm' in data['confidence']])}\n")
        
        f.write("\nVLM-ONLY FIELDS:\n")
        f.write("-" * 30 + "\n")
        for field, value in vlm_only_fields.items():
            f.write(f"  {field}: {value}\n")
        
        f.write("\nDISCREPANCIES FOUND:\n")
        for field, data in merged_results.items():
            if data['llm_value'] != data['vlm_value'] and data['llm_value'] is not None and data['vlm_value'] is not None:
                f.write(f"  {field}: LLM='{data['llm_value']}' vs VLM='{data['vlm_value']}'\n")
    
    print(f"\nVLM validation results saved:")
    print(f"  Detailed results: vlm_validation_results.json")
    print(f"  VLM-only fields: vlm_extracted_fields.json")
    print(f"  Final validated fields: final_validated_fields.json")
    print(f"  Validation report: vlm_validation_report.txt")

def main():
    """Main VLM validation process"""
    print("STEP 3: VLM VALIDATION")
    print("=" * 80)
    
    # Set OpenAI API key
    # Set OpenAI API key from environment
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai.api_key:
        print("Error: OPENAI_API_KEY not found in environment variables!")
        print("Please set your OpenAI API key in the .env file")
        exit(1)
    
    # Read LLM extraction results
    chunks, llm_fields = read_extraction_results()
    if not chunks or not llm_fields:
        print("Error: Could not read LLM extraction results")
        return
    
    # Determine VLM target pages
    vlm_pages = determine_vlm_targets(chunks)
    print(f"\nVLM TARGET PAGES: {vlm_pages}")
    
    if not vlm_pages:
        print("No pages require VLM validation")
        return
    
    # Process each target page with VLM
    vlm_results = {}
    pdf_file = "pdf/PROPERTY QUOTE.pdf"
    
    for page_num in vlm_pages:
        print(f"\nProcessing Page {page_num} with VLM...")
        
        # Convert page to image
        img_data = convert_page_to_image(pdf_file, page_num)
        if not img_data:
            continue
        
        # Get existing fields for this page
        existing_fields = {}
        for field, value in llm_fields.items():
            if not field.startswith('_') and value is not None:
                # Check if this field was found on this page
                for chunk in chunks:
                    if '_metadata' in chunk:
                        individual_pages = chunk['_metadata'].get('individual_page_fields', {})
                        if field in individual_pages and page_num in individual_pages[field]:
                            existing_fields[field] = value
                            break
        
        print(f"  Validating {len(existing_fields)} existing fields: {list(existing_fields.keys())}")
        
        # Run VLM validation
        page_results = validate_with_vlm(page_num, img_data, existing_fields)
        if page_results:
            vlm_results[page_num] = page_results
            found_fields = len([f for f, data in page_results.items() if isinstance(data, dict) and data.get('value') is not None])
            print(f"  [SUCCESS] VLM found {found_fields} fields on Page {page_num}")
        else:
            print(f"  [ERROR] VLM processing failed for Page {page_num}")
    
    # Merge LLM and VLM results
    print(f"\nMerging LLM and VLM results...")
    merged_results = merge_vlm_results(llm_fields, vlm_results)
    
    # Save results
    save_vlm_results(vlm_results, merged_results)
    
    print(f"\n" + "=" * 80)
    print("VLM VALIDATION COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
