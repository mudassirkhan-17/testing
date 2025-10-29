# Insurance Document Processing System

An intelligent PDF processing pipeline that extracts insurance data from PDF documents and automatically populates Google Sheets. This system combines PyMuPDF text extraction, OCR processing, AI-powered page selection, and LLM field extraction to process insurance documents efficiently.

## 🎯 Features

- **Multi-Carrier Support**: Process multiple insurance carriers simultaneously
- **Multiple Insurance Types**: Property, General Liability, Liquor, and Workers Compensation
- **Smart Text Extraction**: Combines PyMuPDF and OCR for maximum accuracy
- **AI-Powered Processing**: Uses GPT models for intelligent page selection and field extraction
- **Web Interface**: Beautiful, modern GUI for easy document upload and processing
- **Real-Time Progress**: Live progress tracking with animated UI
- **Google Sheets Integration**: Automatically pushes extracted data to Google Sheets
- **Comprehensive Reporting**: Detailed reports for each processing phase

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key
- Google Sheets API credentials
- Tesseract OCR (for OCR processing)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   cd summary_final_deployment
   ```

2. **Install dependencies**
   ```bash
   cd property
   pip install -r config/requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `config/.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Configure Google Sheets**
   
   Place your Google Sheets credentials JSON file in the appropriate location.

## 💻 Usage

### Option 1: Web Interface (Recommended)

Start the Flask web application:

```bash
cd property/src
python app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

**Features:**
- Upload multiple carriers at once
- Support for 4 insurance types per carrier
- Real-time progress tracking
- Beautiful animated UI
- Automatic processing pipeline

### Option 2: Command Line Pipeline

Run the complete processing pipeline:

```bash
cd property/src
python mine.py
```

This will:
1. Let you select a PDF file
2. Run all processing phases automatically
3. Push results to Google Sheets
4. Generate detailed reports

### Option 3: Individual Phases

You can also run individual phases separately:

**Phase 1: PyMuPDF Extraction**
```bash
python A_phase1_Pymupdf.py
```

**Phase 2: OCR Processing**
```bash
python A_phase2_ocr.py
```

**Phase 2C: Smart LLM Selection**
```bash
python A_phase2c_smart_selection.py
```

**Phase 2D: Intelligent Combining**
```bash
python A_phase2d_intelligent_combining.py
```

**Phase 3: LLM Field Extraction**
```bash
python A_phase3_llm_extraction.py
```

**Phase 4: Google Sheets Integration**
```bash
python A_phase5_simple_sheets.py
```

## 📁 Project Structure

```
summary_final_deployment/
├── property/
│   ├── api/                    # FastAPI endpoints
│   │   └── main.py
│   ├── config/                 # Configuration files
│   │   ├── requirements.txt
│   │   ├── R&R.json
│   │   └── renewal.json
│   ├── pdf/                    # Input PDF files
│   ├── pdf2/                   # Additional PDF files
│   ├── results/                # Processing results
│   └── src/                    # Source code
│       ├── app.py              # Flask web application (GUI)
│       ├── mine.py             # Main pipeline script
│       ├── A_phase1_Pymupdf.py        # PyMuPDF extraction
│       ├── A_phase2_ocr.py            # OCR processing
│       ├── A_phase2c_smart_selection.py # AI page selection
│       ├── A_phase2d_intelligent_combining.py # Text combining
│       ├── A_phase3_llm_extraction.py   # Field extraction
│       ├── A_phase5_simple_sheets.py    # Google Sheets integration
│       ├── multi_carrier_master.py      # Multi-carrier processing
│       ├── pdf_input_selector.py        # PDF selection utility
│       └── utils/              # Utility functions
└── README.md                   # This file
```

## 🔄 Processing Pipeline

The system follows a 5-phase processing pipeline:

### Phase 1: PyMuPDF Extraction
- Extracts text directly from PDF using PyMuPDF
- Classifies pages as CLEAN, PROBLEM, or BORDERLINE
- Analyzes text quality and confidence scores
- Generates initial text extraction report

### Phase 2: OCR Processing
- Processes all pages with OCR for comprehensive coverage
- Handles scanned documents and images
- Extracts text even from low-quality pages
- Provides backup extraction method

### Phase 2C: Smart LLM Selection
- Uses GPT-3.5 to compare PyMuPDF vs OCR extraction
- Selects the best text source for each page
- Optimizes for accuracy and completeness
- Creates intelligent selection report

### Phase 2D: Intelligent Combining
- Combines selected text from all pages
- Creates optimized final text file
- Prepares data for field extraction
- Ensures maximum information retention

### Phase 3: LLM Field Extraction
- Uses GPT models to extract insurance fields
- Processes data in chunks for efficiency
- Merges results from all chunks
- Creates structured JSON output

### Phase 4: Google Sheets Integration
- Pushes extracted fields to Google Sheets
- Automatically formats data
- Updates existing rows or creates new ones
- Provides cloud-based data storage

## 📊 Results

All processing results are saved in the `property/results/` directory:

- `clean_pages_results.txt` - High-quality pages ready for use
- `problem_pages_list.txt` - Pages requiring attention
- `phase1_report.txt` - Detailed Phase 1 analysis
- `all_pages_results.txt` - Comprehensive page analysis
- `combined_text.txt` - Final optimized text
- `final_extraction_results.json` - Extracted insurance fields
- `final_validated_fields.json` - Validated field data

## 🛠️ Configuration

### PDF File Naming Convention

For multi-carrier processing, name your PDFs as:
```
{carrier_name}_property.pdf
{carrier_name}_general_liability.pdf
{carrier_name}_liquor.pdf
{carrier_name}_workers_compensation.pdf
```

Example:
```
king_property.pdf
king_general_liability.pdf
king_liquor.pdf
```

## 🔧 Troubleshooting

### Uvicorn Not Found Error
If you see `uvicorn is not recognized`, install uvicorn:
```bash
pip install uvicorn[standard]
```

Or run Flask instead:
```bash
python property/src/app.py
```

### PDF Not Found
Ensure PDF files are in the `property/pdf/` directory or update the path in the script.

### OpenAI API Errors
Verify your `OPENAI_API_KEY` is set correctly in `property/config/.env`.

### Google Sheets Errors
Check that your Google Sheets credentials are properly configured and the service account has access to the spreadsheet.

## 📝 Notes

- Processing time depends on PDF size and number of pages
- OCR processing is slower but more comprehensive
- AI-powered selection optimizes both speed and accuracy
- All results are saved locally before Google Sheets upload
- The system automatically retries failed API calls

## 🎨 Web Interface Features

- **Modern Design**: Beautiful gradient backgrounds and smooth animations
- **Real-Time Updates**: Server-Sent Events for live progress tracking
- **Multi-Carrier Upload**: Add multiple carriers dynamically
- **File Status Indicators**: Visual feedback for uploaded files
- **Progress Animations**: Phase-specific progress bars and icons
- **Field Extraction Preview**: Live preview of extracted fields
- **Fun Facts**: Educational content during processing

## 📚 Technologies Used

- **Python 3.11**: Core language
- **Flask**: Web framework for GUI
- **FastAPI**: REST API framework
- **PyMuPDF (fitz)**: PDF text extraction
- **Tesseract OCR**: Optical character recognition
- **OpenAI GPT**: AI-powered text selection and extraction
- **Google Sheets API**: Data integration
- **Pillow**: Image processing
- **python-dotenv**: Environment management

## 🤝 Contributing

This is a proprietary system. For issues or suggestions, please contact the development team.

## 📄 License

Proprietary - All rights reserved

## 🎯 Quick Start Summary

1. Install dependencies: `pip install -r property/config/requirements.txt`
2. Set up `.env` file with OpenAI API key
3. Run the web app: `cd property/src && python app.py`
4. Open browser to `http://localhost:5000`
5. Upload your insurance PDFs
6. Watch the magic happen! ✨

---

**Happy Processing! 🚀**
