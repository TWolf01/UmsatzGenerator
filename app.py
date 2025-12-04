import os

from flask import Flask, request, send_from_directory, render_template_string, url_for
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
        h1 { margin-top: 0; font-size: 1.8rem; }
        p { margin: 0.6rem 0 1.8rem; }
        label { font-weight: 600; display: inline-block; margin-bottom: 0.4rem; }
        input[type="file"] { width: 100%; }
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
        <p>Upload one or more .csv files and get ReportLab-generated PDFs.</p>
        <form method="post" enctype="multipart/form-data" action="/upload" target="_blank">
            <label for="csv-input">Select CSV files</label>
            <input id="csv-input" type="file" name="files" accept=".csv" multiple required>
            <button type="submit" aria-label="Convert CSV files to PDF">Convert</button>
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
    if "files" not in request.files:
        return "No files uploaded", 400

    files = [f for f in request.files.getlist("files") if f.filename]
    if not files:
        return "No selected files", 400

    pdf_links = []
    for file in files:
        filename = secure_filename(file.filename)
        base_name, ext = os.path.splitext(filename)
        if ext.lower() != ".csv":
            return "Only .csv files are allowed", 400

        safe_base = base_name or "csv_file"
        stem = safe_base
        counter = 1
        while os.path.exists(os.path.join(app.config["OUTPUT_FOLDER"], f"{stem}.pdf")):
            stem = f"{safe_base}_{counter}"
            counter += 1

        input_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{stem}.csv")
        pdf_path = os.path.join(app.config["OUTPUT_FOLDER"], f"{stem}.pdf")

        file.save(input_path)

        try:
            # Process CSV directly to PDF with ReportLab
            process_csv(input_path, pdf_path)

            pdf_url = url_for("serve_output", filename=f"{stem}.pdf", _external=True)
            pdf_links.append((stem, pdf_url))

        except Exception as err:
            return f"Error during processing {filename}:\n{err}", 500

    links_html = "".join(
        f'<li><a href="{url}" target="_blank" rel="noopener">{name}.pdf</a></li>'
        for name, url in pdf_links
    )
    urls_js_array = ",".join(f'"{url}"' for _, url in pdf_links)

    result_page = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Conversion Complete</title>
    </head>
    <body>
        <h2>Generated PDFs</h2>
        <ul>{links_html}</ul>
        <script>
            const pdfUrls = [{urls_js_array}];
            window.addEventListener("DOMContentLoaded", () => {{
                pdfUrls.forEach(url => window.open(url, "_blank", "noopener"));
            }});
        </script>
    </body>
    </html>
    """

    return result_page


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename, as_attachment=False)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
