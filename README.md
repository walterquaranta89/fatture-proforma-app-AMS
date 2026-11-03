# Web App Generatore Fatture Pro Forma
**Azienda:** CICCIMARRA Carlo & Figli srl  
**Destinatario:** Ufficio Amministrazione

---

## 📋 Descrizione del Software
Questa applicazione web permette di generare in pochissimi secondi tutte le fatture pro forma del mese per ciascun cliente a partire dall'elenco esportato dal gestionale trasporti (in formato Excel `.xlsx` o `.csv`).

### Caratteristiche Principali:
1. **Raggruppamento Intelligente per Cliente:** Se un cliente ha 1 o 20 viaggi eseguiti nel mese, il software crea **una sola fattura pro forma** contenente tutti i viaggi come righe separate nel corpo del documento.
2. **Layout Fedele al 100%:** La grafica, i riquadri, le diciture, il logo e i campi sono modellati esattamente sulla fattura cartacea ufficiale di *CICCIMARRA Carlo & Figli srl*.
3. **Calcoli Automatici:** Calcola in automatico l'imponibile per riga (`Quantità * Prezzo`), la suddivisione dell'IVA (22% o Art. 9 se esente), e il Totale Fattura.
4. **Data e Numerazione Flessibili:**
   - La data di emissione è impostata di default sul giorno corrente (data di caricamento), ma modificabile con un click.
   - Il numero iniziale progressivo è impostabile (es. 1, 10, ecc.) e viene incrementato per ciascun cliente.
5. **Download Istantaneo:** Puoi scaricare singolarmente i PDF generati o scaricare un unico archivio compresso **ZIP** contenente tutte le fatture nominate con ordine:
   `Proforma_01_AGENCY_MANAGEMENT_SHIPPING_10_2026.pdf`

---

## 🚀 Come Avviare l'Applicazione
È sufficiente fare **doppio clic** sul file:
👉 `avvia_app.bat`

Si aprirà automaticamente il tuo browser predefinito all'indirizzo:
`http://127.0.0.1:5000`

---

## 📊 Colonne Supportate nel File Excel / CSV
Il sistema accetta i seguenti nomi di colonna (non fa distinzione tra maiuscole, minuscole o accenti):

| Nome Colonna | Descrizione | Obbligatorio? |
| :--- | :--- | :---: |
| **Ragione Sociale** | Nome/intestazione del cliente o committente | **Sì** |
| **Indirizzo** | Indirizzo della sede legale/operativa | No (consigliato) |
| **CAP** | Codice di avviamento postale | No |
| **Città** | Comune di residenza del cliente | No |
| **Prov** | Sigla o nome della provincia | No |
| **Tel** | Recapito telefonico | No |
| **P.IVA** | Partita IVA o Codice Fiscale | No (consigliato) |
| **Codice COF** | Codice cliente COF | No |
| **Modalità Pagamento** | Es. *RIMESSA DIRETTA*, *BONIFICO 30 GG* (default: RIMESSA DIRETTA) | No |
| **IBAN** | Codice IBAN per il pagamento (es. *IT60X0542811101000000123456*) | No |
| **DDT Numero** | Numero progressivo del DDT di trasporto emesso | No |
| **DDT Data** | Data di emissione del DDT | No |
| **Rif. Cliente** | Riferimento viaggio assegnato dal cliente | No |
| **Container** | Sigla/matricola del container trasportato | No |
| **Data Carico** | Data in cui il trasporto è stato eseguito | No |
| **Tratta** | Percorso (es. *Porto di Bari - Policoro*), oppure *Sosta*, *Pesa* | No |
| **UM** | Unità di misura (opzionale) | No |
| **Quantità** | Quantità (default: 1) | No |
| **Prezzo** | Prezzo unitario del trasporto/servizio | **Sì** |
| **IVA** | Aliquota (es. `22%`, oppure `Es. Art. 9`) | No (default 22%) |

> 💡 **Nota:** Cliccando sul pulsante **"Scarica File Excel di Esempio"** direttamente nella barra in alto della Web App, potrai scaricare un foglio già compilato e pronto all'uso come modello.
