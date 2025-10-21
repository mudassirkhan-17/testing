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

    # Create pdf directory if it doesn't exist
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    # Copy all PDF files from uploads to pdf directory
    for filename in os.listdir(uploads_dir):
        if filename.endswith('.pdf'):
            src_path = os.path.join(uploads_dir, filename)
            dst_path = os.path.join(pdf_dir, filename)
            shutil.copy2(src_path, dst_path)
            print(f"Copied {filename} to pdf directory")
            print(f"Source: {src_path}")
            print(f"Destination: {dst_path}")
            print(f"PDF dir exists: {os.path.exists(pdf_dir)}")

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
        # Expected format: {name}_{type}.pdf (e.g., king_property.pdf)
        parts = filename.rsplit('_', 1)
        if len(parts) == 2:
            carrier_name = parts[0]
            insurance_type = parts[1].replace('.pdf', '')

            # Map insurance types to expected format
            type_mapping = {
                'property': 'property',
                'gl': 'general_liability',
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
        # Get form data
        property_name = request.form.get('property_name', 'king').strip()
        gl_name = request.form.get('gl_name', 'king').strip()
        liquor_name = request.form.get('liquor_name', 'king').strip()

        # Handle file uploads
        files_processed = 0

        # Property file
        if 'property_file' in request.files:
            property_file = request.files['property_file']
            if property_file and property_file.filename and allowed_file(property_file.filename):
                filename = secure_filename(property_file.filename)
                # Use the name from input field, default to 'king'
                name_to_use = property_name if property_name else 'king'
                new_filename = f"{name_to_use}_property.pdf"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                property_file.save(file_path)
                files_processed += 1
                flash(f'Property file saved as: {new_filename}')

        # GL file
        if 'gl_file' in request.files:
            gl_file = request.files['gl_file']
            if gl_file and gl_file.filename and allowed_file(gl_file.filename):
                filename = secure_filename(gl_file.filename)
                # Use the name from input field, default to 'king'
                name_to_use = gl_name if gl_name else 'king'
                new_filename = f"{name_to_use}_gl.pdf"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                gl_file.save(file_path)
                files_processed += 1
                flash(f'GL file saved as: {new_filename}')

        # Liquor file
        if 'liquor_file' in request.files:
            liquor_file = request.files['liquor_file']
            if liquor_file and liquor_file.filename and allowed_file(liquor_file.filename):
                filename = secure_filename(liquor_file.filename)
                # Use the name from input field, default to 'king'
                name_to_use = liquor_name if liquor_name else 'king'
                new_filename = f"{name_to_use}_liquor.pdf"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                liquor_file.save(file_path)
                files_processed += 1
                flash(f'Liquor file saved as: {new_filename}')

        if files_processed > 0:
            flash(f'Successfully processed {files_processed} file(s)!')
            # Copy files to pdf directory for multi_carrier_master processing
            copy_files_to_pdf_directory()
            # Run multi_carrier_master pipeline
            pipeline_success = run_multi_carrier_pipeline()
            if pipeline_success:
                flash('✅ Pipeline completed successfully! Check results folder and Google Sheets.')
            else:
                flash('❌ Pipeline failed. Check the logs for details.')
        else:
            flash('No valid PDF files were uploaded.')

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
                    <!-- Property Section -->
                    <div class="form-section property">
                        <h2><span class="insurance-icon"></span>Property Insurance</h2>
                        <div class="form-group">
                            <label for="property_name">Carrier Name (default: king):</label>
                            <input type="text" id="property_name" name="property_name" value="king" placeholder="Enter carrier name">
                        </div>
                        <div class="form-group">
                            <label for="property_file">Upload Property PDF:</label>
                            <div class="file-upload">
                                <input type="file" id="property_file" name="property_file" accept=".pdf" required>
                                <label for="property_file" class="file-upload-label">
                                    Drop your Property Insurance PDF here or click to browse
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- General Liability Section -->
                    <div class="form-section gl">
                        <h2><span class="insurance-icon"></span>General Liability Insurance</h2>
                        <div class="form-group">
                            <label for="gl_name">Carrier Name (default: king):</label>
                            <input type="text" id="gl_name" name="gl_name" value="king" placeholder="Enter carrier name">
                        </div>
                        <div class="form-group">
                            <label for="gl_file">Upload General Liability PDF:</label>
                            <div class="file-upload">
                                <input type="file" id="gl_file" name="gl_file" accept=".pdf" required>
                                <label for="gl_file" class="file-upload-label">
                                    Drop your General Liability PDF here or click to browse
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- Liquor Section -->
                    <div class="form-section liquor">
                        <h2><span class="insurance-icon"></span>Liquor Insurance</h2>
                        <div class="form-group">
                            <label for="liquor_name">Carrier Name (default: king):</label>
                            <input type="text" id="liquor_name" name="liquor_name" value="king" placeholder="Enter carrier name">
                        </div>
                        <div class="form-group">
                            <label for="liquor_file">Upload Liquor PDF:</label>
                            <div class="file-upload">
                                <input type="file" id="liquor_file" name="liquor_file" accept=".pdf" required>
                                <label for="liquor_file" class="file-upload-label">
                                    Drop your Liquor Insurance PDF here or click to browse
                                </label>
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <button type="submit" class="submit-btn">
                            🚀 Upload & Process Documents
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''

    return render_template_string(html_template)

if __name__ == '__main__':
    app.run(debug=True)
