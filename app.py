import os
import subprocess

from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename
from csv_to_latex import process_csv

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSV → PDF Converter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            color-scheme: light dark;
            font-family: "Segoe UI", sans-serif;
        }
        body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: linear-gradient(160deg, #f5f7fa, #c3cfe2);
        }
        .box {
            background: #fff;
            color: #222;
            padding: 2.5rem;
            border-radius: 18px;
            box-shadow: 0 25px 60px rgba(0,0,0,0.12);
            max-width: 420px;
            width: 90%;
        }
        h1 {
            margin-top: 0;
            font-size: 1.8rem;
        }
        p {
            margin: 0.6rem 0 1.8rem;
        }
        label {
            font-weight: 600;
            display: inline-block;
            margin-bottom: 0.4rem;
        }
        input[type="file"] {
            width: 100%;
        }
        button {
            margin-top: 1.4rem;
            width: 100%;
            padding: 0.9rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            background: #4f46e5;
            color: #fff;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(79,70,229,0.35);
        }
    </style>
</head>
<body>
    <main class="box">
        <h1>CSV → PDF Converter</h1>
        <p>Upload a .csv file and get a LaTeX-rendered PDF in seconds.</p>
        <form method="post" enctype="multipart/form-data" action="/upload" target="_blank">
            <label for="csv-input">Select CSV file</label>
            <input id="csv-input" type="file" name="file" accept=".csv" required>
            <button type="submit" aria-label="Convert CSV to PDF">Convert</button>
        </form>
    </main>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(input_path)

    base_name = os.path.splitext(filename)[0]
    tex_path = os.path.join(app.config["OUTPUT_FOLDER"], f"{base_name}.tex")
    pdf_path = os.path.join(app.config["OUTPUT_FOLDER"], f"{base_name}.pdf")

    try:
        # Run csv_to_latex
        process_csv(input_path, tex_path)

        # Compile LaTeX to PDF (twice for references), capture output
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", app.config["OUTPUT_FOLDER"], tex_path],
                capture_output=True, text=True, check=True
            )

        # Clean auxiliary files
        aux_exts = (".aux", ".log", ".out", ".toc")
        for ext in aux_exts:
            aux_file = os.path.join(app.config["OUTPUT_FOLDER"], f"{base_name}{ext}")
            try:
                if os.path.exists(aux_file):
                    os.remove(aux_file)
            except OSError:
                pass

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        # Capture errors from processing or LaTeX compilation
        return f"Error during processing:\n{e}", 500


if __name__ == "__main__":
    app.run(debug=True)
