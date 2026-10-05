import os
import io
import zipfile
import re
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from generator import create_proforma_pdf, format_currency

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "fatture_generate")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mappatura approfondita dei nomi colonna in caso di variazioni
COLUMN_ALIASES = {
    'ragione_sociale': [
        'ragione sociale', 'ragionesociale', 'cliente', 'committente', 'intestatario', 
        'nome cliente', 'denominazione', 'cliente committente', 'committente cliente'
    ],
    'indirizzo': ['indirizzo', 'via', 'sede', 'indirizzo sede', 'indirizzo cliente'],
    'cap': ['cap', 'c.a.p.', 'codice postale'],
    'citta': ['citta', 'città', 'comune', 'localita', 'località'],
    'prov': ['prov', 'prov.', 'provincia', 'pr'],
    'tel': ['tel', 'num. tel.', 'num tel', 'telefono', 'cellulare', 'contatto', 'num. tel'],
    'piva': ['piva', 'p.iva', 'partita iva', 'c. f./p. iva', 'c.f./p.iva', 'cf/piva', 'codice fiscale', 'cf', 'p_iva'],
    'codice_cof': ['codice cof', 'codice_cof', 'cof', 'codice', 'codice cliente'],
    'modalita_pagamento': ['modalita di pagamento', 'modalita pagamento', 'modalità di pagamento', 'modalità pagamento', 'pagamento', 'condizioni pagamento'],
    'ddt_numero': [
        'ddt', 'd.d.t.', 'd d t', 'numero ddt', 'num ddt', 'ddt_numero', 'n ddt', 'n. ddt', 
        'n° ddt', 'ddt n.', 'ddt n°', 'doc trasporto', 'bolla', 'num. ddt', 'n.ddt', 'ddt_num', 
        'nr ddt', 'numero bolla', 'n bolla', 'n. bolla'
    ],
    'ddt_data': ['data ddt', 'data d.d.t.', 'data d d t', 'ddt data', 'ddt_data', 'data bolla', 'data emissione ddt'],
    'rif_cliente': ['rif cliente', 'riferimento cliente', 'rif. cliente', 'rif viaggio', 'riferimento', 'booking', 'rif cliente viaggio', 'commessa'],
    'container': ['container', 'n container', 'n° container', 'n° container/merce', 'sigla container', 'matricola', 'matricola container', 'container merce'],
    'data_carico': ['data carico', 'data carico.', 'data trasporto', 'data viaggio', 'data esecuzione', 'data trasporto eseguito'],
    'tratta': ['tratta', 'percorso', 'tratta / sosta / pesa', 'descrizione trasporto', 'servizio', 'operazione', 'tratta percorso', 'tratta o sosta'],
    'quantita': ['quantita', 'quantità', 'qta', 'q.ta', 'q.tà', 'qty', 'quant'],
    'iva': ['iva', '% iva', 'aliquota iva', 'iva %', 'aliquota'],
    'prezzo': ['prezzo', 'importo unitario', 'prezzo unitario', 'tariffa', 'costo', 'imponibile riga']
}

def normalize_columns(df):
    clean_cols = {}
    for col in df.columns:
        # Pulisce stringa da simboli strani ma tiene caratteri alfanumerici
        norm_name = re.sub(r'[^a-zA-Z0-9àèéìòù]', ' ', str(col).lower()).strip()
        norm_name = re.sub(r'\s+', ' ', norm_name)
        
        matched_standard = None
        for standard_key, aliases in COLUMN_ALIASES.items():
            if norm_name in aliases or norm_name == standard_key:
                matched_standard = standard_key
                break
        
        if matched_standard:
            clean_cols[col] = matched_standard
        else:
            clean_cols[col] = norm_name
            
    df = df.rename(columns=clean_cols)
    return df

@app.route('/')
def index():
    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', today=today_str)

@app.route('/download-sample')
def download_sample():
    sample_path = os.path.join(BASE_DIR, "dati_trasporti_esempio.xlsx")
    return send_file(sample_path, as_attachment=True, download_name="Esempio_Elenco_Trasporti_5_Aziende.xlsx")

@app.route('/download-sample-csv')
def download_sample_csv():
    sample_path = os.path.join(BASE_DIR, "dati_trasporti_esempio.csv")
    return send_file(sample_path, as_attachment=True, download_name="Esempio_Elenco_Trasporti_5_Aziende.csv")

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file caricato.'}), 400
        
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({'error': 'Nessun file selezionato.'}), 400

    filename = uploaded_file.filename.lower()
    start_num_raw = request.form.get('start_number', '1')
    try:
        start_number = int(start_num_raw)
    except ValueError:
        start_number = 1
        
    invoice_date_str = request.form.get('invoice_date', '')
    if invoice_date_str:
        try:
            invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d')
        except ValueError:
            invoice_date = datetime.now()
    else:
        invoice_date = datetime.now()

    # Lettura file Excel o CSV
    try:
        if filename.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
                if len(df.columns) <= 1:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=',', encoding='utf-8')
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return jsonify({'error': 'Formato non supportato. Carica un file .xlsx o .csv'}), 400
    except Exception as e:
        return jsonify({'error': f"Errore durante la lettura del file: {str(e)}"}), 400

    if df.empty:
        return jsonify({'error': 'Il file caricato è privo di dati.'}), 400

    df = normalize_columns(df)

    if 'ragione_sociale' not in df.columns:
        return jsonify({
            'error': "Colonna 'Ragione Sociale' (o 'Cliente') non trovata nel file. Verifica le intestazioni."
        }), 400

    # Rimuovi righe con ragione sociale vuota
    df = df.dropna(subset=['ragione_sociale'])
    df['ragione_sociale'] = df['ragione_sociale'].astype(str).str.strip()
    df = df[df['ragione_sociale'] != '']

    if df.empty:
        return jsonify({'error': 'Nessun dato valido trovato dopo la pulizia.'}), 400

    # Pulizia cartella output per nuova sessione
    for f in os.listdir(OUTPUT_DIR):
        file_p = os.path.join(OUTPUT_DIR, f)
        if os.path.isfile(file_p):
            try:
                os.remove(file_p)
            except Exception:
                pass

    # Raggruppamento per cliente
    grouped = df.groupby('ragione_sociale', sort=False)
    
    invoices_summary = []
    current_num = start_number
    
    for client_name, group in grouped:
        client_dict = group.iloc[0].to_dict()
        transports = group.to_dict('records')
        
        num_str = f"{current_num:02d}"
        clean_client_slug = re.sub(r'[^a-zA-Z0-9]', '_', client_name)[:30].strip('_')
        month_year_str = invoice_date.strftime('%m_%Y')
        pdf_filename = f"Proforma_{num_str}_{clean_client_slug}_{month_year_str}.pdf"
        pdf_filepath = os.path.join(OUTPUT_DIR, pdf_filename)
        
        # Calcolo totali
        tot_imponibile = 0.0
        tot_iva = 0.0
        for r in transports:
            try:
                q = float(r.get('quantita', 1.0))
            except Exception:
                q = 1.0
            try:
                p = float(r.get('prezzo', 0.0))
            except Exception:
                p = 0.0
            subtot = q * p
            tot_imponibile += subtot
            
            aliquota = str(r.get('iva', '22%')).strip().lower()
            if not ('art' in aliquota or 'es' in aliquota or aliquota == '0' or aliquota == '0%'):
                tot_iva += subtot * 0.22
                
        tot_fattura = tot_imponibile + tot_iva

        # Generazione PDF
        try:
            create_proforma_pdf(
                client_dict,
                transports,
                pdf_filepath,
                invoice_number=num_str,
                invoice_date=invoice_date
            )
        except Exception as e:
            return jsonify({'error': f"Errore generazione fattura per {client_name}: {str(e)}"}), 500

        invoices_summary.append({
            'number': num_str,
            'client': client_name,
            'address': client_dict.get('indirizzo', ''),
            'transports_count': len(transports),
            'imponibile': format_currency(tot_imponibile),
            'iva': format_currency(tot_iva),
            'totale': format_currency(tot_fattura),
            'pdf_file': pdf_filename
        })
        current_num += 1

    return jsonify({
        'success': True,
        'count': len(invoices_summary),
        'invoices': invoices_summary
    })

@app.route('/download-pdf/<filename>')
def download_single_pdf(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return "File non trovato", 404

@app.route('/download-all-zip')
def download_all_zip():
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith('.pdf'):
                f_path = os.path.join(OUTPUT_DIR, f)
                zf.write(f_path, arcname=f)
    memory_file.seek(0)
    
    zip_name = f"Fatture_Proforma_Agency_Shipping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(memory_file, as_attachment=True, download_name=zip_name, mimetype='application/zip')

if __name__ == '__main__':
    print("Avvio App Web Fatturazione Pro Forma su http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
