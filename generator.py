import os
import io
import math
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# Palette colori aziendali
NAVY = colors.HexColor("#0f3868")
LIGHT_GRAY = colors.HexColor("#f4f5f7")
BORDER_GRAY = colors.HexColor("#9ca3af")
TEXT_DARK = colors.HexColor("#1f2937")

# Dati Emittente Fattura
COMPANY_INFO = {
    "name": "AGENCY MANAGEMENT SHIPPING srls",
    "address": "Trav. Via Toniolo SN",
    "city": "74019 Palagiano (TA)",
    "vat": "P.I. / C.F. 03067000731",
    "tel": "Tel. 099/4002663"
}

def format_currency(val):
    if val is None or (isinstance(val, float) and math.isnan(val)) or val == 0:
        return "€ -"
    try:
        val = float(val)
        formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"€ {formatted}"
    except Exception:
        return str(val)

def format_date(val):
    if pd.isna(val) or val is None or val == "" or str(val).lower() == "nan":
        return ""
    if isinstance(val, (datetime, pd.Timestamp)):
        months = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
        return f"{val.day:02d}-{months[val.month - 1]}-{str(val.year)[-2:]}"
    try:
        dt = pd.to_datetime(val)
        months = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
        return f"{dt.day:02d}-{months[dt.month - 1]}-{str(dt.year)[-2:]}"
    except Exception:
        return str(val)

def format_ddt(val):
    if pd.isna(val) or val is None or val == "" or str(val).lower() == "nan":
        return ""
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        return str(val)
    except Exception:
        return str(val)

class NumberedCanvas(canvas.Canvas):
    """Canvas per aggiungere numero di pagina dinamico e piè di pagina standard"""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6b7280"))
        page_text = f"Pagina {self._pageNumber} di {page_count}"
        self.drawRightString(A4[0] - 12 * mm, 8 * mm, page_text)
        self.restoreState()

def create_proforma_pdf(client_data, transports, output_path_or_buffer, invoice_number="01", invoice_date=None):
    if not invoice_date:
        invoice_date = datetime.now()
    formatted_invoice_date = format_date(invoice_date)
    
    # Margini pagina (10 mm)
    doc = SimpleDocTemplate(
        output_path_or_buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm
    )
    
    styles = getSampleStyleSheet()
    
    text_company = ParagraphStyle(
        'CompanyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK
    )
    title_proforma = ParagraphStyle(
        'ProformaTitle',
        parent=styles['Normal'],
        fontName='Helvetica-BoldOblique',
        fontSize=14,
        leading=16,
        alignment=1,
        textColor=TEXT_DARK
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=TEXT_DARK
    )
    cell_regular = ParagraphStyle(
        'CellRegular',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=TEXT_DARK
    )
    cell_center = ParagraphStyle(
        'CellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        alignment=1,
        textColor=TEXT_DARK
    )
    cell_right = ParagraphStyle(
        'CellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        alignment=2,
        textColor=TEXT_DARK
    )
    
    elements = []
    
    # 1. TESTATA: Dati Emittente (Agency Management Shipping srls) a Sinistra, "FATTURA PRO FORMA" a Destra
    company_p = Paragraph(f"""
        <font size="12" color="{NAVY}"><b>{COMPANY_INFO['name']}</b></font><br/>
        {COMPANY_INFO['address']}<br/>
        {COMPANY_INFO['city']}<br/>
        {COMPANY_INFO['vat']} • {COMPANY_INFO['tel']}
    """, text_company)
    
    # Box "FATTURA PRO FORMA"
    proforma_box = Table(
        [
            [""],
            [Paragraph("FATTURA PRO FORMA", title_proforma)],
            [""]
        ],
        colWidths=[75 * mm],
        rowHeights=[1.5 * mm, 8 * mm, 1.5 * mm]
    )
    proforma_box.setStyle(TableStyle([
        ('LINEABOVE', (0, 1), (-1, 1), 1.5, NAVY),
        ('LINEBELOW', (0, 1), (-1, 1), 1.5, NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    header_table = Table(
        [[company_p, proforma_box]],
        colWidths=[115 * mm, 75 * mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3 * mm))
    
    # 2. BOX DATI CLIENTE (SX) E DATI DOCUMENTO (DX)
    client_name = str(client_data.get('ragione_sociale', '')).upper()
    client_addr = str(client_data.get('indirizzo', '')) if pd.notna(client_data.get('indirizzo')) else ""
    client_cap = str(client_data.get('cap', '')) if pd.notna(client_data.get('cap')) else ""
    client_city = str(client_data.get('citta', '')) if pd.notna(client_data.get('citta')) else ""
    client_prov = str(client_data.get('prov', '')) if pd.notna(client_data.get('prov')) else ""
    client_tel = str(client_data.get('tel', '')) if pd.notna(client_data.get('tel')) else ""
    client_vat = str(client_data.get('piva', '')) if pd.notna(client_data.get('piva')) else ""
    client_code = str(client_data.get('codice_cof', '')) if pd.notna(client_data.get('codice_cof')) else ""
    
    client_rows = [
        [Paragraph("Nome", cell_bold), Paragraph(f"<b>{client_name}</b>", cell_bold)],
        [Paragraph("Indirizzo", cell_regular), Paragraph(client_addr, cell_regular)],
        [Paragraph("C.A.P.", cell_regular), Paragraph(f"{client_cap}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Città:</b> {client_city}", cell_regular)],
        [Paragraph("Num. tel.", cell_regular), Paragraph(f"{client_tel}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Prov.:</b> {client_prov}", cell_regular)],
        [Paragraph("C. f./P. IVA", cell_regular), Paragraph(client_vat, cell_regular)]
    ]
    client_table = Table(client_rows, colWidths=[20 * mm, 107 * mm], rowHeights=[4.5 * mm] * 5)
    client_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    doc_rows = [
        [Paragraph("Numero", cell_regular), Paragraph(f"<b>{invoice_number}</b>", cell_bold)],
        [Paragraph("Data", cell_regular), Paragraph(formatted_invoice_date, cell_regular)],
        [Paragraph("Codice COF", cell_regular), Paragraph(client_code, cell_regular)],
        [Paragraph("Merce", cell_regular), Paragraph("Containers", cell_regular)],
        ["", ""]
    ]
    doc_table = Table(doc_rows, colWidths=[24 * mm, 39 * mm], rowHeights=[4.5 * mm] * 5)
    doc_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    client_doc_wrapper = Table(
        [
            [Paragraph("<b>Cliente</b>", cell_bold), ""],
            [client_table, doc_table]
        ],
        colWidths=[127 * mm, 63 * mm]
    )
    client_doc_wrapper.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
    ]))
    elements.append(client_doc_wrapper)
    elements.append(Spacer(1, 2 * mm))
    
    # 3. TABELLA TRASPORTI SENZA COLONNA UM
    # Totale larghezza disponibile: 190 mm
    # Colonne: d.d.t. (14mm) | DATA d.d.t. (18mm) | Descrizione (104mm) | Q.tà (10mm) | IVA (10mm) | Prezzo (16mm) | Importo (18mm) = 190mm
    table_data = []
    
    # Riga 0: Intestazione principale
    table_data.append([
        Paragraph("<b>d.d.t.</b>", cell_center),
        Paragraph("<b>DATA d.d.t.</b>", cell_center),
        Paragraph("<b>Descrizione</b>", cell_center),
        Paragraph("<b>Q.tà</b>", cell_center),
        Paragraph("<b>IVA</b>", cell_center),
        Paragraph("<b>Prezzo</b>", cell_center),
        Paragraph("<b>Importo</b>", cell_center)
    ])
    
    # Riga 1: Sotto-intestazione per colonna Descrizione (104mm totali)
    # Rif. Cliente (24mm) | n° Container (26mm) | Data Carico (17mm) | Percorso / Servizio (37mm) = 104mm
    desc_subhead = Table(
        [[
            Paragraph("<b>Rif. Cliente</b>", cell_bold),
            Paragraph("<b>n° Container/Merce</b>", cell_bold),
            Paragraph("<b>Data Carico</b>", cell_bold),
            Paragraph("<b>Percorso / Servizio</b>", cell_bold)
        ]],
        colWidths=[24 * mm, 26 * mm, 17 * mm, 37 * mm]
    )
    desc_subhead.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    table_data.append([
        "",
        "",
        desc_subhead,
        "",
        "",
        "",
        ""
    ])
    
    tot_imponibile = 0.0
    tot_iva_22 = 0.0
    tot_iva_art9 = 0.0
    
    for row in transports:
        # Formattazione sicura del numero DDT
        ddt_val = row.get('ddt_numero', '')
        ddt_num = format_ddt(ddt_val)
        ddt_date = format_date(row.get('ddt_data', ''))
        
        rif_cliente = str(row.get('rif_cliente', '')) if pd.notna(row.get('rif_cliente')) and str(row.get('rif_cliente')).lower() != 'nan' else ""
        container = str(row.get('container', '')) if pd.notna(row.get('container')) and str(row.get('container')).lower() != 'nan' else ""
        data_carico = format_date(row.get('data_carico', ''))
        tratta = str(row.get('tratta', '')) if pd.notna(row.get('tratta')) and str(row.get('tratta')).lower() != 'nan' else ""
        
        try:
            qty = float(row.get('quantita', 1.0))
            if math.isnan(qty):
                qty = 1.0
        except (ValueError, TypeError):
            qty = 1.0
            
        try:
            prezzo = float(row.get('prezzo', 0.0))
            if math.isnan(prezzo):
                prezzo = 0.0
        except (ValueError, TypeError):
            prezzo = 0.0
            
        importo = qty * prezzo
        tot_imponibile += importo
        
        aliquota_iva = str(row.get('iva', '22%')).strip()
        if 'art' in aliquota_iva.lower() or 'es' in aliquota_iva.lower() or aliquota_iva == '0' or aliquota_iva == '0%':
            iva_str = "Art. 9"
            tot_iva_art9 += importo
        else:
            iva_str = "22%"
            tot_iva_22 += importo * 0.22
            
        desc_content = Table(
            [[
                Paragraph(rif_cliente, cell_regular),
                Paragraph(f"<b>{container}</b>" if container else "", cell_regular),
                Paragraph(data_carico, cell_regular),
                Paragraph(tratta, cell_regular)
            ]],
            colWidths=[24 * mm, 26 * mm, 17 * mm, 37 * mm]
        )
        desc_content.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        table_data.append([
            Paragraph(f"<b>{ddt_num}</b>" if ddt_num else "", cell_center),
            Paragraph(ddt_date, cell_center),
            desc_content,
            Paragraph(f"{qty:.2f}".replace(".", ","), cell_center),
            Paragraph(iva_str, cell_center),
            Paragraph(format_currency(prezzo), cell_right),
            Paragraph(format_currency(importo), cell_right)
        ])
    
    # Creazione Tabella Principale
    items_table = Table(
        table_data,
        colWidths=[14 * mm, 18 * mm, 104 * mm, 10 * mm, 10 * mm, 16 * mm, 18 * mm],
        repeatRows=2
    )
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.black),
        ('LINEBELOW', (0, 1), (-1, 1), 0.75, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4 * mm))
    
    # 4. BLOCCO FINALE (PAGAMENTO A SX, TOTALI A DX)
    totale_fattura = tot_imponibile + tot_iva_22
    payment_method = str(client_data.get('modalita_pagamento', 'RIMESSA DIRETTA'))
    if pd.isna(payment_method) or payment_method.strip() == '' or payment_method.lower() == 'nan':
        payment_method = 'RIMESSA DIRETTA'
    
    pay_table = Table(
        [
            [Paragraph("<b>Modalità di pagamento</b>", cell_bold)],
            [Paragraph(f"<b>{payment_method}</b>", cell_bold)],
            [""],
            [""]
        ],
        colWidths=[110 * mm],
        rowHeights=[4.5 * mm, 6 * mm, 5 * mm, 5 * mm]
    )
    pay_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    
    totals_table = Table(
        [
            [Paragraph("<b>Imponibile</b>", cell_regular), Paragraph(format_currency(tot_imponibile), cell_bold)],
            [Paragraph("Spese di spedizione", cell_regular), Paragraph("€ -", cell_regular)],
            [Paragraph("IVA ES. ART. 9", cell_regular), Paragraph(format_currency(tot_iva_art9) if tot_iva_art9 > 0 else "€ -", cell_regular)],
            [Paragraph("IVA 22,0%", cell_regular), Paragraph(format_currency(tot_iva_22), cell_regular)],
            [Paragraph("IVA", cell_regular), Paragraph("€ -", cell_regular)],
            [Paragraph("<b>TOTALE FATTURA</b>", cell_bold), Paragraph(f"<b>{format_currency(totale_fattura)}</b>", cell_bold)],
            [Paragraph("(S.E.&O.)", cell_center), ""]
        ],
        colWidths=[42 * mm, 38 * mm],
        rowHeights=[4.5 * mm] * 7
    )
    totals_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ('LINEABOVE', (0, 5), (-1, 5), 1, colors.black),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor("#f1f5f9")),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('SPAN', (0, 6), (1, 6)),
    ]))
    
    footer_wrapper = Table(
        [[pay_table, totals_table]],
        colWidths=[110 * mm, 80 * mm]
    )
    footer_wrapper.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    elements.append(KeepTogether(footer_wrapper))
    
    doc.build(elements, canvasmaker=NumberedCanvas)
