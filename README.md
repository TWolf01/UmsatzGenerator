# CSV to PDF Financial Report Generator

This project provides a web application to convert German bank transaction CSV files (e.g., from Sparkasse, Commerzbank) into a formatted PDF financial report.

## How it Works

1.  A Flask web server (`app.py`) provides a simple web page to upload a CSV file.
2.  The script `csv_to_latex.py` processes the CSV, parsing German date and number formats.
3.  A LaTeX (`.tex`) file is generated from the transaction data.
4.  The server uses `pdflatex` to compile the LaTeX file into a PDF.
5.  The resulting PDF is sent to the user for download.

## Prerequisites

*   Python 3
*   Flask (`pip install Flask`)
*   A LaTeX distribution (e.g., TeX Live, MiKTeX) with `pdflatex` in your system's PATH.

## Usage

1.  Start the Flask web server:
    ```bash
    python app.py
    ```
2.  Open your web browser and go to `http://127.0.0.1:5000`.
3.  Upload your CSV file and click "Convert".