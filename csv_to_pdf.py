import csv
import sys
from decimal import Decimal
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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

def add_page_number(canvas, doc):
    canvas.saveState()
    if canvas.getPageNumber() == 1:
        canvas.setTitle('')
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"Seite {canvas.getPageNumber()}")
    canvas.restoreState()

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
                        'bezeichnung': empfaenger or '',
                        'betrag': betrag,
                        'einnahmen': format_german_number(betrag) if betrag > 0 else '',
                        'ausgaben': format_german_number(betrag) if betrag < 0 else ''
                    })
            break  # success, stop trying encodings
        except UnicodeDecodeError:
            continue  # try next encoding

    # Sortiere nach Datum (älteste zuerst)
    transactions.sort(key=lambda x: x['datum'])

    # Change output_file extension from .tex to .pdf
    if output_file.endswith('.tex'):
        output_file = output_file[:-4] + '.pdf'

    # Create PDF with ReportLab
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        leftMargin=1*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    doc.title = ''

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    # Title
    title = Paragraph("<b>Einnahmen und Ausgaben</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))

    # Split into blocks of 27 entries per table
    rows_per_table = 27
    total_tables = (len(transactions) + rows_per_table - 1) // rows_per_table

    for table_idx in range(total_tables):
        start_idx = table_idx * rows_per_table
        end_idx = min(start_idx + rows_per_table, len(transactions))
        table_transactions = transactions[start_idx:end_idx]

        # Calculate sums for this table
        einnahmen_sum = sum(t['betrag'] for t in table_transactions if t['betrag'] > 0)
        ausgaben_sum = abs(sum(t['betrag'] for t in table_transactions if t['betrag'] < 0))

        # Create table data
        data = []

        # Header row 1
        header_style = ParagraphStyle('header', fontSize=8, alignment=TA_LEFT, leading=10)
        data.append([
            Paragraph('<b>Lfd. Nummer,<br/>zugleich<br/>Beleg-Nr.</b>', header_style),
            Paragraph('<b>Datum des<br/>Eingangs bzw.<br/>der Auszahlung</b>', header_style),
            Paragraph('<b>Bezeichnung der Einnahme<br/>bzw. Ausgabe<br/><font size=6>(soweit aus den Belegen nicht ersichtlich,<br/>auch Einzahler bzw. Empfänger)</font></b>', header_style),
            Paragraph('<b>Einnahmen<br/>EUR</b>', header_style),
            Paragraph('<b>Ausgaben<br/>EUR</b>', header_style)
        ])

        # Header row 2 (column numbers)
        col_num_style = ParagraphStyle('colnum', fontSize=8, alignment=TA_CENTER, leading=10)
        data.append([
            Paragraph('<b>1</b>', col_num_style),
            Paragraph('<b>2</b>', col_num_style),
            Paragraph('<b>3</b>', col_num_style),
            Paragraph('<b>4</b>', col_num_style),
            Paragraph('<b>5</b>', col_num_style)
        ])

        # Transaction rows
        cell_style = ParagraphStyle('cell', fontSize=8, alignment=TA_LEFT, leading=10)
        for trans in table_transactions:
            data.append([
                '',
                Paragraph(trans['datum_str'], cell_style),
                Paragraph(trans['bezeichnung'], cell_style),
                Paragraph(trans['einnahmen'], cell_style),
                Paragraph(trans['ausgaben'], cell_style)
            ])

        # Total row
        total_style = ParagraphStyle('total', fontSize=8, alignment=TA_LEFT, leading=10)
        data.append([
            '',
            '',
            Paragraph('<b>Übertrag</b>', total_style),
            Paragraph(f'<b>{format_german_number(einnahmen_sum)}</b>', total_style),
            Paragraph(f'<b>{format_german_number(ausgaben_sum)}</b>', total_style)
        ])

        # Create table
        table = Table(data, colWidths=[2.6*cm, 2.6*cm, None, 2.6*cm, 2.6*cm])

        # Table style
        table_style = TableStyle([
            # Outer border - thick
            ('BOX', (0, 0), (-1, -1), 1.2, colors.black),

            # Header styling
            ('BACKGROUND', (0, 0), (-1, 1), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Grid lines
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.black),
            ('LINEABOVE', (0, 2), (-1, 2), 1.2, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.black),

            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ])

        table.setStyle(table_style)
        elements.append(table)
        totals.append([einnahmen_sum, ausgaben_sum])

        # Add space between tables or page break
        if table_idx < total_tables - 1:
            elements.append(PageBreak())

    # Add summary table on new page
    elements.append(PageBreak())

    # Summary table
    summary_data = [['Seite', 'Einnahmen', 'Ausgaben']]

    seite = 1
    einnahmen_gesamt = 0
    ausgaben_gesamt = 0

    for total in totals:
        summary_data.append([
            str(seite),
            format_german_number(total[0]),
            format_german_number(total[1])
        ])
        seite += 1
        einnahmen_gesamt += total[0]
        ausgaben_gesamt += total[1]

    summary_data.append([
        'Gesamt',
        format_german_number(einnahmen_gesamt),
        format_german_number(ausgaben_gesamt)
    ])

    summary_table = Table(summary_data, colWidths=[3*cm, 4*cm, 4*cm])
    summary_style = TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.black),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    summary_table.setStyle(summary_style)
    elements.append(summary_table)

    # Build PDF
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)



def main():
    if len(sys.argv) != 3:
        print("Verwendung: python script.py input.csv output.pdf")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]


    process_csv(input_file, output_file)
    print(f"Erfolgreich verarbeitet! Ausgabe in: {output_file}")




if __name__ == "__main__":
    main()