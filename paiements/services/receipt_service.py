"""
Service de génération de reçus PDF pour les paiements CamPay.
Utilise ReportLab pour créer un PDF élégant.
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


def generate_receipt_pdf(paiement) -> bytes:
    """
    Génère un reçu PDF pour un paiement donné.

    Args:
        paiement: Instance du modèle Paiement

    Returns:
        bytes: contenu PDF brut
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Reçu de paiement #{str(paiement.reference)[:8].upper()}"
    )

    styles = getSampleStyleSheet()
    story = []

    # Couleurs de la plateforme
    primary_color = colors.HexColor('#4f46e5')  # Indigo
    success_color = colors.HexColor('#059669')  # Vert
    dark_color = colors.HexColor('#1e293b')
    gray_color = colors.HexColor('#64748b')
    light_gray = colors.HexColor('#f1f5f9')

    # ----- EN-TÊTE -----
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        textColor=gray_color,
        alignment=TA_CENTER,
        spaceAfter=2,
    )

    story.append(Paragraph("🏥 Fransick Santé", header_style))
    story.append(Paragraph("Plateforme de Télémédecine & Consultation Médicale", subtitle_style))
    story.append(Paragraph("Douala, Cameroun | fransick-sante.cm", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
    story.append(Spacer(1, 0.5 * cm))

    # ----- TITRE REÇU -----
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=dark_color,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    ref_style = ParagraphStyle(
        'Ref',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=gray_color,
        alignment=TA_CENTER,
    )
    story.append(Paragraph("REÇU DE PAIEMENT", title_style))
    story.append(Paragraph(f"Référence : #{str(paiement.reference).upper()[:16]}", ref_style))
    story.append(Spacer(1, 0.6 * cm))

    # ----- TABLEAU STATUT -----
    status_label = "✅ PAIEMENT CONFIRMÉ" if paiement.is_successful else "⏳ EN ATTENTE"
    status_bg = success_color if paiement.is_successful else colors.HexColor('#f59e0b')
    status_table = Table([[status_label]], colWidths=[16 * cm])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), status_bg),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 13),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [status_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.6 * cm))

    # ----- TABLEAU DÉTAILS -----
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=gray_color)
    value_style = ParagraphStyle('Value', parent=styles['Normal'], fontSize=10, fontName='Helvetica', textColor=dark_color)

    # Infos patient
    patient = paiement.patient
    medecin = paiement.medecin
    patient_name = f"{patient.first_name} {patient.last_name}".strip() or patient.username
    medecin_name = f"Dr. {medecin.first_name} {medecin.last_name}".strip() or f"Dr. {medecin.username}"

    # Formatage date
    date_paiement = paiement.paid_at or paiement.created_at
    date_str = date_paiement.strftime('%d/%m/%Y à %H:%M') if date_paiement else '-'
    created_str = paiement.created_at.strftime('%d/%m/%Y à %H:%M') if paiement.created_at else '-'

    data = [
        ['INFORMATIONS PATIENT', ''],
        ['Nom du patient', patient_name],
        ['Téléphone Mobile Money', paiement.phone_number],
        ['Email', patient.email or '-'],
        ['', ''],
        ['INFORMATIONS MÉDECIN', ''],
        ['Médecin traitant', medecin_name],
        ['Spécialité', getattr(getattr(medecin, 'doctor_profile', None), 'speciality', '-') or '-'],
        ['', ''],
        ['DÉTAILS DU PAIEMENT', ''],
        ['Type de paiement', paiement.get_payment_type_display()],
        ['Tarif total de la consultation', f"{int(paiement.montant_total_consultation):,} XAF".replace(',', ' ')],
        ['Montant payé', f"{int(paiement.montant_paye):,} XAF".replace(',', ' ')],
        ['Opérateur Mobile Money', paiement.campay_operator or '-'],
        ['Référence CamPay', paiement.campay_reference or '-'],
        ['Date de création', created_str],
        ['Date de confirmation', date_str],
    ]

    # Style du tableau
    table = Table(data, colWidths=[7 * cm, 9 * cm])
    table_styles = [
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]
    # Sections header (rangées 0, 5, 9)
    for row_idx in [0, 5, 9]:
        table_styles += [
            ('BACKGROUND', (0, row_idx), (-1, row_idx), primary_color),
            ('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.white),
            ('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
            ('SPAN', (0, row_idx), (-1, row_idx)),
        ]
    # Lignes vides (spacers)
    for row_idx in [4, 8]:
        table_styles += [
            ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.white),
            ('LINEBELOW', (0, row_idx), (-1, row_idx), 0, colors.white),
            ('LINEABOVE', (0, row_idx), (-1, row_idx), 0, colors.white),
            ('TOPPADDING', (0, row_idx), (-1, row_idx), 3),
            ('BOTTOMPADDING', (0, row_idx), (-1, row_idx), 3),
        ]
    # Alternance des lignes
    for i in range(1, len(data)):
        if i not in [0, 4, 5, 8, 9]:
            if i % 2 == 0:
                table_styles.append(('BACKGROUND', (0, i), (-1, i), light_gray))

    table.setStyle(TableStyle(table_styles))
    story.append(table)
    story.append(Spacer(1, 0.8 * cm))

    # ----- MONTANT EN VEDETTE -----
    amount_data = [[f"{int(paiement.montant_paye):,} XAF".replace(',', ' ')]]
    amount_table = Table(amount_data, colWidths=[16 * cm])
    amount_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), success_color if paiement.is_successful else colors.HexColor('#f59e0b')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 20),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(amount_table)
    story.append(Spacer(1, 0.8 * cm))

    # ----- PIED DE PAGE -----
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.3 * cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=gray_color,
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        "Ce reçu est généré automatiquement par la plateforme Fransick Santé.<br/>"
        "Pour toute réclamation, contactez le support : support@fransick-sante.cm<br/>"
        "Document valide sans signature — Paiement traité par CamPay (Mobile Money Cameroun)",
        footer_style
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
