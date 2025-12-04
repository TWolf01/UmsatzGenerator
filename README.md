# CSV to PDF Financial Report Generator

This project provides a web application to convert German bank transaction CSV files (e.g., from Sparkasse, Commerzbank) into a formatted PDF financial report.

## How it Works

1.  A Flask web server (`app.py`) provides a simple web page to upload one or more CSV files.
2.  The script `csv_to_latex.py` processes each CSV, parsing German date and number formats.
3.  PDFs are generated directly using the ReportLab library.
4.  The resulting PDFs are sent to the user for download and automatically opened in new browser tabs.

## Prerequisites

*   Python 3
*   Flask
*   ReportLab

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1.  Start the Flask web server:
    ```bash
    python app.py
    ```
2.  Open your web browser and go to `http://127.0.0.1:5000`.
3.  Upload your CSV file(s) and click "Convert".

## Command Line Usage

You can also use the script directly from the command line:
```bash
python csv_to_pdf.py input.csv output.pdf
```
