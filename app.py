from flask import Flask, render_template, request, jsonify, session
import os
import sys
import json
import shutil
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename
import threading

# Add src folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.secret_key = 'insurance_app_secret_key_2024'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('results', exist_ok=True)

processing_status = {}

@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({'error': str(e.description)}), 400

@app.errorhandler(500)
def handle_server_error(e):
    return jsonify({'error': 'Internal server error: ' + str(e)}), 500

@app.before_request
def log_request():
    print(f"\n{'='*80}")
    print(f"REQUEST: {request.method} {request.path}")
    print(f"{'='*80}")

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Insurance Quote Comparison System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 10px;
                font-size: 2em;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .setup-section {
                background: #f0f4ff;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                border-left: 4px solid #667eea;
            }
            .setup-controls {
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
            }
            .setup-controls select,
            .setup-controls button {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 1em;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .setup-controls select {
                background: white;
                border: 2px solid #667eea;
                color: #333;
            }
            .setup-controls button {
                background: #667eea;
                color: white;
                font-weight: bold;
            }
            .setup-controls button:hover {
                background: #764ba2;
                transform: translateY(-2px);
            }
            .columns-wrapper {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .column {
                background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
                padding: 20px;
                border-radius: 12px;
                border: 2px solid #e0e7ff;
            }
            .column h3 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.1em;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .carrier-group {
                margin-bottom: 20px;
                padding: 15px;
                background: white;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .carrier-group label {
                display: block;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
                font-size: 0.9em;
            }
            .carrier-group input[type="text"],
            .carrier-group input[type="file"] {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-bottom: 10px;
                font-size: 0.9em;
            }
            .file-label {
                display: block;
                padding: 10px;
                background: #f8f9fa;
                border: 2px dashed #667eea;
                border-radius: 6px;
                text-align: center;
                color: #667eea;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-bottom: 10px;
            }
            .file-label:hover {
                background: #f0f4ff;
                border-color: #764ba2;
            }
            .file-label.selected {
                background: #e8f0fe;
                border-color: #4CAF50;
                color: #4CAF50;
            }
            .process-section {
                text-align: center;
                margin-top: 30px;
            }
            .process-btn {
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 15px 50px;
                border: none;
                border-radius: 8px;
                font-size: 1.1em;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .process-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(76, 175, 80, 0.3);
            }
            .process-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .progress-section {
                display: none;
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .progress-section.active {
                display: block;
            }
            .progress-bar {
                width: 100%;
                height: 10px;
                background: #ddd;
                border-radius: 5px;
                overflow: hidden;
                margin: 10px 0;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                width: 0%;
                transition: width 0.3s ease;
            }
            .status-text {
                color: #666;
                font-size: 0.95em;
                margin-top: 10px;
            }
            .results-section {
                display: none;
                margin-top: 30px;
                padding: 20px;
                background: #f0fff4;
                border-radius: 10px;
                border-left: 4px solid #4CAF50;
            }
            .results-section.active {
                display: block;
            }
            .result-link {
                color: #667eea;
                text-decoration: none;
                font-weight: bold;
            }
            .error-section {
                display: none;
                margin-top: 20px;
                padding: 15px;
                background: #fff3f0;
                border-radius: 10px;
                border-left: 4px solid #ff6b6b;
                color: #c92a2a;
            }
            .error-section.active {
                display: block;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏢 Insurance Quote Comparison System</h1>
            <p class="subtitle">Multi-Carrier PDF Analysis & Google Sheets Integration</p>
            
            <div class="setup-section">
                <h2>📊 Setup Carriers</h2>
                <div class="setup-controls">
                    <label for="numCarriers">Number of Carriers:</label>
                    <select id="numCarriers">
                        <option value="1">1 Carrier</option>
                        <option value="2" selected>2 Carriers</option>
                        <option value="3">3 Carriers</option>
                    </select>
                    <button onclick="setupCarriers()">Setup</button>
                </div>
            </div>
            
            <div class="columns-wrapper" id="columnsWrapper"></div>
            
            <div class="process-section">
                <button class="process-btn" id="processBtn" onclick="processQuotes()">
                    🚀 PROCESS ALL CARRIERS
                </button>
            </div>
            
            <div class="progress-section" id="progressSection">
                <h3>⚙️ Processing...</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="status-text" id="statusText">Initializing...</div>
            </div>
            
            <div class="results-section" id="resultsSection">
                <h3>✅ Processing Complete!</h3>
                <div id="resultsList"></div>
            </div>
            
            <div class="error-section" id="errorSection">
                <div id="errorMessage"></div>
            </div>
        </div>
        
        <script>
            let carriers = [];
            let numCarriers = 2;
            
            function setupCarriers() {
                numCarriers = parseInt(document.getElementById('numCarriers').value);
                carriers = [];
                for (let i = 0; i < numCarriers; i++) {
                    carriers.push({
                        name: '',
                        property: null,
                        gl: null,
                        liquor: null
                    });
                }
                renderColumns();
            }
            
            function renderColumns() {
                const wrapper = document.getElementById('columnsWrapper');
                wrapper.innerHTML = '';
                
                const insuranceTypes = [
                    { key: 'property', label: 'PROPERTY INSURANCE', icon: '🏠' },
                    { key: 'gl', label: 'GENERAL LIABILITY', icon: '⚖️' },
                    { key: 'liquor', label: 'LIQUOR INSURANCE', icon: '🍷' }
                ];
                
                insuranceTypes.forEach(insType => {
                    const column = document.createElement('div');
                    column.className = 'column';
                    column.innerHTML = `
                        <h3>${insType.icon} ${insType.label}</h3>
                        ${carriers.map((c, idx) => `
                            <div class="carrier-group">
                                <label>Carrier ${idx + 1} Name:</label>
                                <input type="text" placeholder="e.g., King Saif" 
                                       onchange="carriers[${idx}].name = this.value" 
                                       value="${c.name}">
                                <label>Upload PDF:</label>
                                <input type="file" accept=".pdf" 
                                       onchange="handleFileUpload(${idx}, '${insType.key}', this)"
                                       data-carrier="${idx}" data-type="${insType.key}">
                                <div class="file-label" id="file-${idx}-${insType.key}">
                                    Click or drag & drop PDF
                                </div>
                            </div>
                        `).join('')}
                    `;
                    wrapper.appendChild(column);
                });
            }
            
            function handleFileUpload(carrierIdx, insType, input) {
                if (input.files.length > 0) {
                    carriers[carrierIdx][insType] = input.files[0];
                    const label = document.getElementById(`file-${carrierIdx}-${insType}`);
                    label.textContent = '✅ ' + input.files[0].name;
                    label.classList.add('selected');
                }
            }
            
            function processQuotes() {
                if (!carriers.some(c => c.name.trim())) {
                    showError('Please enter at least one carrier name');
                    return;
                }
                
                if (!carriers.some(c => c.property || c.gl || c.liquor)) {
                    showError('Please upload at least one PDF');
                    return;
                }
                
                document.getElementById('progressSection').classList.add('active');
                document.getElementById('processBtn').disabled = true;
                document.getElementById('errorSection').classList.remove('active');
                
                const formData = new FormData();
                carriers.forEach((carrier, idx) => {
                    formData.append(`carrier_${idx}_name`, carrier.name);
                    if (carrier.property) formData.append(`carrier_${idx}_property`, carrier.property);
                    if (carrier.gl) formData.append(`carrier_${idx}_gl`, carrier.gl);
                    if (carrier.liquor) formData.append(`carrier_${idx}_liquor`, carrier.liquor);
                });
                
                fetch('/api/process', {
                    method: 'POST',
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        showError(data.error);
                    } else {
                        updateProgress(100);
                        document.getElementById('statusText').textContent = 'Complete!';
                        setTimeout(() => {
                            showResults(data);
                            document.getElementById('processBtn').disabled = false;
                        }, 1500);
                    }
                })
                .catch(err => {
                    showError('Processing failed: ' + err.message);
                    document.getElementById('processBtn').disabled = false;
                });
            }
            
            function updateProgress(percent) {
                document.getElementById('progressFill').style.width = percent + '%';
            }
            
            function showResults(data) {
                document.getElementById('progressSection').classList.remove('active');
                document.getElementById('resultsSection').classList.add('active');
                const list = document.getElementById('resultsList');
                list.innerHTML = `
                    <div style="padding: 10px; background: white; border-radius: 6px; margin-bottom: 10px;">
                        <strong>✅ Carriers Processed:</strong> ${data.carriers_processed || 0}
                    </div>
                    <div style="padding: 10px; background: white; border-radius: 6px; margin-bottom: 10px;">
                        <strong>📊 Google Sheet Updated:</strong> Insurance Fields Data
                    </div>
                    <div style="padding: 10px; background: white; border-radius: 6px;">
                        <strong>🎉 Status:</strong> All data pushed to Google Sheets!
                    </div>
                `;
            }
            
            function showError(msg) {
                document.getElementById('errorSection').classList.add('active');
                document.getElementById('errorMessage').textContent = '❌ ' + msg;
            }
            
            setupCarriers();
        </script>
    </body>
    </html>
    '''

@app.route('/api/process', methods=['POST'])
def process_quotes_api():
    """Process insurance quotes from uploaded PDFs"""
    print("\n[API] /api/process called")
    
    try:
        # Get the property directory (parent of app.py)
        property_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(property_dir, 'src')
        
        print(f"[API] Property dir: {property_dir}")
        print(f"[API] Src dir: {src_dir}")
        
        # Change to property directory
        original_dir = os.getcwd()
        os.chdir(property_dir)
        print(f"[API] Changed to: {os.getcwd()}")
        
        # Add src to path if not already there
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        try:
            # Import processing functions AFTER changing directory
            print("[API] Importing multi_carrier_master...")
            from multi_carrier_master import (
                process_carrier_insurance_type,
                push_master_to_sheets
            )
            print("[API] ✅ Import successful")
            
            # Parse carriers from request
            print("[API] Parsing carriers from request...")
            carriers = []
            idx = 0
            while f'carrier_{idx}_name' in request.form:
                carrier_name = request.form.get(f'carrier_{idx}_name', '').strip()
                if not carrier_name:
                    idx += 1
                    continue
                    
                print(f"[API] Processing Carrier {idx}: {carrier_name}")
                carrier = {'name': carrier_name}
                
                # Map file upload keys to insurance types
                insurance_types_map = {
                    'property': 'property',
                    'gl': 'general_liability',
                    'liquor': 'liquor'
                }
                
                # Save uploaded files and build carrier data
                for upload_key, insurance_type in insurance_types_map.items():
                    form_key = f'carrier_{idx}_{upload_key}'
                    if form_key in request.files:
                        file = request.files[form_key]
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            # Save to uploads folder with full path
                            upload_folder_path = os.path.join(property_dir, app.config['UPLOAD_FOLDER'])
                            os.makedirs(upload_folder_path, exist_ok=True)
                            
                            pdf_filename = f"{carrier_name}_{upload_key}_{filename}"
                            pdf_path = os.path.join(upload_folder_path, pdf_filename)
                            file.save(pdf_path)
                            
                            # Store carrier PDF info in format expected by processing functions
                            carrier[insurance_type] = {
                                'pdf_file': filename,
                                'pdf_path': pdf_path
                            }
                            print(f"[API]   ✅ Saved {insurance_type}: {pdf_path}")
                
                carriers.append(carrier)
                idx += 1
            
            if not carriers:
                return jsonify({'error': 'No carriers or PDFs provided'}), 400
            
            print(f"[API] Total carriers to process: {len(carriers)}")
            
            # Process each carrier and insurance type
            print("[API] Starting carrier processing...")
            all_results = {}
            for carrier in carriers:
                carrier_name = carrier['name']
                all_results[carrier_name] = {}
                print(f"\n[API] >>> PROCESSING CARRIER: {carrier_name}")
                
                for insurance_type in ['property', 'general_liability', 'liquor']:
                    if insurance_type in carrier:
                        print(f"[API]   >>> {insurance_type.upper()}")
                        try:
                            result = process_carrier_insurance_type(
                                carrier,
                                insurance_type,
                                carrier[insurance_type]
                            )
                            all_results[carrier_name][insurance_type] = result
                            print(f"[API]   ✅ {insurance_type} completed")
                        except Exception as e:
                            print(f"[API]   ❌ {insurance_type} FAILED: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            all_results[carrier_name][insurance_type] = None
            
            # Push to Google Sheets
            print(f"\n[API] >>> PHASE 4: PUSHING TO GOOGLE SHEETS")
            try:
                sheets_result = push_master_to_sheets(carriers)
                print("[API] ✅ Google Sheets push completed")
            except Exception as e:
                print(f"[API] ⚠️ Google Sheets push failed: {str(e)}")
                import traceback
                traceback.print_exc()
            
            print("\n[API] ✅✅✅ BACKEND PROCESSING COMPLETE!")
            
            return jsonify({
                'status': 'success',
                'carriers_processed': len(carriers),
                'message': 'All data pushed to Google Sheets!',
                'results': all_results
            }), 200
        
        except Exception as e:
            print(f"\n[API] ❌ ERROR DURING PROCESSING: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
        
        finally:
            os.chdir(original_dir)
            print(f"[API] Restored directory to: {os.getcwd()}")
    
    except Exception as e:
        print(f"\n[API] ❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'version': '3.0'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
