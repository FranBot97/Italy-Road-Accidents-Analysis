# Info sui dati

import streamlit as st

st.set_page_config(
    page_title="Info sui dati",
)


def show():
    st.markdown("""
    <div style='text-align:center; margin-top: 1rem; margin-bottom: 2rem;'>
        <h2 style="color:#1f2937; margin-bottom:0.2em;">Info e metodologie</h2>
        <div style="height:3px; width:180px; background:linear-gradient(90deg,#3b82f6,#22c55e,#06b6d4); margin:1rem auto; border-radius:2px;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Fonte dati
    st.markdown("### Fonte dati")
    st.markdown("""
    I dati utilizzati in questa dashboard provengono dalle **indagini ISTAT** relative agli incidenti stradali 
    con lesioni a persone (feriti e morti) nel periodo **2019-2023**.
    
    **Fonte ufficiale:** [ISTAT - Rilevazione degli incidenti stradali con lesioni a persone](https://www.istat.it/microdati/rilevazione-degli-incidenti-stradali-con-lesioni-a-persone-2/)
    """)

    st.markdown("---")

    # Gestione dati
    st.markdown("### Elaborazione dei dati")
    st.markdown("""
    I dati originali in formato `.txt` sono stati processati e ottimizzati per l'analisi. 
    Il dataset finale include i seguenti attributi:
    """)
    
    st.code("""
anno
provincia
comune
giorno
localizzazione_incidente
condizioni_meteorologiche
fondo_stradale
natura_incidente
tipo_veicolo_a
veicolo__a___sesso_conducente
veicolo__a___et__conducente
tipo_veicoli__b_
veicolo__b___sesso_conducente
veicolo__b___et__conducente
morti_entro_24_ore
morti_entro_30_giorni
feriti
Ora
tipo_veicolo__c_
    """, language=None)

    st.markdown("""
    **Operazioni eseguite:**
    - Rimozione di righe con valori mancanti
    - Integrazione con dati demografici (popolazione regioni/province da ISTAT 2023)
    - Inserimento dei dati sorgente e dei metadati in un database relazionale
    """)

    st.markdown("---")

    # Struttura dashboard
    st.markdown("### Struttura e dettagli Dashboard")
    
    st.markdown("#### Panoramica")
    st.markdown("""
    Statistiche generali e trend del periodo 2019-2023.
    
    Il **tasso di mortalità** è calcolato come `#morti / #incidenti * 100`. Si considerano sia i morti entro 24 ore che i morti entro 30 giorni. Sono esclusi i feriti.
    
    **Suddivisione geografica:**
    - **Nord:** Piemonte, Valle d'Aosta, Lombardia, Trentino-Alto Adige, Veneto, 
      Friuli-Venezia Giulia, Liguria, Emilia-Romagna
    - **Centro:** Toscana, Umbria, Marche, Lazio
    - **Sud e Isole:** Abruzzo, Molise, Campania, Puglia, Basilicata, Calabria, Sicilia, Sardegna
    """)
    
    st.markdown("#### Distribuzione Geografica")
    st.markdown("""
    Mappa interattiva e distribuzione territoriale degli incidenti per regioni e province.
    
    I dati sulla popolazione utilizzati per calcolare gli incidenti ogni 100k abitanti 
    sono riferiti all'anno 2023 (fonte ISTAT).
    """)
    
    st.markdown("#### Giorni e orari")
    st.markdown("""
    Analisi della distribuzione temporale degli incidenti e del numero di morti per giorno della settimana e fascia oraria.
    """)
    
    st.markdown("#### Veicoli")
    st.markdown("""
    Analisi dei veicoli coinvolti negli incidenti.
    
    **Nota metodologica:** I dati originali includevano informazioni fino a 3 veicoli per incidente (A, B e C). 
    Nella maggior parte dei casi il veicolo C non era presente, perciò l'analisi effettuata si limita solo ai veicoli A e B.
    
    I tipi di veicoli mostrati nella heatmap derivano da un accorpamento in macro categorie:
    - **Autoveicoli:** Autovettura privata, con rimorchio, pubblica, di soccorso/polizia
    - **Motoveicoli:** Ciclomotore, motociclo (solo o con passeggero), motocarro, motofurgone
    - **Mezzi pesanti:** Autocarro, autotreno con rimorchio, autosnodato, autoarticolato, 
      trattore stradale, motrice, trattore agricolo
    - **Trasporto pubblico:** Autobus/filobus urbano, autobus extraurbano, tram
    - **Biciclette:** Velocipede, bicicletta elettrica
    - **Monopattini:** Monopattino elettrico
    """)
    
    st.markdown("#### Profilo conducenti")
    st.markdown("""
    Analisi demografica dei conducenti coinvolti per età e per sesso.
    """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6b7280; font-size: 14px;'>
        <b>Fonte dati:</b> <a href="https://www.istat.it/microdati/rilevazione-degli-incidenti-stradali-con-lesioni-a-persone-2/" target="_blank">ISTAT - Incidenti stradali</a><br>
        <b>Autore:</b> Francesco Botrugno<br>
        <b>Anno:</b> 2025
    </div>
    """, unsafe_allow_html=True)