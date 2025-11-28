import csv
import sys
from decimal import Decimal
from datetime import datetime

def parse_german_number(value_str):
    """Konvertiert deutsche Zahlenformatierung in Decimal"""
    if not value_str or value_str.strip() == '':
        return Decimal('0')
    # Ersetze Tausendertrennzeichen und Dezimalkomma
    value_str = value_str.replace('.', '').replace(',', '.')
    try:
        return Decimal(value_str)
    except:
        return Decimal('0')

def format_german_number(value):
    """Formatiert Decimal als deutsche Zahl"""
    if value == 0:
        return ''
    # Formatiere mit 2 Dezimalstellen und ersetze Punkt durch Komma
    formatted = f"{abs(value):.2f}".replace('.', ',')
    return formatted

def parse_german_date(date_str):
    """Konvertiert deutsches Datum (dd.mm.YYYY oder dd.mm.yy) in ein datetime Objekt"""
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def format_date_for_output(date_obj):
    """Formatiert datetime Objekt für Ausgabe"""
    if date_obj:
        return date_obj.strftime('%d.%m.%Y')
    return ''

def escape_latex(text):
    """Escaped spezielle LaTeX Zeichen"""
    if not text:
        return ''
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def process_csv(input_file, output_file):
    """Hauptfunktion zur Verarbeitung der CSV-Datei"""

    # Lese CSV-Datei
    totals = []
    transactions = []


    # Try Sparkasse encoding first, fallback to Commerzbank
    for encoding in ('utf-8-sig', 'iso-8859-15'):
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=';', quotechar='"')
                # Normalize fieldnames (strip, unify spacing, umlauts etc.)
                reader.fieldnames = [fn.strip() for fn in reader.fieldnames]

                for row in reader:
                    # Normalize keys for Sparkasse vs. Commerzbank
                    buchungstag = row.get('Buchungstag')
                    betrag_str = row.get('Betrag')
                    empfaenger = (
                        row.get('Beguenstigter/Zahlungspflichtiger') or
                        row.get('Begünstigter / Auftraggeber') or
                        row.get('Name Zahlungsbeteiligter')
                    )

                    date_obj = parse_german_date(buchungstag)
                    if not date_obj:
                        continue

                    betrag = parse_german_number(betrag_str)

                    transactions.append({
                        'datum': date_obj,
                        'datum_str': format_date_for_output(date_obj),
                        'bezeichnung': empfaenger,
                        'betrag': betrag,
                        'einnahmen': format_german_number(betrag) if betrag > 0 else '',
                        'ausgaben': format_german_number(betrag) if betrag < 0 else ''
                    })
            break  # success, stop trying encodings
        except UnicodeDecodeError:
            continue  # try next encoding

    # Sortiere nach Datum (älteste zuerst)
    transactions.sort(key=lambda x: x['datum'])

    # Schreibe LaTeX-Ausgabe
    with open(output_file, 'w', encoding='utf-8') as f:

        f.write(r"\documentclass[a4paper,8pt]{article}" + "\n")
        f.write(r"\usepackage[utf8]{inputenc}" + "\n")
        f.write(r"\usepackage[T1]{fontenc}" + "\n")
        f.write(r"\usepackage[left=1cm,right=2cm,top=2cm,bottom=2cm]{geometry}" + "\n")
        f.write(r"\usepackage{array}" + "\n")
        f.write(r"\usepackage{tabularx}" + "\n")
        f.write(r"\usepackage{makecell}" + "\n")
        f.write(r"\usepackage{helvet}" + "\n")
        f.write(r"\usepackage{hhline}" + "\n")
        f.write(r"\usepackage{arydshln}" + "\n")
        f.write(r"\usepackage{fancyhdr}" + "\n")
        f.write(r"\pagestyle{fancy}" + "\n")
        f.write(r"\renewcommand{\familydefault}{\sfdefault}" + "\n")
        f.write(r"\renewcommand\theadfont{\bfseries}" + "\n")
        f.write(r"\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}" + "\n")
        f.write(r"\newcolumntype{Y}{>{\raggedright\arraybackslash}X}" + "\n")
        f.write(r"\newcommand{\thickhline}{\noalign{\hrule height 1.2pt}}" + "\n")
        f.write(r"\fancyhead{}" + "\n")
        f.write(r"\fancyhead[C]{\LARGE Einnahmen und Ausgaben}" + "\n")
        f.write(r"\renewcommand{\headrulewidth}{0pt}" + "\n")

        f.write(r"\begin{document}" + "\n")
        f.write(r"	\vspace{1em}" + "\n")
        f.write(r"	\renewcommand{\arraystretch}{1.4}" + "\n")
        f.write(r"  \noindent" + "\n")

        # Teile in Blöcke von 27 Einträgen auf
        rows_per_table = 27
        total_tables = (len(transactions) + rows_per_table - 1) // rows_per_table

        for table_idx in range(total_tables):
            start_idx = table_idx * rows_per_table
            end_idx = min(start_idx + rows_per_table, len(transactions))
            table_transactions = transactions[start_idx:end_idx]

            # Berechne Summen für diese Tabelle
            einnahmen_sum = sum(t['betrag'] for t in table_transactions if t['betrag'] > 0)
            ausgaben_sum = abs(sum(t['betrag'] for t in table_transactions if t['betrag'] < 0))


            # Schreibe Tabellenkopf
            f.write(r"\begin{tabularx}{\textwidth}{!{\vrule width 1.2pt}C{2.6cm}|C{2.6cm}|Y|C{2.6cm}|C{2.6cm}!{\vrule width 1.2pt}}" + "\n")
            f.write(r"    \thickhline" + "\n")
            f.write(r"    \makecell[l]{\textbf{Lfd. Nummer,}\\\textbf{zugleich}\\\textbf{Beleg-Nr.}} &" + "\n")
            f.write(r"    \makecell[l]{\textbf{Datum des}\\\textbf{Eingangs bzw.}\\\textbf{der Auszahlung}} &" + "\n")
            f.write(r"    \makecell[l]{\textbf{Bezeichnung der Einnahme} \\\textbf{ bzw. Ausgabe}\\" + "\n")
            f.write(r"        {\scriptsize (soweit aus den Belegen nicht ersichtlich,}\\{\scriptsize auch Einzahler bzw. Empfänger)}} &" + "\n")
            f.write(r"    \makecell[l]{\textbf{Einnahmen}\\\textbf{EUR}} &" + "\n")
            f.write(r"    \makecell[l]{\textbf{Ausgaben}\\\textbf{EUR}} \\ \hline" + "\n")
            f.write(r"    \makecell{\textbf{1}} & \makecell{\textbf{2}} & \makecell{\textbf{3}} & \makecell{\textbf{4}} & \makecell{\textbf{5}} \\ \thickhline" + "\n")

            # Schreibe Transaktionen
            for trans in table_transactions:
                f.write(f"    & {trans['datum_str']} & {escape_latex(trans['bezeichnung'])} & {trans['einnahmen']} & {trans['ausgaben']} \\\\ \\hline\n")

            # Schreibe Übertrag
            f.write(r"    \thickhline" + "\n")
            f.write(f"    & & \\makecell*[r]{{Übertrag}} & {format_german_number(einnahmen_sum)} & {format_german_number(ausgaben_sum)} \\\\ \\thickhline\n")
            f.write(r"\end{tabularx}" + "\n")
            totals.append([einnahmen_sum,ausgaben_sum])

            # Füge Abstand zwischen Tabellen ein
            if table_idx < total_tables - 1:
                f.write("\n\\vspace{1cm}\n\n")

        # Schreibe Tabellenkopf
        f.write(r"\begin{tabular}{|c|c|c|}" + "\n")
        f.write(r"    \hline" + "\n")
        f.write(r"    Seite & Einnahmen & Ausgaben \\" + "\n")
        f.write(r"    \thickhline" + "\n")

        # Schreibe Überträge
        seite = 1
        einnahmen_sum = 0
        ausgaben_sum = 0
        for total in totals:
            f.write(f" {seite}   & {format_german_number(total[0])} & {format_german_number(total[1])} \\\\ \\hline\n")
            seite += 1
            einnahmen_sum += total[0]
            ausgaben_sum += total[1]

        f.write(r"    \thickhline" + "\n")
        f.write(f" Gesamt   & {format_german_number(einnahmen_sum)} & {format_german_number(ausgaben_sum)} \\\\ \\hline\n")
        f.write(r"\end{tabular}" + "\n")

        f.write(r"\end{document}" + "\n")


def main():
    if len(sys.argv) != 3:
        print("Verwendung: python script.py input.csv output.tex")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]


    process_csv(input_file, output_file)
    print(f"Erfolgreich verarbeitet! Ausgabe in: {output_file}")




if __name__ == "__main__":
    main()