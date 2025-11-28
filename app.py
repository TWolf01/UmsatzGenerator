import os
import subprocess
import sys

from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>CSV → PDF Converter</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        .box { border: 1px solid #ccc; padding: 2em; border-radius: 8px; max-width: 400px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>CSV → PDF Converter</h2>
        <form method="post" enctype="multipart/form-data" action="/upload" target="_blank">
            <input type="file" name="file" accept=".csv" required><br><br>
            <button type="submit">Convert</button>
        </form>
    </div>
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
        # Run csv_to_latex.py
        result_csv = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "csv_to_latex.py"), input_path, tex_path],
            capture_output=True, text=True, check=True
        )

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

    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        stdout = e.stdout or ""
        return f"Error during processing:\n{e}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}", 500


if __name__ == "__main__":
    app.run(debug=True)
