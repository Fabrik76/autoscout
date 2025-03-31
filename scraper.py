from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
import time
import pandas as pd
import re

def estrai_da_indirizzo(testo):
    risultato = {
        'indirizzo': testo,
        'citta': 'N/D',
        'provincia': 'N/D',
        'cap': 'N/D'
    }
    
    if testo == 'N/D':
        return risultato
    
    cap_match = re.search(r'(?:IT-)?(\d{5})\b', testo)
    if cap_match:
        risultato['cap'] = cap_match.group(1)
        testo = testo.replace(cap_match.group(0), '').strip()
    
    provincia_match = re.search(r'\((.*?)\)', testo)
    if provincia_match:
        risultato['provincia'] = provincia_match.group(1).strip()
        testo = testo.replace(provincia_match.group(0), '').strip()
    else:
        parts = [p.strip() for p in testo.split('-') if p.strip()]
        if parts and len(parts[-1]) == 2 and parts[-1].isalpha():
            risultato['provincia'] = parts[-1]
            testo = testo.replace(parts[-1], '').strip()
    
    if risultato['provincia'] != 'N/D':
        citta_match = re.search(r'([^\d\-\(\)]+)(?=\s*[-\(]?\s*'+risultato['provincia']+r')', testo)
        if citta_match:
            risultato['citta'] = citta_match.group(1).strip(' -•')
    elif risultato['cap'] != 'N/D':
        citta_match = re.search(r'(?:IT-)?'+risultato['cap']+r'\s*([^\d\-\(\)]+)', testo)
        if citta_match:
            risultato['citta'] = citta_match.group(1).strip(' -•')
    
    testo = re.sub(r'\s*[•\-]\s*$', '', testo.strip())
    testo = ' '.join(testo.split())
    risultato['indirizzo'] = testo if testo else 'N/D'
    
    return risultato

def ricerca_auto_personalizzata(marca, modello=None, anno_da=None, anno_a=None, prezzo_da=None, prezzo_a=None):
    driver = None
    dati_ricerca = []
    pagina_corrente = 1

    try:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')  # Browser visibile a schermo intero
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(1280, 720)
        driver.get("https://www.autoscout24.it")

        # Gestione cookies
        try:
            cookie_accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accetta')]"))
            )
            cookie_accept_button.click()
        except TimeoutException:
            pass

        # Ricerca auto
        try:
            marca_dropdown = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "make"))
            )
            marca_dropdown.click()
            marca_input = driver.find_element(By.ID, "make")
            marca_input.send_keys(marca)
            time.sleep(1)
        except TimeoutException:
            raise Exception("Dropdown della marca non trovato")

        if modello:
            try:
                modello_dropdown = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "model"))
                )
                modello_dropdown.click()
                modello_input = driver.find_element(By.ID, "model")
                modello_input.send_keys(modello)
                time.sleep(1)
            except TimeoutException:
                pass

        try:
            ricerca_button = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "hf-searchmask-form__filter__search-button"))
            )
            ricerca_button.click()
            time.sleep(5)
        except (NoSuchElementException, TimeoutException) as e:
            raise Exception(f"Errore durante l'avvio della ricerca: {e}")

        # Applica filtri aggiuntivi (anno, prezzo, ecc.)
        if anno_da:
            try:
                anno_da_field_icon = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "fieldset:nth-of-type(2) div.InputPair_inputPairLeft__V2X61 svg"))
                )
                ActionChains(driver).move_to_element(anno_da_field_icon).click().perform()
                time.sleep(1)
                
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "firstRegistrationFrom-input-suggestions"))
                )
                
                indice_da = 2025 - int(anno_da)
                anno_da_elemento = WebDriverWait(driver, 25).until(
                    EC.element_to_be_clickable((By.ID, f"firstRegistrationFrom-input-suggestion-{indice_da}"))
                )
                ActionChains(driver).move_to_element(anno_da_elemento).click().perform()
            except Exception:
                pass

        if anno_a:
            try:
                anno_a_field_icon = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "fieldset:nth-of-type(2) div.InputPair_inputPairRight__9r948 svg"))
                )
                ActionChains(driver).move_to_element(anno_a_field_icon).click().perform()
                time.sleep(1)
                
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "firstRegistrationTo-input-suggestions"))
                )
                
                indice_a = 2025 - int(anno_a)
                anno_a_elemento = WebDriverWait(driver, 25).until(
                    EC.element_to_be_clickable((By.ID, f"firstRegistrationTo-input-suggestion-{indice_a}"))
                )
                ActionChains(driver).move_to_element(anno_a_elemento).click().perform()
            except Exception:
                pass

        if prezzo_da is not None:
            try:
                prezzo_da_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "price-from"))
                )
                prezzo_da_button.click()
                time.sleep(1)
                
                prezzo_da_suggestions = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "price-from-suggestions"))
                )
                
                prezzo_da_options = prezzo_da_suggestions.find_elements(By.TAG_NAME, "li")
                found_option = None
                
                for option in prezzo_da_options:
                    option_text = option.text.strip()
                    option_value_str = ''.join(filter(str.isdigit, option_text))
                    try:
                        option_value = int(option_value_str)
                        if option_value == prezzo_da:
                            found_option = option
                            break
                    except ValueError:
                        continue

                if found_option:
                    found_option.click()
                else:
                    prezzo_da_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#price-from-suggestions input[type='text']"))
                    )
                    prezzo_da_input.send_keys(str(prezzo_da))
            except Exception:
                pass

        if prezzo_a is not None:
            try:
                prezzo_a_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "price-to"))
                )
                prezzo_a_button.click()
                time.sleep(1)
                
                prezzo_a_suggestions_ul = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "price-to-suggestions"))
                )
                
                prezzo_a_options = prezzo_a_suggestions_ul.find_elements(By.TAG_NAME, "li")
                found_option = None
                
                for option in prezzo_a_options:
                    option_text = option.text.strip()
                    option_value_str = ''.join(filter(str.isdigit, option_text))
                    try:
                        option_value = int(option_value_str)
                        if option_value == prezzo_a:
                            found_option = option
                            break
                    except ValueError:
                        continue

                if found_option:
                    found_option.click()
                else:
                    prezzo_a_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#price-to-suggestions input[type='text']"))
                    )
                    prezzo_a_input.send_keys(str(prezzo_a))
            except Exception:
                pass

        # Estrazione annunci
        while True:
            time.sleep(3)
            annunci = driver.find_elements(By.CSS_SELECTOR, "article.cldt-summary-full-item.listing-impressions-tracking.list-page-item.ListItem_article__qyYw7")

            if not annunci:
                break

            for annuncio in annunci:
                try:
                    data_attributes = {
                        'id_annuncio': annuncio.get_attribute('id') or 'N/D',
                        'data_make': annuncio.get_attribute('data-make') or 'N/D',
                        'data_model': annuncio.get_attribute('data-model') or 'N/D',
                        'data_price': annuncio.get_attribute('data-price') or 'N/D',
                        'data_mileage': annuncio.get_attribute('data-mileage') or 'N/D',
                        'data_fuel_type': annuncio.get_attribute('data-fuel-type') or 'N/D',
                        'data_first_registration': annuncio.get_attribute('data-first-registration') or 'N/D',
                        'data_seller_type': annuncio.get_attribute('data-seller-type') or 'N/D',
                        'data_listing_zip_code': annuncio.get_attribute('data-listing-zip-code') or 'N/D',
                        'data_vehicle_type': annuncio.get_attribute('data-vehicle-type') or 'N/D',
                        'data_transmission': annuncio.get_attribute('data-transmission') or 'N/D',
                        'data_power': annuncio.get_attribute('data-power') or 'N/D'
                    }

                    dati_visibili = {
                        'titolo_completo': estrai_testo(annuncio, "a.ListItem_title__ndA4s.ListItem_title_new_design__QIU2b.Link_link__Ajn7I h2"),
                        'prezzo': estrai_testo(annuncio, "p.Price_price__APlgs.PriceAndSeals_current_price__ykUpx"),
                        'anno': estrai_testo(annuncio, "span[data-testid='VehicleDetails-calendar']"),
                        'km': estrai_testo(annuncio, "span[data-testid='VehicleDetails-mileage']", True),
                        'cambio': estrai_testo(annuncio, "span[data-testid='VehicleDetails-transmission']"),
                        'carburante': estrai_testo(annuncio, "span[data-testid='VehicleDetails-fuel']"),
                        'potenza': estrai_testo(annuncio, "span[data-testid='VehicleDetails-power']"),
                        'inserzionista': estrai_testo(annuncio, "span.SellerInfo_name__lX2Ve"),
                        'indirizzo_venditore': estrai_testo(annuncio, "span.SellerInfo_address__leRMu"),
                        'localita': estrai_testo(annuncio, "span[data-testid='VehicleDetails-registration']"),
                        'cilindrata': estrai_testo(annuncio, "span[data-testid='VehicleDetails-cubicCapacity']"),
                        'porte': estrai_testo(annuncio, "span[data-testid='VehicleDetails-doors']"),
                        'data_pubblicazione': estrai_testo(annuncio, "span.ListItem_date__DqVDw"),
                        'link': estrai_attributo(annuncio, "a.ListItem_title__ndA4s.ListItem_title_new_design__QIU2b.Link_link__Ajn7I", 'href')
                    }

                    marca_auto = dati_visibili['titolo_completo'].split()[0] if dati_visibili['titolo_completo'] != 'N/D' else data_attributes['data_make']
                    modello_auto = " ".join(dati_visibili['titolo_completo'].split()[1:]) if dati_visibili['titolo_completo'] != 'N/D' else data_attributes['data_model']

                    prezzo_formattato = 'N/D'
                    if dati_visibili['prezzo'] != 'N/D':
                        prezzo_numerico = re.sub(r'[^\d]', '', dati_visibili['prezzo'])
                        try:
                            prezzo_formattato = f"€{int(prezzo_numerico):,}".replace(",", ".")
                        except:
                            prezzo_formattato = dati_visibili['prezzo']
                    elif data_attributes['data_price'] != 'N/D':
                        prezzo_formattato = f"€{int(data_attributes['data_price']):,}".replace(",", ".")
                    
                    prezzo_numerico = 'N/D'
                    if dati_visibili['prezzo'] != 'N/D':
                        prezzo_numerico = re.sub(r'[^\d]', '', dati_visibili['prezzo'])
                    elif data_attributes['data_price'] != 'N/D':
                        prezzo_numerico = data_attributes['data_price']
                    
                    km_pulito = dati_visibili['km'].replace("km", "").replace(".", "").strip() if dati_visibili['km'] != 'N/D' else data_attributes['data_mileage']
                    
                    kw, cv = 'N/D', 'N/D'
                    if dati_visibili['potenza'] != 'N/D':
                        if "kW" in dati_visibili['potenza'] and "CV" in dati_visibili['potenza']:
                            kw = dati_visibili['potenza'].split("kW")[0].strip()
                            cv = dati_visibili['potenza'].split("(")[1].replace("CV)", "").strip()
                        else:
                            kw = cv = dati_visibili['potenza']
                    elif data_attributes['data_power'] != 'N/D':
                        kw = cv = data_attributes['data_power']

                    tipo_venditore = "Privato" if data_attributes['data_seller_type'] == 'p' else "Concessionario"

                    indirizzo_completo = dati_visibili['indirizzo_venditore']
                    cap = data_attributes['data_listing_zip_code']
                    
                    dati_indirizzo = estrai_da_indirizzo(indirizzo_completo)
                    
                    if dati_indirizzo['cap'] == 'N/D' and cap != 'N/D':
                        dati_indirizzo['cap'] = cap
                    
                    if (dati_indirizzo['citta'] == 'N/D' or dati_indirizzo['provincia'] == 'N/D') and dati_visibili['localita'] != 'N/D':
                        localita_dati = estrai_da_indirizzo(dati_visibili['localita'])
                        if dati_indirizzo['citta'] == 'N/D':
                            dati_indirizzo['citta'] = localita_dati['citta']
                        if dati_indirizzo['provincia'] == 'N/D':
                            dati_indirizzo['provincia'] = localita_dati['provincia']
                    
                    indirizzo_venditore = dati_indirizzo['indirizzo']
                    citta = dati_indirizzo['citta']
                    provincia = dati_indirizzo['provincia']
                    cap = dati_indirizzo['cap']

                    dati_ricerca.append({
                        "ID Annuncio": data_attributes['id_annuncio'],
                        "Marchio": marca_auto,
                        "Modello": modello_auto,
                        "Titolo": dati_visibili['titolo_completo'],
                        "Prezzo": prezzo_formattato,
                        "Prezzo (numerico)": prezzo_numerico,
                        "Chilometraggio (km)": km_pulito,
                        "Cambio": dati_visibili['cambio'] if dati_visibili['cambio'] != 'N/D' else data_attributes['data_transmission'],
                        "Anno immatricolazione": dati_visibili['anno'],
                        "Data prima immatricolazione": data_attributes['data_first_registration'],
                        "Alimentazione": dati_visibili['carburante'] if dati_visibili['carburante'] != 'N/D' else data_attributes['data_fuel_type'],
                        "Potenza (kW)": kw,
                        "Potenza (CV)": cv,
                        "Cilindrata": dati_visibili['cilindrata'],
                        "Numero porte": dati_visibili['porte'],
                        "Tipo veicolo": data_attributes['data_vehicle_type'],
                        "Inserzionista": dati_visibili['inserzionista'],
                        "Tipo venditore": tipo_venditore,
                        "Indirizzo venditore": indirizzo_venditore,
                        "Città": citta,
                        "Provincia": provincia,
                        "CAP": cap,
                        "Data pubblicazione": dati_visibili['data_pubblicazione'],
                        "Link annuncio": dati_visibili['link']
                    })

                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    print(f"Errore durante l'estrazione dei dati da un annuncio: {e}")
                    continue

            try:
                pulsante_successiva = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Vai alla pagina successiva']"))
                )
                pulsante_successiva.click()
                pagina_corrente += 1
                time.sleep(3)
            except:
                break

        return dati_ricerca

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def estrai_testo(elemento, selettore, pulisci=False):
    try:
        testo = elemento.find_element(By.CSS_SELECTOR, selettore).text.strip()
        if pulisci:
            testo = testo.replace(".", "").replace("€", "").strip()
        return testo if testo else 'N/D'
    except:
        return 'N/D'

def estrai_attributo(elemento, selettore, attributo):
    try:
        attr = elemento.find_element(By.CSS_SELECTOR, selettore).get_attribute(attributo)
        return attr if attr else 'N/D'
    except:
        return 'N/D'