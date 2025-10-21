from flask import Flask, render_template_string, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def copy_files_to_pdf_directory():
    """Copy uploaded files to pdf directory for multi_carrier_master processing"""
    import shutil

    # Use absolute paths to avoid directory issues
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    uploads_dir = os.path.join(current_dir, app.config['UPLOAD_FOLDER'])
    # parent_dir is already the property directory
    pdf_dir = os.path.join(parent_dir, 'pdf')

    print("\n" + "=" * 60)
    print("FILE COPY OPERATION - DEBUG INFO")
    print("=" * 60)
    print(f"🔍 Current dir (app location): {current_dir}")
    print(f"🔍 Parent dir (property folder): {parent_dir}")
    print(f"🔍 Uploads dir: {uploads_dir}")
    print(f"🔍 PDF dir (destination): {pdf_dir}")
    
    # VALIDATION: Make sure pdf_dir is NOT in src folder
    if 'src' in pdf_dir and pdf_dir.endswith(os.path.join('src', 'pdf')):
        print(f"❌ ERROR: PDF dir is in SRC folder! This is WRONG!")
        print(f"   Fixing path...")
        # Recalculate: go up two directories from src
        pdf_dir = os.path.join(os.path.dirname(parent_dir), 'property', 'pdf')
        print(f"   Corrected PDF dir: {pdf_dir}")
    
    print(f"   Uploads dir exists: {os.path.exists(uploads_dir)}")
    print(f"   PDF dir exists: {os.path.exists(pdf_dir)}")
    print("=" * 60)

    # Create pdf directory if it doesn't exist
    if not os.path.exists(pdf_dir):
        print(f"📁 Creating PDF directory: {pdf_dir}")
        os.makedirs(pdf_dir)
    
    print("\n" + "=" * 60)
    print("CLEANING OLD CARRIER FILES FROM PDF DIRECTORY")
    print("=" * 60)

    # STEP 1: Delete old carrier files (any files that match carrier_*.pdf pattern)
    # This ensures we start with a clean slate
    files_to_delete = []
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            # Check if it matches carrier file pattern: {name}_{type}.pdf
            # where type is property, gl, or liquor
            if '_property.pdf' in filename or '_gl.pdf' in filename or '_liquor.pdf' in filename:
                files_to_delete.append(filename)

    # Delete old files
    for filename in files_to_delete:
        filepath = os.path.join(pdf_dir, filename)
        try:
            os.remove(filepath)
            print(f"  🗑️  Deleted old file: {filename}")
        except Exception as e:
            print(f"  ⚠️  Could not delete {filename}: {e}")

    if files_to_delete:
        print(f"✅ Cleaned {len(files_to_delete)} old carrier file(s)")
    else:
        print("ℹ️  No old carrier files to clean")

    print("\n" + "=" * 60)
    print("COPYING NEW FILES TO PDF DIRECTORY")
    print("=" * 60)

    # STEP 2: Copy all NEW PDF files from uploads to pdf directory
    files_copied = 0
    for filename in os.listdir(uploads_dir):
        if filename.endswith('.pdf'):
            src_path = os.path.join(uploads_dir, filename)
            dst_path = os.path.join(pdf_dir, filename)
            shutil.copy2(src_path, dst_path)
            print(f"  ✅ Copied {filename}")
            files_copied += 1

    print(f"✅ Copied {files_copied} new file(s) to pdf directory")
    print("=" * 60)

def run_multi_carrier_pipeline():
    """Run the multi_carrier_master pipeline with uploaded files"""
    try:
        # Get current directory paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        # parent_dir is already the property directory, no need to add 'property' again
        pdf_dir = os.path.join(parent_dir, 'pdf')

        print(f"Current dir: {current_dir}")
        print(f"Parent dir: {parent_dir}")
        print(f"PDF dir: {pdf_dir}")
        print(f"PDF dir exists: {os.path.exists(pdf_dir)}")
        if os.path.exists(pdf_dir):
            print(f"PDF files: {os.listdir(pdf_dir)}")

        # Run from src directory (where pipeline expects to start)
        # The pipeline will handle its own navigation to property/ for results
        current_working_dir = os.getcwd()
        print(f"Flask app running from: {current_working_dir}")
        print(f"Results accessible via ../results: {os.path.exists('../results')}")
        if os.path.exists('../results'):
            results_count = len(os.listdir('../results'))
            print(f"Results directory has {results_count} files")
            # Show a few recent files to verify it's the right directory
            recent_files = sorted(os.listdir('../results'))[-3:]
            print(f"Recent result files: {recent_files}")

        try:
            # Import required functions from multi_carrier_master
            import sys
            sys.path.append(current_dir)  # Add src to path for imports
            from multi_carrier_master import process_carrier_insurance_type

            # Get uploaded files and organize them by carrier and insurance type
            carriers_data = organize_uploaded_files_for_pipeline()

            print(f"DEBUG: carriers_data structure: {carriers_data}")
            if not carriers_data:
                flash('❌ No valid carrier files found in uploads directory.')
                return False

            # Process each carrier using the standard multi_carrier_master approach
            all_results = {}
            insurance_types = ["property", "general_liability", "liquor"]

            for carrier_name, carrier_info in carriers_data.items():
                print(f"\n{'='*60}")
                print(f"PROCESSING CARRIER: {carrier_name}")
                print(f"{'='*60}")

                # Create carrier dict in the exact format expected by multi_carrier_master
                carrier_dict = {
                    'name': carrier_name,
                    'property': carrier_info.get('property', {}),
                    'general_liability': carrier_info.get('general_liability', {}),
                    'liquor': carrier_info.get('liquor', {})
                }

                all_results[carrier_name] = {}

                # Process each insurance type for this carrier (like the main function does)
                for insurance_type in insurance_types:
                    if insurance_type in carrier_info:
                        pdf_info = carrier_info[insurance_type]
                        print(f"\nProcessing {insurance_type} for {carrier_name}...")
                        print(f"DEBUG: carrier_dict keys: {list(carrier_dict.keys())}")
                        print(f"DEBUG: pdf_info: {pdf_info}")

                        result = process_carrier_insurance_type(
                            carrier_dict,
                            insurance_type,
                            pdf_info
                        )
                        all_results[carrier_name][insurance_type] = result
                    else:
                        print(f"\nSkipping {insurance_type} for {carrier_name} (no file uploaded)")
                        all_results[carrier_name][insurance_type] = None

            # Run Phase 4: Google Sheets integration
            from multi_carrier_master import push_master_to_sheets

            # Convert carriers_data to the format expected by push_master_to_sheets
            # It needs full carrier dictionaries with 'name' field
            carriers_for_sheets = []
            for carrier_name, carrier_info in carriers_data.items():
                carrier_dict = {'name': carrier_name}
                carrier_dict.update(carrier_info)  # Add property, gl, liquor data
                carriers_for_sheets.append(carrier_dict)

            sheets_success = push_master_to_sheets(carriers_for_sheets)

            if sheets_success:
                flash('✅ Pipeline completed successfully! Check results folder and Google Sheets.')
                return True
            else:
                flash('❌ Pipeline completed but Google Sheets integration failed.')
                return False

        except Exception as e:
            print(f"Pipeline error: {e}")
            import traceback
            print(traceback.format_exc())
            flash(f'❌ Pipeline failed: {str(e)}')
            return False
        finally:
            # Always return to original directory
            os.chdir(original_dir)

    except Exception as e:
        print(f"Could not setup pipeline: {e}")
        flash('❌ Pipeline not available. Please ensure all dependencies are installed.')
        return False

def organize_uploaded_files_for_pipeline():
    """Organize uploaded files by carrier and insurance type"""
    # Use absolute paths to avoid directory issues
    current_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(current_dir, app.config['UPLOAD_FOLDER'])
    carriers_data = {}

    # Look for files in uploads directory
    if not os.path.exists(uploads_dir):
        print(f"Uploads directory not found: {uploads_dir}")
        return carriers_data

    for filename in os.listdir(uploads_dir):
        if not filename.endswith('.pdf'):
            continue

        # Parse filename to extract carrier name and insurance type
        # Expected format: {carrier_name}_{type}.pdf
        # Types can be: 'property', 'general_liability', 'liquor'
        # So we need to check which type it ends with
        
        if filename.endswith('_property.pdf'):
            carrier_name = filename.replace('_property.pdf', '')
            insurance_type = 'property'
        elif filename.endswith('_general_liability.pdf'):
            carrier_name = filename.replace('_general_liability.pdf', '')
            insurance_type = 'general_liability'
        elif filename.endswith('_liquor.pdf'):
            carrier_name = filename.replace('_liquor.pdf', '')
            insurance_type = 'liquor'
        elif filename.endswith('_gl.pdf'):
            # Also support the old 'gl' format for backward compatibility
            carrier_name = filename.replace('_gl.pdf', '')
            insurance_type = 'general_liability'
        else:
            continue  # Skip files that don't match expected pattern
        
        # Map insurance types to expected format
        type_mapping = {
            'property': 'property',
            'general_liability': 'general_liability',
            'liquor': 'liquor'
        }

        if insurance_type in type_mapping:
            mapped_type = type_mapping[insurance_type]

            if carrier_name not in carriers_data:
                carriers_data[carrier_name] = {}

            # Use absolute path for pdf_path to avoid directory issues
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            # parent_dir is already the property directory
            abs_pdf_path = os.path.join(parent_dir, 'pdf', filename)

            print(f"DEBUG: carrier={carrier_name}, type={mapped_type}, filename={filename}")
            print(f"DEBUG: pdf_path={abs_pdf_path}")
            print(f"DEBUG: pdf file exists? {os.path.exists(abs_pdf_path)}")

            carriers_data[carrier_name][mapped_type] = {
                'pdf_file': filename,
                'pdf_path': abs_pdf_path
            }

    print(f"Found {len(carriers_data)} carrier(s) with uploaded files:")
    for carrier_name, types in carriers_data.items():
        print(f"  {carrier_name}: {list(types.keys())}")

    return carriers_data

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        print("=" * 60)
        print("PROCESSING MULTI-CARRIER UPLOAD")
        print("=" * 60)

        # CLEANUP: Delete old PDF files from uploads first
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        up_dir = os.path.join(cur_dir, app.config['UPLOAD_FOLDER'])
        if os.path.exists(up_dir):
            for fn in os.listdir(up_dir):
                if fn.endswith('.pdf'):
                    try:
                        os.remove(os.path.join(up_dir, fn))
                    except:
                        pass

        # Get all form data and organize by carrier
        carriers_data = {}
        insurance_types = ['property', 'general_liability', 'liquor']
        files_processed = 0

        # Iterate through all carriers in the form
        carrier_index = 0
        while True:
            carrier_name_field = f'carrier_name_{carrier_index}'
            
            # Check if this carrier exists in the form
            if carrier_name_field not in request.form:
                break
            
            carrier_name = request.form.get(carrier_name_field, f'carrier{carrier_index}').strip()
            if not carrier_name:
                carrier_name = f'carrier{carrier_index}'

            print(f"\n{'='*60}")
            print(f"PROCESSING CARRIER {carrier_index + 1}: {carrier_name}")
            print(f"{'='*60}")

            carriers_data[carrier_name] = {}

            # Process each insurance type for this carrier
            for insurance_type in insurance_types:
                # Map insurance type names to form field names
                # 'general_liability' → 'gl', 'property' → 'property', 'liquor' → 'liquor'
                field_type_map = {
                    'property': 'property',
                    'general_liability': 'gl',
                    'liquor': 'liquor'
                }
                form_type = field_type_map.get(insurance_type, insurance_type)
                file_field_name = f'{form_type}_file_{carrier_index}'
                
                if file_field_name in request.files:
                    file = request.files[file_field_name]
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        # Rename with carrier name and insurance type
                        new_filename = f"{carrier_name}_{insurance_type}.pdf"
                        # Use ABSOLUTE path to ensure correct directory
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        file_path = os.path.join(current_dir, app.config['UPLOAD_FOLDER'], new_filename)
                        file.save(file_path)
                        
                        carriers_data[carrier_name][insurance_type] = {
                            'pdf_file': new_filename,
                            'pdf_path': file_path
                        }
                        
                        print(f"  ✅ {insurance_type}: {new_filename} → {file_path}")
                        files_processed += 1
                    else:
                        print(f"  ⏭️  {insurance_type}: Skipped (no file or invalid)")
                        carriers_data[carrier_name][insurance_type] = {}
                else:
                    print(f"  ⏭️  {insurance_type}: Not uploaded")
                    carriers_data[carrier_name][insurance_type] = {}

            carrier_index += 1

        print(f"\n{'='*60}")
        print(f"UPLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"Total Carriers: {len(carriers_data)}")
        print(f"Total Files Processed: {files_processed}")
        print(f"Carriers Data: {carriers_data}")
        print(f"Request.files keys: {request.files.keys()}") # Added debugging

        if files_processed > 0:
            flash(f'✅ Successfully processed {files_processed} file(s) from {len(carriers_data)} carrier(s)!')
            # Copy files to pdf directory for multi_carrier_master processing
            copy_files_to_pdf_directory()
            # Run multi_carrier_master pipeline
            pipeline_success = run_multi_carrier_pipeline()
            if pipeline_success:
                flash('✅ Pipeline completed successfully! Check results folder and Google Sheets.')
            else:
                flash('❌ Pipeline failed. Check the logs for details.')
        else:
            flash('❌ No valid PDF files were uploaded.')

        return redirect(url_for('upload_files'))

    # HTML template
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Insurance Document Upload</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }

            .container {
                max-width: 900px;
                width: 100%;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                backdrop-filter: blur(10px);
            }

            .header {
                background: linear-gradient(135deg, #2c3e50, #3498db);
                color: white;
                padding: 30px;
                text-align: center;
            }

            .header h1 {
                font-size: 2.5rem;
                font-weight: 300;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }

            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
            }

            .form-container {
                padding: 40px;
            }

            .form-section {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin: 20px 0;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
                border-left: 5px solid;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }

            .form-section:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            }

            .form-section.property { border-left-color: #e74c3c; }
            .form-section.gl { border-left-color: #f39c12; }
            .form-section.liquor { border-left-color: #9b59b6; }

            .form-section h2 {
                font-size: 1.5rem;
                margin-bottom: 20px;
                color: #2c3e50;
                display: flex;
                align-items: center;
            }

            .form-section h2::before {
                content: '';
                width: 4px;
                height: 20px;
                background: inherit;
                margin-right: 10px;
                border-radius: 2px;
            }

            .form-group {
                margin: 20px 0;
            }

            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #34495e;
                font-size: 0.95rem;
            }

            input[type="text"] {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s ease, box-shadow 0.3s ease;
                background: #f8f9fa;
            }

            input[type="text"]:focus {
                outline: none;
                border-color: #3498db;
                box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
                background: white;
            }

            .file-upload {
                position: relative;
                display: inline-block;
                width: 100%;
            }

            .file-upload input[type="file"] {
                position: absolute;
                opacity: 0;
                width: 100%;
                height: 100%;
                cursor: pointer;
            }

            .file-upload-label {
                display: block;
                padding: 12px 16px;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                background: #f8f9fa;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
                font-size: 16px;
                color: #7f8c8d;
            }

            .file-upload-label:hover {
                border-color: #3498db;
                background: #ecf0f1;
                color: #2c3e50;
            }

            .file-upload-label::before {
                content: '📎 ';
                font-size: 1.2em;
            }

            .submit-btn {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 25px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                width: 100%;
                margin-top: 30px;
            }

            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            }

            .submit-btn:active {
                transform: translateY(0);
            }

            .flash-messages {
                margin: 20px 0;
                padding: 15px 20px;
                border-radius: 8px;
                font-weight: 500;
            }

            .flash-success {
                background: linear-gradient(135deg, #2ecc71, #27ae60);
                color: white;
                border: 1px solid rgba(46, 204, 113, 0.3);
                box-shadow: 0 4px 15px rgba(46, 204, 113, 0.2);
            }

            .flash-error {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                color: white;
                border: 1px solid rgba(231, 76, 60, 0.3);
                box-shadow: 0 4px 15px rgba(231, 76, 60, 0.2);
            }

            .success-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #2ecc71, #27ae60);
                color: white;
                padding: 15px 25px;
                border-radius: 50px;
                box-shadow: 0 4px 20px rgba(46, 204, 113, 0.3);
                animation: slideIn 0.5s ease-out;
                z-index: 1000;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            .insurance-icon {
                font-size: 1.5rem;
                margin-right: 10px;
            }

            .property .insurance-icon::before { content: '🏠'; }
            .gl .insurance-icon::before { content: '🛡️'; }
            .liquor .insurance-icon::before { content: '🍷'; }

            .carriers-container {
                margin: 20px 0;
            }

            .carrier-block {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 15px;
                padding: 30px;
                margin: 20px 0;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                position: relative;
            }

            .carrier-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 2px solid rgba(0, 0, 0, 0.1);
            }

            .carrier-title {
                font-size: 1.8rem;
                font-weight: 600;
                color: #2c3e50;
                margin: 0;
            }

            .remove-carrier-btn {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }

            .remove-carrier-btn:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(231, 76, 60, 0.4);
            }

            .add-carrier-btn {
                background: linear-gradient(135deg, #2ecc71, #27ae60);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                width: 100%;
                margin: 20px 0;
            }

            .add-carrier-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(46, 204, 113, 0.4);
            }

            .carrier-name-input-wrapper {
                margin-bottom: 20px;
            }

            .carrier-name-input-wrapper label {
                font-weight: 700;
                color: #2c3e50;
            }

            .carrier-name-input-wrapper input {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #3498db;
                border-radius: 8px;
                font-size: 16px;
                background: white;
                font-weight: 600;
            }

            .file-status {
                position: absolute;
                top: 0;
                left: 0;
                padding: 8px 12px;
                background-color: #e0f2f7;
                color: #3498db;
                border-bottom-right-radius: 8px;
                font-size: 0.85em;
                font-weight: 600;
                z-index: 1;
                display: none; /* Hidden by default */
            }

            .file-status.active {
                margin-top: 10px;
                padding: 12px 16px;
                background: linear-gradient(135deg, #e8f8f5 0%, #d5f4e6 100%);
                border-left: 4px solid #27ae60;
                border-radius: 8px;
                display: flex !important;
                justify-content: space-between;
                align-items: center;
                position: relative;
            }

            .file-info {
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
            }

            .file-icon {
                font-size: 1.3em;
            }

            .file-details {
                display: flex;
                flex-direction: column;
                gap: 2px;
            }

            .file-name {
                font-weight: 700;
                color: #27ae60;
                font-size: 0.95em;
            }

            .file-size {
                font-size: 0.8em;
                color: #7f8c8d;
            }

            .cancel-file-btn {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.85em;
                transition: all 0.3s ease;
                white-space: nowrap;
                margin-left: 10px;
            }

            .cancel-file-btn:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Insurance Document Upload</h1>
                <p>Upload your insurance documents for automated processing</p>
            </div>

            <div class="form-container">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="flash-messages flash-{{ 'success' if category == 'message' else 'error' }}">
                                {{ message }}
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                <form method="post" enctype="multipart/form-data">
                    <div class="carriers-container" id="carriersContainer">
                        <!-- Carrier 1 (default) -->
                        <div class="carrier-block" data-carrier-index="0">
                            <div class="carrier-header">
                                <h2 class="carrier-title">📦 Carrier #1</h2>
                                <button type="button" class="remove-carrier-btn" onclick="removeCarrier(0)" style="display: none;">✕ Remove</button>
                            </div>

                            <div class="carrier-name-input-wrapper">
                                <label for="carrier_name_0">Carrier Name:</label>
                                <input type="text" id="carrier_name_0" name="carrier_name_0" value="king" placeholder="Enter carrier name" required>
                            </div>

                            <!-- Property Insurance -->
                            <div class="form-section property">
                                <h3><span class="insurance-icon"></span>Property Insurance</h3>
                                <div class="form-group">
                                    <label for="property_file_0">Upload Property PDF:</label>
                                    <div class="file-upload">
                                        <input type="file" id="property_file_0" name="property_file_0" accept=".pdf" onchange="updateFileStatus(0, 'property')">
                                        <label for="property_file_0" class="file-upload-label">
                                            📁 Drop your Property Insurance PDF here or click to browse
                                        </label>
                                    </div>
                                    <div id="property_file_status_0" class="file-status" style="display: none;">
                                        <span class="file-info">
                                            <span class="file-icon">📁</span>
                                            <span class="file-details">
                                                <span class="file-name">No file selected</span>
                                                <span class="file-size">0 bytes</span>
                                            </span>
                                        </span>
                                        <button type="button" class="cancel-file-btn" onclick="clearFileInput(0, 'property')">✗</button>
                                    </div>
                                </div>
                            </div>

                            <!-- General Liability Insurance -->
                            <div class="form-section gl">
                                <h3><span class="insurance-icon"></span>General Liability Insurance</h3>
                                <div class="form-group">
                                    <label for="gl_file_0">Upload General Liability PDF:</label>
                                    <div class="file-upload">
                                        <input type="file" id="gl_file_0" name="gl_file_0" accept=".pdf" onchange="updateFileStatus(0, 'general_liability')">
                                        <label for="gl_file_0" class="file-upload-label">
                                            📁 Drop your General Liability PDF here or click to browse
                                        </label>
                                    </div>
                                    <div id="gl_file_status_0" class="file-status" style="display: none;">
                                        <span class="file-info">
                                            <span class="file-icon">📁</span>
                                            <span class="file-details">
                                                <span class="file-name">No file selected</span>
                                                <span class="file-size">0 bytes</span>
                                            </span>
                                        </span>
                                        <button type="button" class="cancel-file-btn" onclick="clearFileInput(0, 'general_liability')">✗</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Liquor Insurance -->
                            <div class="form-section liquor">
                                <h3><span class="insurance-icon"></span>Liquor Insurance</h3>
                                <div class="form-group">
                                    <label for="liquor_file_0">Upload Liquor PDF:</label>
                                    <div class="file-upload">
                                        <input type="file" id="liquor_file_0" name="liquor_file_0" accept=".pdf" onchange="updateFileStatus(0, 'liquor')">
                                        <label for="liquor_file_0" class="file-upload-label">
                                            📁 Drop your Liquor Insurance PDF here or click to browse
                                        </label>
                                    </div>
                                    <div id="liquor_file_status_0" class="file-status" style="display: none;">
                                        <span class="file-info">
                                            <span class="file-icon">📁</span>
                                            <span class="file-details">
                                                <span class="file-name">No file selected</span>
                                                <span class="file-size">0 bytes</span>
                                            </span>
                                        </span>
                                        <button type="button" class="cancel-file-btn" onclick="clearFileInput(0, 'liquor')">✗</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <button type="button" class="add-carrier-btn" onclick="addCarrier()">➕ Add Another Carrier</button>

                    <div class="form-group">
                        <button type="submit" class="submit-btn">
                            🚀 Upload & Process All Carriers
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            function addCarrier() {
                const carriersContainer = document.getElementById('carriersContainer');
                const carrierIndex = carriersContainer.children.length;

                const newCarrierBlock = document.createElement('div');
                newCarrierBlock.className = 'carrier-block';
                newCarrierBlock.setAttribute('data-carrier-index', carrierIndex);

                newCarrierBlock.innerHTML = `
                    <div class="carrier-header">
                        <h2 class="carrier-title">📦 Carrier #${carrierIndex + 1}</h2>
                        <button type="button" class="remove-carrier-btn" onclick="removeCarrier(${carrierIndex})">✕ Remove</button>
                    </div>

                    <div class="carrier-name-input-wrapper">
                        <label for="carrier_name_${carrierIndex}">Carrier Name:</label>
                        <input type="text" id="carrier_name_${carrierIndex}" name="carrier_name_${carrierIndex}" value="king" placeholder="Enter carrier name" required>
                    </div>

                    <!-- Property Insurance -->
                    <div class="form-section property">
                        <h3><span class="insurance-icon"></span>Property Insurance</h3>
                        <div class="form-group">
                            <label for="property_file_${carrierIndex}">Upload Property PDF:</label>
                            <div class="file-upload">
                                <input type="file" id="property_file_${carrierIndex}" name="property_file_${carrierIndex}" accept=".pdf" onchange="updateFileStatus(${carrierIndex}, 'property')">
                                <label for="property_file_${carrierIndex}" class="file-upload-label">
                                    Drop your Property Insurance PDF here or click to browse
                                </label>
                            </div>
                            <div id="property_file_status_${carrierIndex}" class="file-status" style="display: none;">
                                <span class="file-info">
                                    <span class="file-icon">📁</span>
                                    <span class="file-details">
                                        <span class="file-name">No file selected</span>
                                        <span class="file-size">0 bytes</span>
                                    </span>
                                </span>
                                <button type="button" class="cancel-file-btn" onclick="clearFileInput(${carrierIndex}, 'property')">✗</button>
                            </div>
                        </div>
                    </div>

                    <!-- General Liability Insurance -->
                    <div class="form-section gl">
                        <h3><span class="insurance-icon"></span>General Liability Insurance</h3>
                        <div class="form-group">
                            <label for="gl_file_${carrierIndex}">Upload General Liability PDF:</label>
                            <div class="file-upload">
                                <input type="file" id="gl_file_${carrierIndex}" name="gl_file_${carrierIndex}" accept=".pdf" onchange="updateFileStatus(${carrierIndex}, 'general_liability')">
                                <label for="gl_file_${carrierIndex}" class="file-upload-label">
                                    Drop your General Liability PDF here or click to browse
                                </label>
                            </div>
                            <div id="gl_file_status_${carrierIndex}" class="file-status" style="display: none;">
                                <span class="file-info">
                                    <span class="file-icon">📁</span>
                                    <span class="file-details">
                                        <span class="file-name">No file selected</span>
                                        <span class="file-size">0 bytes</span>
                                    </span>
                                </span>
                                <button type="button" class="cancel-file-btn" onclick="clearFileInput(${carrierIndex}, 'general_liability')">✗</button>
                            </div>
                        </div>
                    </div>

                    <!-- Liquor Insurance -->
                    <div class="form-section liquor">
                        <h3><span class="insurance-icon"></span>Liquor Insurance</h3>
                        <div class="form-group">
                            <label for="liquor_file_${carrierIndex}">Upload Liquor PDF:</label>
                            <div class="file-upload">
                                <input type="file" id="liquor_file_${carrierIndex}" name="liquor_file_${carrierIndex}" accept=".pdf" onchange="updateFileStatus(${carrierIndex}, 'liquor')">
                                <label for="liquor_file_${carrierIndex}" class="file-upload-label">
                                    Drop your Liquor Insurance PDF here or click to browse
                                </label>
                            </div>
                            <div id="liquor_file_status_${carrierIndex}" class="file-status" style="display: none;">
                                <span class="file-info">
                                    <span class="file-icon">📁</span>
                                    <span class="file-details">
                                        <span class="file-name">No file selected</span>
                                        <span class="file-size">0 bytes</span>
                                    </span>
                                </span>
                                <button type="button" class="cancel-file-btn" onclick="clearFileInput(${carrierIndex}, 'liquor')">✗</button>
                            </div>
                        </div>
                    </div>
                `;

                carriersContainer.appendChild(newCarrierBlock);
                // Show remove button for the new carrier
                newCarrierBlock.querySelector('.remove-carrier-btn').style.display = 'block';
            }

            function removeCarrier(index) {
                const carriersContainer = document.getElementById('carriersContainer');
                const carrierBlock = carriersContainer.children[index];
                carrierBlock.remove();

                // Re-index carrier blocks
                carriersContainer.children.forEach((block, i) => {
                    block.setAttribute('data-carrier-index', i);
                    // Update carrier name inputs
                    const carrierNameInput = block.querySelector(`input[name^="carrier_name_"]`);
                    if (carrierNameInput) {
                        carrierNameInput.id = `carrier_name_${i}`;
                        carrierNameInput.name = `carrier_name_${i}`;
                    }
                    // Update file inputs
                    const propertyFileInput = block.querySelector(`input[name^="property_file_"]`);
                    if (propertyFileInput) {
                        propertyFileInput.id = `property_file_${i}`;
                        propertyFileInput.name = `property_file_${i}`;
                    }
                    const glFileInput = block.querySelector(`input[name^="gl_file_"]`);
                    if (glFileInput) {
                        glFileInput.id = `gl_file_${i}`;
                        glFileInput.name = `gl_file_${i}`;
                    }
                    const liquorFileInput = block.querySelector(`input[name^="liquor_file_"]`);
                    if (liquorFileInput) {
                        liquorFileInput.id = `liquor_file_${i}`;
                        liquorFileInput.name = `liquor_file_${i}`;
                    }
                    // Update file status divs
                    const propertyStatusDiv = block.querySelector(`#property_file_status_${i}`);
                    if (propertyStatusDiv) {
                        propertyStatusDiv.style.display = 'none';
                    }
                    const glStatusDiv = block.querySelector(`#gl_file_status_${i}`);
                    if (glStatusDiv) {
                        glStatusDiv.style.display = 'none';
                    }
                    const liquorStatusDiv = block.querySelector(`#liquor_file_status_${i}`);
                    if (liquorStatusDiv) {
                        liquorStatusDiv.style.display = 'none';
                    }
                    // Update remove button
                    const removeBtn = block.querySelector('.remove-carrier-btn');
                    if (removeBtn) {
                        removeBtn.onclick = () => removeCarrier(i);
                        removeBtn.setAttribute('onclick', `removeCarrier(${i})`);
                    }
                });
            }

            function updateFileStatus(carrierIndex, insuranceType) {
                // Map general_liability to gl for form field names
                const fieldMap = {'property': 'property', 'general_liability': 'gl', 'liquor': 'liquor'};
                const fieldType = fieldMap[insuranceType] || insuranceType;
                
                const fileInput = document.getElementById(`${fieldType}_file_${carrierIndex}`);
                const statusDiv = document.getElementById(`${fieldType}_file_status_${carrierIndex}`);
                
                if (fileInput && fileInput.files && fileInput.files.length > 0) {
                    const file = fileInput.files[0];
                    const fileSize = (file.size / 1024).toFixed(2);
                    statusDiv.innerHTML = `<div class="file-info"><span class="file-icon">✅</span><div class="file-details"><span class="file-name">${file.name}</span><span class="file-size">${fileSize} KB</span></div></div><button type="button" class="cancel-file-btn" onclick="clearFileInput(${carrierIndex}, '${insuranceType}')">✕ Clear</button>`;
                    statusDiv.classList.add('active');
                } else if (statusDiv) {
                    statusDiv.innerHTML = '';
                    statusDiv.classList.remove('active');
                }
            }

            function clearFileInput(carrierIndex, insuranceType) {
                // Map general_liability to gl
                const fieldMap = {'property': 'property', 'general_liability': 'gl', 'liquor': 'liquor'};
                const fieldType = fieldMap[insuranceType] || insuranceType;
                
                const fileInput = document.getElementById(`${fieldType}_file_${carrierIndex}`);
                if (fileInput) fileInput.value = '';
                
                const statusDiv = document.getElementById(`${fieldType}_file_status_${carrierIndex}`);
                if (statusDiv) {
                    statusDiv.innerHTML = '';
                    statusDiv.classList.remove('active');
                }
            }
        </script>
    </body>
    </html>
    '''

    return render_template_string(html_template)

if __name__ == '__main__':
    app.run(debug=True)
