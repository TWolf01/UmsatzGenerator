import os
import subprocess
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
        # Step 1: Run csv_to_latex.py
        subprocess.run(["python", "csv_to_latex.py", input_path, tex_path], check=True)

        # Step 2: Compile LaTeX to PDF
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", app.config["OUTPUT_FOLDER"], tex_path],
            check=True
        )

        # Return PDF
        return send_file(pdf_path, as_attachment=True)

    except subprocess.CalledProcessError as e:
        return f"Error during processing: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
