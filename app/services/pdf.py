# Service de génération de PDF pour les tickets
# Crée un ticket PDF stylisé avec QR code et numéro de siège

from io import BytesIO
import json
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

class PDFService:
    
    @staticmethod
    def generate_ticket_pdf(ticket_data: dict) -> BytesIO:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Palette simple et élégante
        primary_color = HexColor('#E65100')      # Orange discret
        accent_color = HexColor('#FFA726')       # Orange clair pour accents
        text_dark = HexColor('#212121')          # Noir doux
        text_light = HexColor('#757575')         # Gris
        bg_color = HexColor('#FAFAFA')           # Gris très clair
        
        # Fond simple
        c.setFillColor(bg_color)
        c.rect(0, 0, width, height, fill=True, stroke=False)
        
        # En-tête simple
        c.setFillColor(primary_color)
        c.rect(0, height - 3.5*cm, width, 3.5*cm, fill=True, stroke=False)
        
        # Titre centré et stylisé
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 40)
        title_width = c.stringWidth("BitTravel", "Helvetica-Bold", 40)
        c.drawString((width - title_width) / 2, height - 2.3*cm, "BitTravel")
        
        c.setFont("Helvetica", 13)
        subtitle_width = c.stringWidth("Billet de voyage", "Helvetica", 13)
        c.drawString((width - subtitle_width) / 2, height - 3.1*cm, "Billet de voyage")
        
        # Numéro de ticket
        c.setFillColor(text_dark)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, height - 5*cm, "Numéro de ticket:")
        c.setFont("Helvetica", 9)
        c.setFillColor(text_light)
        c.drawString(5*cm, height - 5*cm, ticket_data.get('ticket_id', 'N/A'))
        
        # Agence
        c.setFillColor(text_dark)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, height - 5.7*cm, "Agence:")
        c.setFont("Helvetica", 10)
        c.setFillColor(text_light)
        c.drawString(5*cm, height - 5.7*cm, ticket_data.get('agency_name', 'N/A'))
        
        # Ligne de séparation
        c.setStrokeColor(accent_color)
        c.setLineWidth(1.5)
        c.line(2*cm, height - 6.5*cm, width - 2*cm, height - 6.5*cm)
        
        # Titre section voyage
        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, height - 7.5*cm, "Informations du voyage")
        
        y_pos = height - 8.7*cm
        info_items = [
            ("Départ:", ticket_data.get('origin', 'N/A')),
            ("Arrivée:", ticket_data.get('destination', 'N/A')),
            ("Heure:", ticket_data.get('departure', 'N/A')),
            ("Siège:", f"N° {ticket_data.get('seat_number', 'N/A')}"),
            ("Prix:", f"{ticket_data.get('price', 'N/A')} FCFA")
        ]
        
        for label, value in info_items:
            c.setFillColor(text_dark)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2.5*cm, y_pos, label)
            c.setFont("Helvetica", 10)
            c.setFillColor(text_light)
            c.drawString(5.5*cm, y_pos, value)
            y_pos -= 0.8*cm
        
        # Ligne de séparation
        c.setStrokeColor(accent_color)
        c.setLineWidth(1.5)
        c.line(2*cm, height - 13*cm, width - 2*cm, height - 13*cm)
        
        # Titre section passager
        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, height - 14*cm, "Informations passager")
        
        passenger = ticket_data.get('passenger', {})
        y_pos = height - 15.2*cm
        passenger_items = [
            ("Nom:", passenger.get('name', 'N/A')),
            ("Téléphone:", passenger.get('phone', 'N/A')),
        ]
        
        for label, value in passenger_items:
            c.setFillColor(text_dark)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2.5*cm, y_pos, label)
            c.setFont("Helvetica", 10)
            c.setFillColor(text_light)
            c.drawString(5.5*cm, y_pos, value)
            y_pos -= 0.8*cm
        
        # QR Code
        qr_data = {
            "ticket_id": ticket_data.get('ticket_id'),
            "payload": ticket_data.get('payload'),
            "signature": ticket_data.get('signature'),
            "public_key": ticket_data.get('public_key')
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        qr_image = ImageReader(qr_buffer)
        
        # QR Code agrandi et centré en bas
        qr_size = 7*cm
        qr_x = (width - qr_size) / 2
        qr_y = 5*cm
        
        # Fond blanc pour le QR
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(qr_x - 0.5*cm, qr_y - 0.5*cm, qr_size + 1*cm, qr_size + 1.5*cm, 0.4*cm, fill=True, stroke=False)
        
        # Bordure stylisée autour du QR
        c.setStrokeColor(primary_color)
        c.setLineWidth(3)
        c.roundRect(qr_x - 0.5*cm, qr_y - 0.5*cm, qr_size + 1*cm, qr_size + 1.5*cm, 0.4*cm, fill=False, stroke=True)
        
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        
        # Label centré sous le QR
        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", 11)
        label_text = "CODE DE VÉRIFICATION"
        label_width = c.stringWidth(label_text, "Helvetica-Bold", 11)
        c.drawString((width - label_width) / 2, qr_y - 1.2*cm, label_text)
        
        # Instructions en haut du pied de page
        c.setFillColor(text_light)
        c.setFont("Helvetica", 9)
        c.drawString(2*cm, 3.2*cm, "• Présentez ce ticket au contrôle")
        c.drawString(2*cm, 2.7*cm, "• Conservez-le pendant le voyage")
        
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor('#BDBDBD'))
        footer_text = "BitTravel - Billet sécurisé"
        footer_width = c.stringWidth(footer_text, "Helvetica", 8)
        c.drawString((width - footer_width) / 2, 0.5*cm, footer_text)
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer