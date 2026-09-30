# RPA Challenge OCR Invoice Extraction Benchmark

This is a self-contained Project Bundle flow for the **Automation Challenge - OCR** benchmark.

---

## 1. Overview

This flow automates the following steps:
1. Opens `https://rpachallengeocr.azurewebsites.net` using Playwright (`web.open`).
2. Locates and downloads sample invoice 1 directly from the webpage via Playwright (`web.download`) into `assets/sample1.jpg`.
3. Sends the invoice to a local Ollama instance (`ai.extract`) to extract key fields: `InvoiceNo`, `InvoiceDate`, `CompanyName`, and `TotalDue` into clean JSON.
4. Maps the extracted data along with the challenge ID and due date.
5. Exports the result to CSV (`output/result.csv`) matching the challenge specification.
6. Closes the browser session (`web.close`).

---

## 2. Configuration (`config/config.json`)

```json
{
  "website": "https://rpachallengeocr.azurewebsites.net",
  "invoice_local_path": "assets/sample1.jpg",
  "ollama_url": "http://localhost:11434",
  "model": "qwen2.5:1.5b",
  "headless": true,
  "output_csv": "output/result.csv"
}
```

---

## 3. Execution Instructions

### Prerequisites
1. Ensure Ollama is running locally:
   ```powershell
   ollama run qwen2.5:1.5b
   ```
2. Run the flow using the Kinenix CLI:
   ```powershell
   kinenix run flows/examples/rpachallenge_ocr/flow.json
   ```

---

## 4. Expected Output

The generated CSV in `output/result.csv` will follow the challenge format:

```csv
ID,DueDate,InvoiceNo,InvoiceDate,CompanyName,TotalDue
sample1,25-02-2019,10021,13-02-2019,Sit Amet Corp.,1234.40
```
