from flask import Flask, render_template, request, jsonify, send_from_directory
from scraper import ricerca_auto_personalizzata
import threading
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='static')

# Configurazione
OUTPUT_FOLDER = 'output'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    
    # Avvia lo scraping in un thread separato
    thread = threading.Thread(
        target=run_scraping,
        args=(data,),
        daemon=True  # Permette al thread di continuare dopo la chiusura dell'app
    )
    thread.start()
    
    return jsonify({
        "status": "started", 
        "message": "Scraping avviato - Guarda la finestra del browser Chrome"
    })

def run_scraping(params):
    marca = params.get('marca')
    modello = params.get('modello')
    anno_da = params.get('anno_da')
    anno_a = params.get('anno_a')
    prezzo_da = params.get('prezzo_da')
    prezzo_a = params.get('prezzo_a')
    
    # Esegui lo scraping
    risultati = ricerca_auto_personalizzata(
        marca=marca,
        modello=modello if modello else None,
        anno_da=anno_da if anno_da else None,
        anno_a=anno_a if anno_a else None,
        prezzo_da=prezzo_da if prezzo_da else None,
        prezzo_a=prezzo_a if prezzo_a else None
    )
    
    if risultati:
        # Genera nome file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"autoscout_{marca}_{timestamp}.csv"
        percorso_file = os.path.join(OUTPUT_FOLDER, nome_file)
        
        # Salva i dati in CSV
        colonne = [
            "ID Annuncio", "Marchio", "Modello", "Titolo", "Prezzo", "Prezzo (numerico)",
            "Chilometraggio (km)", "Cambio", "Anno immatricolazione", "Data prima immatricolazione",
            "Alimentazione", "Potenza (kW)", "Potenza (CV)", "Cilindrata", "Numero porte",
            "Tipo veicolo", "Inserzionista", "Tipo venditore", "Indirizzo venditore", 
            "Città", "Provincia", "CAP", "Data pubblicazione", "Link annuncio"
        ]
        
        df = pd.DataFrame(risultati, columns=colonne)
        df.to_csv(percorso_file, index=False, encoding='utf-8-sig', sep=';')
        
        # Salva anche i risultati in formato JSON per la visualizzazione
        json_file = os.path.join(OUTPUT_FOLDER, f"autoscout_{marca}_{timestamp}.json")
        df.to_json(json_file, orient='records', force_ascii=False)
    else:
        print("Nessun risultato trovato")

@app.route('/results')
def results():
    # Mostra l'ultimo file di risultati generato
    files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.json')]
    if not files:
        return "Nessun risultato disponibile"
    
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(OUTPUT_FOLDER, x)))
    return send_from_directory(OUTPUT_FOLDER, latest_file)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)