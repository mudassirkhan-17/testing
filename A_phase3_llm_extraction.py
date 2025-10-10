import json
import openai
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def read_combined_file():
    """Read the intelligent combined file from Phase 2D"""
    combined_file = "intelligent_combined_all_pages.txt"
    
    if not os.path.exists(combined_file):
        print("Error: Intelligent combined file not found!")
        print("Please run Phase 2D first to generate intelligent_combined_all_pages.txt")
        return []
    
    print(f"Reading intelligent combined file: {combined_file}")
    
    with open(combined_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract all pages
    all_pages = []
    page_sections = re.findall(r'PAGE (\d+) \((PyMuPDF|OCR) \(.*?\)\):.*?TEXT CONTENT:.*?------------------------------\n(.*?)\n={80}', content, re.DOTALL)
    
    for page_num, source, page_text in page_sections:
        all_pages.append({
            'page_num': int(page_num),
            'source': source,
            'text': page_text.strip()
        })
    
    # Sort by page number
    all_pages.sort(key=lambda x: x['page_num'])
    
    print(f"Extracted {len(all_pages)} pages from combined file")
    for page in all_pages:
        print(f"  Page {page['page_num']:2d} ({page['source']:8s}): {len(page['text']):5,} chars")
    
    return all_pages

def create_chunks(all_pages, chunk_size=4):
    """Split pages into chunks of 4 pages each"""
    chunks = []
    
    for i in range(0, len(all_pages), chunk_size):
        chunk_pages = all_pages[i:i+chunk_size]
        
        # Combine text from all pages in this chunk
        chunk_text = ""
        page_nums = []
        sources = []
        
        for page in chunk_pages:
            chunk_text += f"=== PAGE {page['page_num']} ({page['source']}) ===\n"
            chunk_text += page['text'] + "\n\n"
            page_nums.append(page['page_num'])
            sources.append(page['source'])
        
        chunks.append({
            'chunk_num': len(chunks) + 1,
            'pages': chunk_pages,
            'page_nums': page_nums,
            'sources': sources,
            'text': chunk_text.strip(),
            'char_count': len(chunk_text)
        })
    
    print(f"\nCreated {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  Chunk {chunk['chunk_num']}: Pages {chunk['page_nums']} ({chunk['char_count']:,} chars)")
    
    return chunks

def extract_with_llm(chunk, chunk_num, total_chunks):
    """Extract information using LLM with your exact prompt"""
    
    prompt = f"""
    Analyze the following insurance document text and extract ONLY the 31 specific property coverage fields listed below.
    
    CRITICAL: Extract ONLY these 31 fields. Do NOT create new field names or extract any other information.
    
    THE 31 SPECIFIC FIELDS TO EXTRACT (with examples of what to look for):
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
    
    EXTRACTION RULES:
    - Extract EXACTLY as written in the document
    - Look for SIMILAR PATTERNS even if exact examples don't match
    - For Construction Type: Look for any construction type mentioned (Frame, Masonry, Brick, etc.)
    - For Valuation: Look for any valuation method (Replacement Cost, Actual Cash Value, etc.) with percentages
    - For Dollar Amounts: Look for any dollar amounts ($X,XXX, $X,XXX.XX, $XXX,XXX)
    - For Percentages: Look for any percentages (X%, X.X%)
    - For Deductibles: Look for "Deductible", "Ded", "Min", "Per" with amounts
    - For Sublimits: Look for "Sublimit", "Limit", "Max" with amounts
    - For Coverage Status: Look for "Included", "Excluded", "Not Offered", "Not offered", "Coverage not required"
    - For Business Income: Look for amounts with time periods like "(1/6)", "(1/3)", "per month"
    - For Multi-line Values: Extract everything related to that field, preserve line breaks
    - For Complex Values: Extract the complete text block for that field
    - If field is not found, set to null
    - Do NOT hallucinate or make up values
    - Do NOT combine or modify existing values
    - If you see variations not in examples, still extract them exactly as written
    - Look for field names even if they're worded differently (e.g., "Wind/Hail" instead of "Windstorm or Hail")
    - Do NOT extract administrative, financial, or policy information
    - Do NOT create new field names
    - Do NOT extract premium finance agreements, policy numbers, or legal disclosures
    
    IMPORTANT: This is chunk {chunk_num} of {total_chunks}. This chunk contains pages {chunk['page_nums']}. 
    
    For each field you find, look for the nearest page number in the text above it (e.g., "Page 3", "Page 5"). 
    Use the actual page number from the text. Multiple fields can be on the same page.
    
    CRITICAL: Return ONLY valid JSON with this exact format:
    {{
        "Construction Type": {{"value": "FRAME", "page": 5}},
        "Building": {{"value": "$500,000", "page": 5}},
        "Theft Sublimit": {{"value": "$10,000", "page": 6}},
        "Minimum Earned Premium (MEP)": {{"value": "25%", "page": 3}},
        // ... other fields
    }}
    
    PAGE DETECTION RULES:
    - Look for "Page X" markers in the text above each field
    - Use the nearest page number found above the field
    - If no page number found, use null for page
    - Multiple fields can share the same page number
    - Extract the actual page number from the text (e.g., "Page 3" = page 3)
    
    If a field is not found, use: {{"value": null, "page": null}}
    Do not provide explanations, context, or any text outside the JSON object.
    
    Document text:
    {chunk['text']}
    """
    
    try:
        print(f"  Processing chunk {chunk_num} with LLM (Pages {chunk['page_nums']})...")
        
        # Use OpenAI API (new format)
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a JSON extraction tool. Return ONLY valid JSON. Do not provide explanations, context, or any text outside the JSON object."},
                {"role": "user", "content": prompt}
            ],
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Check if response is empty
        if not result_text:
            print(f"  [ERROR] Empty response from LLM")
            return {'_metadata': {'chunk_num': chunk_num, 'page_nums': chunk['page_nums'], 'error': 'Empty LLM response'}}
        
        # Clean up markdown code blocks if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]  # Remove ```json
        if result_text.startswith('```'):
            result_text = result_text[3:]   # Remove ```
        if result_text.endswith('```'):
            result_text = result_text[:-3]  # Remove trailing ```
        result_text = result_text.strip()
        
        # Try to parse JSON
        try:
            result_json = json.loads(result_text)
            
            # Convert new format to old format for compatibility
            converted_json = {}
            individual_page_fields = {}
            
            for field, data in result_json.items():
                if isinstance(data, dict) and 'value' in data and 'page' in data:
                    # New format: {"value": "FRAME", "page": 5}
                    converted_json[field] = data['value']
                    if data['value'] is not None and data['page'] is not None:
                        individual_page_fields[field] = [data['page']]
                        print(f"    Found {field} on Page {data['page']}")
                else:
                    # Old format: direct value
                    converted_json[field] = data
            
            # Add metadata
            converted_json['_metadata'] = {
                'chunk_num': chunk_num,
                'page_nums': chunk['page_nums'],
                'sources': chunk['sources'],
                'char_count': chunk['char_count'],
                'individual_page_fields': individual_page_fields
            }
            
            found_fields = len([k for k, v in converted_json.items() if v is not None and k != '_metadata'])
            print(f"  [SUCCESS] Extracted {found_fields} fields from pages {chunk['page_nums']}")
            return converted_json
            
        except json.JSONDecodeError as e:
            print(f"  [ERROR] Failed to parse JSON response")
            print(f"  Raw LLM response: {result_text[:200]}...")
            return {'_metadata': {'chunk_num': chunk_num, 'page_nums': chunk['page_nums'], 'error': f'JSON parse failed: {str(e)}'}}
            
    except Exception as e:
        print(f"  [ERROR] LLM processing failed: {e}")
        return {'_metadata': {'chunk_num': chunk_num, 'page_nums': chunk['page_nums'], 'error': str(e)}}

def merge_extraction_results(all_results):
    """Merge results from all chunks, prioritizing non-null values"""
    
    # Define the expected fields
    expected_fields = [
        "Construction Type", "Valuation and Coinsurance", "Cosmetic Damage", "Building",
        "Pumps", "Canopy", "ROOF EXCLUSION", "Roof Surfacing", "Roof Surfacing -Limitation",
        "Business Personal Property", "Business Income", "Business Income with Extra Expense",
        "Equipment Breakdown", "Outdoor Signs", "Signs Within 1,000 Feet to Premises",
        "Employee Dishonesty", "Money & Securities", "Money and Securities (Inside; Outside)",
        "Spoilage", "Theft", "Theft Sublimit", "Theft Deductible", "Windstorm or Hail",
        "Named Storm Deductible", "Wind and Hail and Named Storm exclusion",
        "All Other Perils Deductible", "Fire Station Alarm", "Burglar Alarm", "Terrorism",
        "Protective Safeguards Requirements", "Minimum Earned Premium (MEP)"
    ]
    
    merged_result = {}
    
    # Initialize all expected fields as null
    for field in expected_fields:
        merged_result[field] = None
    
    # Collect all unique fields found by LLM
    all_found_fields = set()
    for chunk_result in all_results:
        if '_metadata' in chunk_result and 'error' not in chunk_result['_metadata']:
            for field in chunk_result.keys():
                if field != '_metadata':
                    all_found_fields.add(field)
    
    # Add any new fields found by LLM
    for field in all_found_fields:
        if field not in merged_result:
            merged_result[field] = None
    
    # Track which specific page each field was found on
    field_sources = {}
    
    # Merge results from all chunks
    for chunk_result in all_results:
        if '_metadata' in chunk_result and 'error' in chunk_result['_metadata']:
            continue  # Skip failed chunks
            
        chunk_pages = chunk_result['_metadata']['page_nums']
        
        for field, value in chunk_result.items():
            if field == '_metadata':
                continue
                
            if value is not None and value != "" and value != "null":
                # If field already has a value, keep the first non-null one
                if merged_result[field] is None:
                    merged_result[field] = value
                    # Store the specific page where this field was found
                    # For now, use the first page of the chunk, but this should be more precise
                    field_sources[field] = [chunk_pages[0]] if chunk_pages else []
                else:
                    # If we have multiple values, note the conflict
                    if merged_result[field] != value:
                        print(f"  Multiple values found for {field}: '{merged_result[field]}' (pages {field_sources[field]}) and '{value}' (pages {chunk_pages})")
    
    # Add source information to merged result
    merged_result['_extraction_summary'] = {
        'total_chunks_processed': len(all_results),
        'successful_chunks': len([r for r in all_results if '_metadata' in r and 'error' not in r['_metadata']]),
        'field_sources': field_sources
    }
    
    return merged_result

def save_extraction_results(merged_result, all_chunk_results):
    """Save extraction results to files"""
    # Save final merged results (overwrite existing)
    final_file = "extracted_insurance_fields.json"
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(merged_result, f, indent=2, ensure_ascii=False)
    
    # Save detailed chunk results (overwrite existing)
    detailed_file = "extraction_chunks.json"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunk_results, f, indent=2, ensure_ascii=False)
    
    # Save summary report (overwrite existing)
    report_file = "extraction_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("INSURANCE FIELD EXTRACTION REPORT - STEP 2\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Chunks Processed: {len(all_chunk_results)}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("EXTRACTED FIELDS:\n")
        f.write("-" * 30 + "\n")
        found_fields = 0
        for field, value in merged_result.items():
            if field.startswith('_'):
                continue
            if value is not None:
                found_fields += 1
                source_pages = merged_result['_extraction_summary']['field_sources'].get(field, [])
                f.write(f"{field}: {value} (Pages: {source_pages})\n")
        
        f.write(f"\nSUMMARY:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Fields Found: {found_fields}/{len([f for f in merged_result.keys() if not f.startswith('_')])}\n")
        f.write(f"Success Rate: {found_fields/len([f for f in merged_result.keys() if not f.startswith('_')])*100:.1f}%\n")
    
    return final_file, detailed_file, report_file

def generate_summary(merged_result):
    """Generate console summary"""
    print(f"\n{'='*80}")
    print("STEP 2 SUMMARY - LLM EXTRACTION")
    print(f"{'='*80}")
    
    found_fields = [k for k, v in merged_result.items() if v is not None and not k.startswith('_')]
    total_fields = len([k for k in merged_result.keys() if not k.startswith('_')])
    
    print(f"Total Fields: {total_fields}")
    print(f"Fields Found: {len(found_fields)}")
    print(f"Success Rate: {len(found_fields)/total_fields*100:.1f}%")
    
    if found_fields:
        print(f"\n[SUCCESS] Fields Successfully Extracted:")
        for field in found_fields:
            source_pages = merged_result['_extraction_summary']['field_sources'].get(field, [])
            print(f"  - {field}: {merged_result[field]} (Pages: {source_pages})")
    
    missing_fields = [k for k, v in merged_result.items() if v is None and not k.startswith('_')]
    if missing_fields:
        print(f"\n[MISSING] Fields Not Found:")
        for field in missing_fields:
            print(f"  - {field}")

def create_final_validated_fields(merged_result):
    """Create final_validated_fields.json without VLM validation"""
    final_fields = {}
    
    # Get page sources from extraction summary
    field_sources = merged_result.get('_extraction_summary', {}).get('field_sources', {})
    
    # Manual corrections for known page locations
    page_corrections = {
        "Minimum Earned Premium (MEP)": "Page 3",
        "Terrorism": "Page 3"
    }
    
    for field_name, llm_value in merged_result.items():
        if not field_name.startswith('_'):  # Skip metadata fields
            # Get page numbers where this field was found
            source_pages = field_sources.get(field_name, [])
            
            # Use manual correction if available, otherwise use extracted page
            if field_name in page_corrections:
                page_info = page_corrections[field_name]
            else:
                page_info = f"Page {source_pages[0]}" if source_pages else ""
            
            final_fields[field_name] = {
                "llm_value": llm_value,
                "vlm_value": None,  # No VLM validation
                "final_value": llm_value,  # Use LLM value as final
                "confidence": "llm_only",  # Only LLM confidence
                "source_page": page_info  # Add page information
            }
    
    # Save to file
    with open('final_validated_fields.json', 'w', encoding='utf-8') as f:
        json.dump(final_fields, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INFO] Created final_validated_fields.json with LLM-only results")
    print(f"[INFO] VLM validation skipped to save costs")
    print(f"[INFO] Page information included for each field")
    print(f"[INFO] Applied manual page corrections for known fields")

if __name__ == "__main__":
    # Set OpenAI API key
    # Set OpenAI API key from environment
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai.api_key:
        print("Error: OPENAI_API_KEY not found in environment variables!")
        print("Please set your OpenAI API key in the .env file")
        exit(1)
    
    print("STEP 2: LLM INFORMATION EXTRACTION")
    print("=" * 80)
    
    # Read combined file
    all_pages = read_combined_file()
    if not all_pages:
        exit(1)
    
    # Create chunks (4 pages each)
    chunks = create_chunks(all_pages, chunk_size=4)
    
    # Process each chunk with LLM
    all_results = []
    for chunk in chunks:
        print(f"\nProcessing Chunk {chunk['chunk_num']}/{len(chunks)}...")
        result = extract_with_llm(chunk, chunk['chunk_num'], len(chunks))
        all_results.append(result)
    
    # Merge all results
    print(f"\nMerging results from {len(all_results)} chunks...")
    merged_result = merge_extraction_results(all_results)
    
    # Save results
    final_file, detailed_file, report_file = save_extraction_results(merged_result, all_results)
    
    # Generate summary
    generate_summary(merged_result)
    
    # Create final_validated_fields.json (without VLM validation)
    create_final_validated_fields(merged_result)
    
    print(f"\n{'='*80}")
    print("FILES GENERATED:")
    print(f"{'='*80}")
    print(f"Final extraction: {final_file}")
    print(f"Detailed chunks: {detailed_file}")
    print(f"Extraction report: {report_file}")
    print(f"Final validated fields: final_validated_fields.json")
    print(f"\nStep 2 complete! Insurance field extraction finished.")
