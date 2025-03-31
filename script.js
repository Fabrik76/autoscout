$(document).ready(function() {
    let currentSearchId = null;
    let dataTable = null;
    
    // Invia il form di ricerca
    $('#searchForm').submit(function(e) {
        e.preventDefault();
        
        const marca = $('#marca').val();
        const modello = $('#modello').val();
        const anno_da = $('#anno_da').val();
        const anno_a = $('#anno_a').val();
        const prezzo_da = $('#prezzo_da').val();
        const prezzo_a = $('#prezzo_a').val();
        
        if (!marca) {
            alert('La marca è obbligatoria!');
            return;
        }
        
        $('#searchBtn').prop('disabled', true).text('Ricerca in corso...');
        $('#statusMessage').html('<div class="loading">Scraping in corso... Guarda la finestra Chrome</div>');
        
        $.ajax({
            url: '/search',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                marca: marca,
                modello: modello,
                anno_da: anno_da,
                anno_a: anno_a,
                prezzo_da: prezzo_da,
                prezzo_a: prezzo_a
            }),
            success: function(response) {
                currentSearchId = new Date().getTime();
                $('#resultsPanel').show();
                checkResults();
            },
            error: function() {
                alert('Errore durante l\'avvio della ricerca');
                $('#searchBtn').prop('disabled', false).text('Avvia Ricerca');
            }
        });
    });
    
    // Controlla periodicamente i risultati
    function checkResults() {
        $.get('/results', function(data) {
            if (data && data.length > 0) {
                displayResults(data);
                $('#statusMessage').html('<div class="success">Ricerca completata! ' + data.length + ' risultati trovati.</div>');
                $('#searchBtn').prop('disabled', false).text('Avvia Ricerca');
            } else {
                setTimeout(checkResults, 5000);
            }
        }).fail(function() {
            setTimeout(checkResults, 5000);
        });
    }
    
    // Mostra i risultati nella tabella
    function displayResults(data) {
        if (dataTable) {
            dataTable.destroy();
        }
        
        $('#resultsBody').empty();
        
        data.forEach(function(item) {
            const row = `
                <tr>
                    <td>${item.Marchio || 'N/D'}</td>
                    <td>${item.Modello || 'N/D'}</td>
                    <td>${item.Prezzo || 'N/D'}</td>
                    <td>${item['Anno immatricolazione'] || 'N/D'}</td>
                    <td>${item['Chilometraggio (km)'] || 'N/D'}</td>
                    <td>${item.Cambio || 'N/D'}</td>
                    <td>${item.Alimentazione || 'N/D'}</td>
                    <td><a href="${item['Link annuncio']}" target="_blank">Dettagli</a></td>
                </tr>
            `;
            $('#resultsBody').append(row);
        });
        
        dataTable = $('#resultsTable').DataTable({
            pageLength: 10,
            language: {
                url: '//cdn.datatables.net/plug-ins/1.11.5/i18n/it-IT.json'
            }
        });
    }
    
    // Esporta i risultati in CSV
    $('#exportCsv').click(function() {
        window.location.href = '/download/' + $('select[name="resultsFile"]').val();
    });
    
    // Aggiorna i risultati
    $('#refreshResults').click(function() {
        $('#statusMessage').html('<div class="loading">Aggiornamento risultati...</div>');
        $.get('/results', function(data) {
            if (data && data.length > 0) {
                displayResults(data);
                $('#statusMessage').html('<div class="success">Risultati aggiornati</div>');
            } else {
                $('#statusMessage').html('<div class="info">Nessun risultato disponibile</div>');
            }
        });
    });
    
    // Interrompi lo scraping
    $('#stopBtn').click(function() {
        $.ajax({
            url: '/stop',
            method: 'POST',
            success: function() {
                alert('Scraping interrotto');
                $('#searchBtn').prop('disabled', false).text('Avvia Ricerca');
            }
        });
    });
});