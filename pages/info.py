#Info sui dati

import streamlit as st

st.set_page_config(
        page_title="Info sui dati",
)

def show():
    st.markdown("""
    <div style='text-align:center; margin-top: 1rem; margin-bottom: 2rem;'>
        <h2 style="color:#15aabf; margin-bottom:0.2em;">Info e metodologie</h2>
        <div style="height:3px; width:180px; background:linear-gradient(90deg,#3b82f6,#22c55e,#06b6d4); margin:1rem auto; border-radius:2px;"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    Questa dashboard esplorativa presenta l'analisi dei principali dati sugli incidenti stradali in Italia dal 2019 al 2023.<br>
    Puoi navigare tra le diverse sezioni tramite la sidebar a sinistra.<br>
    <br>
    Approfondimenti e dettagli sul dataset, sulle fonti e sulle metodologie utilizzate sono riportati qui di seguito.  
    Per domande o suggerimenti puoi contattarmi via GitHub o email.
    """, unsafe_allow_html=True)

    # Altro testo o immagini di esempio:
    st.markdown("""
    ### Struttura della dashboard
    - **Panoramica**: Statistiche principali e trend generali
    - **Geografia**: Mappa e distribuzione territoriale degli incidenti
    - **Giorni e orari**: Analisi temporale delle occorrenze
    - **Veicoli**: Tipologie e coinvolgimenti
    - **Profilo conducenti**: Dati demografici, età e sesso

    ---
    **Fonte dati:** Istat.  
    **Autore:** Francesco Botrugno - 2025  
    """)

