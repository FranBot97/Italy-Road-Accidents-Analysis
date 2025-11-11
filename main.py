import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json
import plotly.io as pio
import numpy as np
import matplotlib.colors as mcolors
from plotly.subplots import make_subplots
from Utils import utils
import Sections.overview as overview
import Sections.geography as geography
import Sections.time as time 
import Sections.drivers as drivers
import Sections.vehicles as vehicles

# =========================
# CONFIGURAZIONE PAGINA 
# =========================

st.set_page_config(
    page_title="Incidenti Stradali Italia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nascondi menu header
st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")

# style
pio.templates.default = "plotly_white"


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")


# =========================
# PAGINA 1: DASHBOARD PRINCIPALE
# =========================
def page_dashboard():
    # ---------- HEADER ----------
    st.markdown("""
    <div style="text-align:center; padding: 1.8rem 0;">
      <h1 style="color:#1f2937; font-size:3rem; margin:0;">Dashboard Incidenti Stradali</h1>
   </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; max-width:650px; margin:0 auto 2rem auto;">
        Questa dashboard interattiva permette di esplorare e analizzare i dati sugli incidenti<br>
        stradali in Italia fra il 2019 e il 2023 che hanno riportato lesioni a persone.<br>
        Per maggiori informazioni sui dati e metodologie consultare la sezione <a href="/page_info">Info e metodologie</a>
    </div>
    <div style="height:3px; width:220px; background:linear-gradient(90deg,#3b82f6,#22c55e,#06b6d4); margin:1rem auto; border-radius:2px;"></div>
 
    """, unsafe_allow_html=True)

    # ---------- SIDEBAR ----------
    st.sidebar.markdown("""
    <div class="sidebar-title">Sezioni</div>
    <ul class="sidebar-links">
      <li><a href="#panoramica">Panoramica</a></li>
      <li><a href="#geografia">Distribuzione Geografica</a></li>
      <li><a href="#analisi-temporale">Giorni e orari</a></li>
      <li><a href="#veicoli">Veicoli</a></li>
      <li><a href="#conducenti">Profilo conducenti</a></li> 
    </ul>
    """, unsafe_allow_html=True)

    # ---------- SEZIONE 1: OVERVIEW ----------
    st.markdown("<a id='panoramica'></a>", unsafe_allow_html=True)
    overview.show()
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

    # ---------- SEZIONE 2: GEOGRAFIA ----------
    st.markdown("<a id='geografia'></a>", unsafe_allow_html=True)
    geography.show()
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

    # ---------- SEZIONE 3: TEMPO ----------
    st.markdown("<a id='analisi-temporale'></a>", unsafe_allow_html=True)
    time.show()
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

    # ---------- SEZIONE 4: VEICOLI ----------
    st.markdown("<a id='veicoli'></a>", unsafe_allow_html=True)
    vehicles.show()
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

    # ---------- SEZIONE 5: CONDUCENTI ----------
    st.markdown("<a id='conducenti'></a>", unsafe_allow_html=True)
    drivers.show()
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

    # ---------- FOOTER ----------
    st.markdown("""
        <div style="text-align: center; padding: 3rem 0 1rem 0;">
            <div style="height: 2px; width: 100%; background: linear-gradient(90deg, #667eea, #764ba2); margin: 2rem 0;"></div>
            <p style="color: #666; font-size: 0.9rem;">
                Francesco Botrugno •
                <span style="color: #0ea5e9;"><a href="https://github.com/FranBot97/Italy-Road-Accidents-Analysis">Github source</a></span>
            </p>
        </div>
    """, unsafe_allow_html=True)


# =========================
# PAGINA 2: INFO / METODOLOGIE
# =========================
def page_info():
    """
    Questa funzione richiama la pagina info.
    Assicurati che in pages/info.py ci sia qualcosa tipo:

    import streamlit as st

    def show():
        st.title("Info e metodologie")
        ...
    """
    # import locale per evitare problemi di packaging
    import pages.info as info
    info.show()


# =========================
# NAVIGAZIONE A 2 PAGINE
# =========================

pages = [
    st.Page(page_dashboard, title="Dashboard Incidenti Stradali", icon="📊"),
    st.Page(page_info,      title="Info e metodologie",          icon="🔍"),
]

nav = st.navigation(pages)
nav.run()
