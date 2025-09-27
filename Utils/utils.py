import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.colors as mcolors

# =========================
# FUNZIONI UTILITY
# =========================
@st.cache_data

def run_query(query):
    with sqlite3.connect("dbAccidents.db") as conn:
        return pd.read_sql_query(query, conn)

def load_yearly_accident_data_from_db():
    conn = sqlite3.connect("dbAccidents.db")
    query = """
    SELECT
        2000 + anno as Anno,
        COUNT(*) AS total_incidents,
        SUM(Morti) AS total_deaths
    FROM incidenti
    GROUP BY anno
    ORDER BY anno;
    """
    df_yearly = pd.read_sql_query(query, conn)
    conn.close()
    return df_yearly

@st.cache_data
def get_available_years():
    """Ottiene gli anni disponibili nel database"""
    conn = sqlite3.connect("dbAccidents.db")
    query = "SELECT DISTINCT anno FROM incidenti ORDER BY anno DESC;"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df['anno'].tolist()

def parse_year_selection(year_selection, available_years):
    """
    Converte la selezione dell'anno in lista di anni da usare nelle query
    Returns: (years_list, is_average_mode, display_text)
    """
    if year_selection == "Tutti gli anni":
        return available_years, True, "Media 2019-2023"
    else:
        return [year_selection], False, str(2000 + year_selection)

def apply_light_theme_to_fig(fig):
    """Applica tema con testo scuro per tutti i grafici"""
    return fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1f2937", size=12),
        title=dict(font=dict(color="#1f2937", size=16)),
        xaxis=dict(
            title_font=dict(color="#374151", size=20),
            tickfont=dict(color="#374151", size=14),
            gridcolor="#f3f4f6",
            linecolor="#d1d5db"
        ),
        yaxis=dict(
            title_font=dict(color="#374151", size=14),
            tickfont=dict(color="#374151", size=11),
            gridcolor="#f3f4f6",
            linecolor="#d1d5db"
        ),
        legend=dict(
            font=dict(color="#374151", size=12),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#d1d5db",
            borderwidth=1
        ),
        margin=dict(l=60, r=60, t=80, b=60)
    )

# Funzione helper per convertire hex in rgba
def hex_to_rgba(hex_color, alpha=0.4):
    rgb = mcolors.to_rgb(hex_color)  # restituisce tuple (r,g,b) in [0,1]
    r, g, b = [int(x*255) for x in rgb]
    return f'rgba({r},{g},{b},{alpha})'

# def hex_to_rgba(hex_color, alpha=1.0):
#     hex_color = hex_color.lstrip('#')
#     r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
#     return f'rgba({r},{g},{b},{alpha})'
# ===========
# GLOBAL VARIABLES
# ===========

available_years = get_available_years()