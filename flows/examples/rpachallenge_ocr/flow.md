# RPA Challenge OCR Invoice Extractor
> Description: Download invoice from Automation Challenge - OCR via Playwright, extract key data using Local AI (Ollama), and export structured CSV
> Version: 1.0.0

## Variables
- `extracted_data`: {}
- `table_row`: {}

## Steps

### 1. Open Automation Challenge OCR Page (`web.open`)
- **url:** ${config.website}
- **headless:** ${config.headless}

### 2. Download Sample Invoice 1 via Playwright (`web.download`)
- **output_var:** `download_info`
- **selector:** a:has-text('Download sample invoice 1')
- **target_path:** ${config.invoice_local_path}

### 3. Extract Invoice Data Using Local AI (Ollama) (`ai.extract`)
- **output_var:** `extracted_data`
- **image_path:** ${config.invoice_local_path}
- **instructions:** You are an RPA invoice extractor. Extract the following fields from the invoice: InvoiceNo, InvoiceDate, CompanyName, TotalDue.
- **schema:** {"InvoiceNo": "string", "InvoiceDate": "string", "CompanyName": "string", "TotalDue": "string"}
- **model:** ${config.model}
- **base_url:** ${config.ollama_url}

### 4. Map Extracted Data to Challenge Table Row (`logic.set_variable`)
- **output_var:** `table_row`
- **name:** table_row
- **value:** {"ID": "sample1", "DueDate": "25-02-2019", "InvoiceNo": "${extracted_data.InvoiceNo}", "InvoiceDate": "${extracted_data.InvoiceDate}", "CompanyName": "${extracted_data.CompanyName}", "TotalDue": "${extracted_data.TotalDue}"}

### 5. Export Extracted Invoices to CSV (`csv.write`)
- **file_path:** ${config.output_csv}
- **data:** ["${table_row}"]
- **columns:** ["ID", "DueDate", "InvoiceNo", "InvoiceDate", "CompanyName", "TotalDue"]

### 6. Close Browser Session (`web.close`)
