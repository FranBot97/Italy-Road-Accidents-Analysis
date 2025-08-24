import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json
import plotly.io as pio
import numpy as np

# =========================
# 🎨 CONFIGURAZIONE PAGINA & STYLING
# =========================
st.set_page_config(
    page_title="🚗 Incidenti Stradali Italia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# sfondo e griglie chiare di default
pio.templates.default = "plotly_white"

# CSS personalizzato per un design moderno (testo scuro)
st.markdown("""
    <style>
        /* App e sfondo chiari */
        html, body, .stApp, .main {
            background: #ffffff !important;
            color: #111 !important;
        }

        /* Sidebar chiara */
        [data-testid="stSidebar"] {
            background: #f7f7fb !important;
            border-right: 1px solid #e5e7eb;
        }

        /* Card metriche */
        .metric-card {
            background: #ffffff !important;
            padding: 1.2rem;
            border-radius: 14px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.06);
            border: 1px solid #eef2f7;
            margin: 0.6rem 0;
        }

        /* Titoli sezione (scuri) */
        .section-header {
            color: #1f2937;
            font-size: 2rem;
            font-weight: 700;
            text-align: center;
            margin: 2rem 0 0.6rem;
            text-shadow: none;
        }
        .section-subtitle {
            color: #6b7280;
            font-size: 1.05rem;
            text-align: center;
            margin-bottom: 1.4rem;
            font-style: italic;
        }

        /* Controlli */
        .stSelectbox > div > div,
        .stMultiSelect > div > div,
        .stRadio > div,
        .stNumberInput > div > div > input,
        .stSlider > div {
            background-color: #ffffff !important;
            border-radius: 10px !important;
        }

        /* Card per analisi temporale */
        .temporal-card {
            background: #ffffff;
            padding: 1.5rem;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            border: 1px solid #e5e7eb;
            margin: 1rem 0;
        }

        .insight-box {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 1rem;
            border-radius: 12px;
            border-left: 4px solid #3b82f6;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# 📊 HEADER PRINCIPALE
# =========================
st.markdown("""
<div style="text-align:center; padding: 1.8rem 0;">
  <h1 style="color:#1f2937; font-size:3rem; margin:0;">🚗 Dashboard Incidenti Stradali</h1>
  <h2 style="color:#6b7280; font-size:1.2rem; margin:0.5rem 0; font-weight:400;">
    Analisi Completa • Italia 2018–2023
  </h2>
  <div style="height:3px; width:220px; background:linear-gradient(90deg,#3b82f6,#22c55e,#06b6d4); margin:1rem auto; border-radius:2px;"></div>
</div>
""", unsafe_allow_html=True)

# =========================
# 🔧 FUNZIONI UTILITY
# =========================
@st.cache_data
def load_yearly_accident_data_from_db():
    conn = sqlite3.connect("dbAccidents.db")
    query = """
    SELECT
        anno,
        COUNT(*) AS total_incidents,
        SUM(Morti) AS total_deaths
    FROM incidenti
    GROUP BY anno
    ORDER BY anno;
    """
    df_yearly = pd.read_sql_query(query, conn)
    conn.close()
    return df_yearly

def apply_dark_theme_to_fig(fig):
    """Applica tema con testo scuro per tutti i grafici"""
    return fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1f2937", size=12),
        title=dict(font=dict(color="#1f2937", size=18)),
        xaxis=dict(
            title_font=dict(color="#374151", size=14),
            tickfont=dict(color="#374151", size=11),
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

# =========================
# 📈 SEZIONE 1: OVERVIEW ANNUALE
# =========================
st.markdown('<div class="section-header">📈 Panoramica Annuale</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Trend degli incidenti e delle vittime nel tempo</div>', unsafe_allow_html=True)

df_yearly_accidents = load_yearly_accident_data_from_db()
df_yearly_accidents['percentuali_morti'] = (df_yearly_accidents['total_deaths'] / df_yearly_accidents['total_incidents']) * 100
df_yearly_accidents = df_yearly_accidents.rename(columns={
    'anno': 'Anno',
    'total_incidents': 'Incidenti',
    'total_deaths': 'Morti',
    'percentuali_morti': 'Percentuale morti'
})

# Metriche chiave in cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_incidents = df_yearly_accidents['Incidenti'].sum()
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">🚨 Incidenti Totali</h3>
            <h2 style="color: #333; margin: 0.5rem 0;">{total_incidents:,}</h2>
            <p style="color: #666; margin: 0; font-size: 0.9rem;">2018-2023</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    total_deaths = df_yearly_accidents['Morti'].sum()
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #e74c3c; margin: 0;">💀 Vittime Totali</h3>
            <h2 style="color: #333; margin: 0.5rem 0;">{total_deaths:,}</h2>
            <p style="color: #666; margin: 0; font-size: 0.9rem;">2018-2023</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    avg_mortality = df_yearly_accidents['Percentuale morti'].mean()
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #f39c12; margin: 0;">📊 Tasso Mortalità</h3>
            <h2 style="color: #333; margin: 0.5rem 0;">{avg_mortality:.2f}%</h2>
            <p style="color: #666; margin: 0; font-size: 0.9rem;">Media annuale</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    trend_change = ((df_yearly_accidents.iloc[-1]['Incidenti'] - df_yearly_accidents.iloc[0]['Incidenti']) / df_yearly_accidents.iloc[0]['Incidenti']) * 100
    trend_color = "#27ae60" if trend_change < 0 else "#e74c3c"
    trend_icon = "📉" if trend_change < 0 else "📈"
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {trend_color}; margin: 0;">{trend_icon} Trend</h3>
            <h2 style="color: #333; margin: 0.5rem 0;">{trend_change:+.1f}%</h2>
            <p style="color: #666; margin: 0; font-size: 0.9rem;">2018 vs 2023</p>
        </div>
    """, unsafe_allow_html=True)

# Grafico principale
fig_yearly = go.Figure()
fig_yearly.add_trace(go.Bar(
    x=df_yearly_accidents["Anno"],
    y=df_yearly_accidents["Incidenti"],
    name="Incidenti",
    marker_color='rgba(102, 126, 234, 0.8)',
    text=df_yearly_accidents["Morti"],
    textposition='outside',
    texttemplate='%{text} morti',
    textfont=dict(color="#1f2937", size=12),
    hovertemplate="<b>Anno %{x}</b><br>" +
                  "Incidenti: %{y:,}<br>" +
                  "Morti: %{text}<br>" +
                  "<extra></extra>"
))
fig_yearly.update_layout(
    title=dict(
        text="🚗 Andamento Incidenti Stradali per Anno",
        font=dict(size=20, color='#1f2937'),
        x=0.5
    ),
    xaxis_title="Anno",
    yaxis_title="Numero di Incidenti",
    height=500
)
fig_yearly = apply_dark_theme_to_fig(fig_yearly)
st.plotly_chart(fig_yearly, use_container_width=True)

# =========================
# 🗺️ SEZIONE 2: ANALISI GEOGRAFICA
# =========================
st.markdown('<div class="section-header">🗺️ Distribuzione Geografica</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Mappa interattiva degli incidenti per regione e provincia</div>', unsafe_allow_html=True)

# Controlli geografici
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 1])
with col_ctrl1:
    anno_sel = st.slider(
        "📅 Seleziona Anno",
        min_value=2018,
        max_value=2023,
        value=2022,
        step=1,
        help="Anno per l'analisi geografica e temporale"
    )
with col_ctrl2:
    view_mode = st.radio("🗺️ Modalità Visualizzazione", ["Province", "Regioni"], horizontal=True)
with col_ctrl3:
    if view_mode == "Regioni":
        normalizza = st.toggle("📊 Normalizza per popolazione", value=False)

conn = sqlite3.connect("dbAccidents.db")

if view_mode == "Province":
    # Query province
    query_province = f"""
    SELECT pr.idProvincia, pr.provincia, COUNT(*) AS incidenti
    FROM incidenti i
    JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
    WHERE i.anno = {anno_sel % 100}
    GROUP BY pr.idProvincia, pr.provincia
    """
    df_geo = pd.read_sql_query(query_province, conn)
    df_geo["idProvincia"] = df_geo["idProvincia"].astype(int)

    # GeoJSON province
    with open("Geo/limits_IT_provinces.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    fig_geo = px.choropleth(
        df_geo,
        geojson=geojson_data,
        locations="idProvincia",
        featureidkey="properties.prov_istat_code_num",
        color="incidenti",
        hover_name="provincia",
        color_continuous_scale="Plasma",
        title=f"🏙️ Incidenti per Provincia - {anno_sel}"
    )
else:
    # Query regioni
    query_regioni = f"""
    SELECT pr.idRegione, pr.regione AS nome_regione, COUNT(*) AS incidenti
    FROM incidenti i
    JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
    WHERE i.anno = {anno_sel % 100}
    GROUP BY pr.idRegione, pr.regione
    """
    df_regioni = pd.read_sql_query(query_regioni, conn)
    df_regioni["idRegione"] = df_regioni["idRegione"].astype(str).str.zfill(2)

    # Popolazione
    query_pop = "SELECT id AS idRegione, popolazione FROM regioni"
    df_pop = pd.read_sql_query(query_pop, conn)
    df_pop["idRegione"] = df_pop["idRegione"].astype(str).str.zfill(2)

    # Merge e calcolo normalizzati
    df_geo = df_regioni.merge(df_pop, on="idRegione", how="left")
    df_geo["incidenti_per_100k"] = df_geo["incidenti"] / df_geo["popolazione"] * 100_000

    # GeoJSON regioni
    with open("Geo/limits_IT_regions.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    # Forza conversione a float e gestisci NaN
    df_geo["incidenti"] = pd.to_numeric(df_geo["incidenti"], errors='coerce').fillna(0)
    df_geo["incidenti_per_100k"] = pd.to_numeric(df_geo["incidenti_per_100k"], errors='coerce').fillna(0)

    # Parametri in base alla modalità
    if normalizza:
        color_column = "incidenti_per_100k"
        min_val = df_geo["incidenti_per_100k"].min()
        max_val = df_geo["incidenti_per_100k"].max()
        title_suffix = "Normalizzati"
        color_scale = "Reds"
    else:
        color_column = "incidenti"
        min_val = df_geo["incidenti"].min()
        max_val = df_geo["incidenti"].max()
        title_suffix = "Assoluti"
        color_scale = "Blues"

    fig_geo = px.choropleth(
        df_geo,
        geojson=geojson_data,
        locations="idRegione",
        featureidkey="properties.reg_istat_code",
        color=color_column,
        hover_name="nome_regione",
        hover_data={
            "incidenti": ":,",
            "incidenti_per_100k": ":.1f",
            "popolazione": ":,",
            "idRegione": False
        },
        color_continuous_scale=color_scale,
        range_color=[min_val, max_val],
        labels={
            "incidenti": "Incidenti",
            "incidenti_per_100k": "Incidenti per 100k ab.",
            "popolazione": "Popolazione"
        },
        title=f"🌍 Incidenti per Regione - {anno_sel} ({title_suffix})"
    )

fig_geo.update_geos(fitbounds="locations", visible=False)
fig_geo = apply_dark_theme_to_fig(fig_geo)
fig_geo.update_layout(height=600)
st.plotly_chart(fig_geo, use_container_width=True)

# =========================
# ⏰ SEZIONE 3: ANALISI TEMPORALE MIGLIORATA
# =========================
st.markdown('<div class="section-header">⏰ Analisi Temporale Avanzata</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Pattern temporali degli incidenti: quando accadono più spesso?</div>', unsafe_allow_html=True)

# Anni disponibili
available_years_df = pd.read_sql_query("SELECT DISTINCT anno FROM incidenti ORDER BY anno DESC;", conn)
available_years = available_years_df['anno'].tolist()

# Controlli centralizzati
st.markdown("### 🎛️ Controlli Analisi Temporale")
col_ctrl_temp1, col_ctrl_temp2, col_ctrl_temp3 = st.columns(3)

with col_ctrl_temp1:
    default_years = available_years[-3:] if len(available_years) >= 3 else available_years
    selected_years = st.multiselect(
        "📅 Seleziona Anni",
        options=available_years,
        default=default_years,
        help="Scegli gli anni da analizzare"
    )

with col_ctrl_temp2:
    analysis_type = st.selectbox(
        "📊 Tipo Analisi",
        ["Entrambe", "Solo Giornaliera", "Solo Oraria"],
        help="Seleziona quale analisi visualizzare"
    )

with col_ctrl_temp3:
    show_insights = st.toggle("💡 Mostra Insights", value=True, help="Attiva/disattiva i suggerimenti automatici")

if selected_years:
    years_str = ','.join(map(str, selected_years))
    
    # === ANALISI GIORNALIERA MIGLIORATA ===
    if analysis_type in ["Entrambe", "Solo Giornaliera"]:
        st.markdown('<div class="temporal-card">', unsafe_allow_html=True)
        st.markdown("#### 📅 Distribuzione Settimanale degli Incidenti")
        
        query_day = f"""
        SELECT g.giorno, g.id as day_id, COUNT(*) AS numero_incidenti,
               SUM(i.Morti) as morti_totali
        FROM incidenti i
        JOIN giorno g ON i.idGiorno = g.id
        WHERE i.anno IN ({years_str})
        GROUP BY g.giorno, g.id
        ORDER BY g.id;
        """
        df_day = pd.read_sql_query(query_day, conn)

        if len(selected_years) > 1:
            df_day['numero_incidenti'] = df_day['numero_incidenti'] / len(selected_years)
            df_day['morti_totali'] = df_day['morti_totali'] / len(selected_years)

        # Calcolo percentuali
        total_incidents_week = df_day['numero_incidenti'].sum()
        df_day['percentuale'] = (df_day['numero_incidenti'] / total_incidents_week) * 100

        # Identifica giorni critici
        mean_incidents = df_day['numero_incidenti'].mean()
        df_day['is_critical'] = df_day['numero_incidenti'] > mean_incidents * 1.1

        # Grafico combinato con barre e linea
        fig_day_combo = go.Figure()

        # Barre colorate in base alla criticità
        colors = ['#ef4444' if critical else '#3b82f6' for critical in df_day['is_critical']]
        
        fig_day_combo.add_trace(go.Bar(
            x=df_day['giorno'],
            y=df_day['numero_incidenti'],
            name='Incidenti',
            marker_color=colors,
            text=[f"{val:.0f}<br>({perc:.1f}%)" for val, perc in zip(df_day['numero_incidenti'], df_day['percentuale'])],
            textposition='outside',
            textfont=dict(color="#1f2937", size=11),
            hovertemplate="<b>%{x}</b><br>" +
                         "Incidenti: %{y:.0f}<br>" +
                         "Percentuale: %{customdata:.1f}%<br>" +
                         "<extra></extra>",
            customdata=df_day['percentuale']
        ))

        # Linea delle morti (asse secondario)
        fig_day_combo.add_trace(go.Scatter(
            x=df_day['giorno'],
            y=df_day['morti_totali'],
            mode='lines+markers',
            name='Morti',
            line=dict(color='#dc2626', width=3),
            marker=dict(size=8, color='#dc2626'),
            yaxis='y2',
            hovertemplate="<b>%{x}</b><br>" +
                         "Morti: %{y:.0f}<br>" +
                         "<extra></extra>"
        ))

        fig_day_combo.update_layout(
            title="📊 Incidenti e Vittime per Giorno della Settimana",
            xaxis_title="Giorno della Settimana",
            yaxis_title="Numero Incidenti",
            yaxis2=dict(
                title="Numero Morti",
                overlaying='y',
                side='right',
                showgrid=False
            ),
            height=500,
            hovermode='x unified'
        )
        
        fig_day_combo = apply_dark_theme_to_fig(fig_day_combo)
        st.plotly_chart(fig_day_combo, use_container_width=True)

        # Insights automatici per giorni
        if show_insights:
            max_day = df_day.loc[df_day['numero_incidenti'].idxmax(), 'giorno']
            min_day = df_day.loc[df_day['numero_incidenti'].idxmin(), 'giorno']
            max_deaths_day = df_day.loc[df_day['morti_totali'].idxmax(), 'giorno']
            
            st.markdown(f"""
            <div class="insight-box">
                <h4 style="color: #1f2937; margin-top: 0;">💡 Insights Settimanali</h4>
                <ul style="color: #374151; margin-bottom: 0;">
                    <li><strong>{max_day}</strong> è il giorno con più incidenti ({df_day[df_day['giorno'] == max_day]['numero_incidenti'].iloc[0]:.0f} in media)</li>
                    <li><strong>{min_day}</strong> è il giorno più sicuro ({df_day[df_day['giorno'] == min_day]['numero_incidenti'].iloc[0]:.0f} incidenti in media)</li>
                    <li><strong>{max_deaths_day}</strong> registra il maggior numero di vittime</li>
                    <li>Giorni critici (rosso): incidenti superiori alla media del 10%</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # === ANALISI ORARIA MIGLIORATA ===
    if analysis_type in ["Entrambe", "Solo Oraria"]:
        st.markdown('<div class="temporal-card">', unsafe_allow_html=True)
        st.markdown("#### 🕐 Distribuzione Oraria degli Incidenti")
        
        query_hour = f"""
        SELECT i.Ora, COUNT(*) AS numero_incidenti,
               SUM(i.Morti) as morti_totali
        FROM incidenti i
        WHERE i.anno IN ({years_str})
        GROUP BY i.Ora
        ORDER BY i.Ora;
        """
        df_hour = pd.read_sql_query(query_hour, conn)

        # Tutte le 24 ore
        all_hours_df = pd.DataFrame({'Ora': range(24)})
        df_hour = pd.merge(all_hours_df, df_hour, on='Ora', how='left').fillna(0)

        if len(selected_years) > 1:
            df_hour['numero_incidenti'] = df_hour['numero_incidenti'] / len(selected_years)
            df_hour['morti_totali'] = df_hour['morti_totali'] / len(selected_years)

        # Categorizzazione per fasce orarie
        def categorize_hour(hour):
            if 6 <= hour < 12:
                return "🌅 Mattina"
            elif 12 <= hour < 18:
                return "☀️ Pomeriggio"
            elif 18 <= hour < 24:
                return "🌆 Sera"
            else:
                return "🌙 Notte"

        df_hour['fascia'] = df_hour['Ora'].apply(categorize_hour)
        
        # Media mobile per smoothing
        df_hour['media_mobile'] = df_hour['numero_incidenti'].rolling(window=3, center=True, min_periods=1).mean()

        # Grafico a area con gradiente + linea smoothed
        fig_hour_area = go.Figure()

        # Area sotto la curva
        fig_hour_area.add_trace(go.Scatter(
            x=df_hour['Ora'],
            y=df_hour['numero_incidenti'],
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.3)',
            line=dict(color='rgba(59, 130, 246, 0.8)', width=2),
            mode='lines',
            name='Incidenti',
            hovertemplate="<b>Ore %{x}:00</b><br>" +
                         "Incidenti: %{y:.0f}<br>" +
                         "Fascia: %{customdata}<br>" +
                         "<extra></extra>",
            customdata=df_hour['fascia']
        ))

        # Linea smoothed
        fig_hour_area.add_trace(go.Scatter(
            x=df_hour['Ora'],
            y=df_hour['media_mobile'],
            line=dict(color='#dc2626', width=3, dash='solid'),
            mode='lines',
            name='Trend (Media Mobile)',
            hovertemplate="<b>Ore %{x}:00</b><br>" +
                         "Trend: %{y:.1f}<br>" +
                         "<extra></extra>"
        ))

        # Evidenziazione picchi
        threshold = df_hour['numero_incidenti'].quantile(0.75)
        peak_hours = df_hour[df_hour['numero_incidenti'] >= threshold]
        
        fig_hour_area.add_trace(go.Scatter(
            x=peak_hours['Ora'],
            y=peak_hours['numero_incidenti'],
            mode='markers',
            marker=dict(color='#ef4444', size=12, symbol='circle'),
            name='Ore di Picco',
            hovertemplate="<b>Ora Critica: %{x}:00</b><br>" +
                         "Incidenti: %{y:.0f}<br>" +
                         "<extra></extra>"
        ))

        fig_hour_area.update_layout(
            title="🕐 Distribuzione Oraria degli Incidenti con Trend",
            xaxis_title="Ora del Giorno",
            yaxis_title="Numero Incidenti (Media)",
            xaxis=dict(tickmode="linear", dtick=2),
            height=500,
            hovermode='x unified'
        )
        
        fig_hour_area = apply_dark_theme_to_fig(fig_hour_area)
        st.plotly_chart(fig_hour_area, use_container_width=True)

        # Heatmap oraria per giorni della settimana (se possibile)
        query_hour_day = f"""
        SELECT g.giorno, i.Ora, COUNT(*) AS incidenti
        FROM incidenti i
        JOIN giorno g ON i.idGiorno = g.id
        WHERE i.anno IN ({years_str})
        GROUP BY g.giorno, i.Ora
        ORDER BY g.id, i.Ora;
        """
        df_hour_day = pd.read_sql_query(query_hour_day, conn)
        
        if not df_hour_day.empty:
            st.markdown("#### 🔥 Heatmap Ore × Giorni")
            
            # Pivot per heatmap
            heatmap_data = df_hour_day.pivot_table(
                index='giorno', 
                columns='Ora', 
                values='incidenti', 
                fill_value=0
            )
            
            # Ordine giorni
            day_order = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            heatmap_data = heatmap_data.reindex(day_order, fill_value=0)
            
            fig_heatmap_time = px.imshow(
                heatmap_data,
                text_auto=True,
                color_continuous_scale="RdYlBu_r",
                aspect="auto",
                title="🔥 Intensità Incidenti per Ora e Giorno"
            )
            
            fig_heatmap_time.update_traces(
                texttemplate="%{z}",
                textfont=dict(size=9, color="#1f2937")
            )
            
            fig_heatmap_time = apply_dark_theme_to_fig(fig_heatmap_time)
            fig_heatmap_time.update_layout(
                height=400,
                xaxis_title="Ora del Giorno",
                yaxis_title="Giorno della Settimana"
            )
            st.plotly_chart(fig_heatmap_time, use_container_width=True)

        # Insights automatici per ore
        if show_insights:
            peak_hour = df_hour.loc[df_hour['numero_incidenti'].idxmax(), 'Ora']
            safest_hour = df_hour.loc[df_hour['numero_incidenti'].idxmin(), 'Ora']
            
            # Statistiche per fasce orarie
            fascia_stats = df_hour.groupby('fascia')['numero_incidenti'].sum().sort_values(ascending=False)
            most_dangerous_period = fascia_stats.index[0]
            safest_period = fascia_stats.index[-1]
            
            st.markdown(f"""
            <div class="insight-box">
                <h4 style="color: #1f2937; margin-top: 0;">💡 Insights Orari</h4>
                <ul style="color: #374151; margin-bottom: 0;">
                    <li><strong>Ore {peak_hour:02d}:00</strong> è l'ora più pericolosa ({df_hour[df_hour['Ora'] == peak_hour]['numero_incidenti'].iloc[0]:.0f} incidenti in media)</li>
                    <li><strong>Ore {safest_hour:02d}:00</strong> è l'ora più sicura ({df_hour[df_hour['Ora'] == safest_hour]['numero_incidenti'].iloc[0]:.0f} incidenti in media)</li>
                    <li><strong>{most_dangerous_period}</strong> è la fascia oraria più critica</li>
                    <li><strong>{safest_period}</strong> è la fascia oraria più sicura</li>
                    <li>Le ore di picco (rosse) superano il 75° percentile</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # === ANALISI COMPARATIVA FASCE ORARIE ===
    if analysis_type == "Entrambe" and selected_years:
        st.markdown("### 📊 Confronto per Fasce Orarie")
        
        # Raggruppa per fasce orarie
        fascia_data = df_hour.groupby('fascia').agg({
            'numero_incidenti': 'sum',
            'morti_totali': 'sum'
        }).reset_index()
        
        col_fascia1, col_fascia2 = st.columns(2)
        
        with col_fascia1:
            # Grafico a torta per incidenti
            fig_pie_incidents = px.pie(
                fascia_data,
                values='numero_incidenti',
                names='fascia',
                title="🥧 Distribuzione Incidenti per Fascia",
                color_discrete_sequence=['#3b82f6', '#ef4444', '#f59e0b', '#10b981']
            )
            fig_pie_incidents = apply_dark_theme_to_fig(fig_pie_incidents)
            fig_pie_incidents.update_traces(textfont=dict(color="#1f2937", size=12))
            st.plotly_chart(fig_pie_incidents, use_container_width=True)
        
        with col_fascia2:
            # Grafico a barre per confronto morti/incidenti
            fascia_data['tasso_mortalita'] = (fascia_data['morti_totali'] / fascia_data['numero_incidenti']) * 100
            
            fig_bar_mortality = px.bar(
                fascia_data,
                x='fascia',
                y='tasso_mortalita',
                title="💀 Tasso di Mortalità per Fascia",
                color='tasso_mortalita',
                color_continuous_scale='Reds'
            )
            fig_bar_mortality = apply_dark_theme_to_fig(fig_bar_mortality)
            fig_bar_mortality.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
            st.plotly_chart(fig_bar_mortality, use_container_width=True)

else:
    st.warning("⚠️ Seleziona almeno un anno per visualizzare l'analisi temporale.")

# =========================
# 🔥 SEZIONE 4: HEATMAP VEICOLI
# =========================
st.markdown('<div class="section-header">🔥 Matrice Interazioni Veicoli</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Analisi delle coppie di veicoli coinvolti negli incidenti</div>', unsafe_allow_html=True)

# Controlli heatmap
col_hm1, col_hm2, col_hm3 = st.columns([1, 1, 2])
with col_hm1:
    metric_mode = st.selectbox(
        "🎯 Metrica",
        ["Conteggi assoluti", "Densità relativa"],
        help="Conteggi assoluti vs percentuali normalizzate"
    )
with col_hm2:
    min_threshold = st.number_input(
        "🎚️ Soglia minima",
        min_value=1,
        max_value=1000,
        value=50,
        help="Numero minimo di incidenti per includere la coppia"
    )

# Query heatmap
query_heatmap = f"""
SELECT va.gruppo AS tipoA, vb.gruppo AS tipoB, COUNT(*) AS n
FROM incidenti i
JOIN tipo_veicolo va ON i.idTipoVeicoloA = va.id
JOIN tipo_veicolo vb ON i.idTipoVeicoloB = vb.id
WHERE i.anno = {anno_sel % 100}
  AND i.idTipoVeicoloA IS NOT NULL
  AND i.idTipoVeicoloB IS NOT NULL
GROUP BY va.gruppo, vb.gruppo
HAVING COUNT(*) >= {min_threshold};
"""
df_pairs = pd.read_sql_query(query_heatmap, conn)
conn.close()

if df_pairs.empty:
    st.warning("⚠️ Nessun dato disponibile con i criteri selezionati.")
else:
    # Crea matrice
    matrix = df_pairs.pivot_table(index="tipoA", columns="tipoB", values="n", fill_value=0)

    # Ordina per frequenza
    row_order = matrix.sum(axis=1).sort_values(ascending=False).index
    col_order = matrix.sum(axis=0).sort_values(ascending=False).index
    matrix = matrix.loc[row_order, col_order]

    # Configura metrica
    if metric_mode == "Densità relativa":
        matrix_display = matrix.div(matrix.sum(axis=1).replace(0, 1), axis=0) * 100
        z = matrix_display.round(1)
        colorbar_title = "Densità (%)"
        color_scale = "Turbo"
        value_format = ".1f"
    else:
        z = matrix
        colorbar_title = "N° Incidenti"
        color_scale = "Reds"
        value_format = "d"

    # Heatmap (testi scuri per leggere su sfondo chiaro)
    fig_hm = px.imshow(
        z,
        text_auto=True,
        color_continuous_scale=color_scale,
        aspect="auto",
        title=f"🔥 Matrice Incidenti {anno_sel} • {metric_mode}"
    )
    fig_hm.update_traces(
        texttemplate=f"%{{z:{value_format}}}",
        textfont_size=9,
        textfont_color="#1f2937"
    )
    fig_hm = apply_dark_theme_to_fig(fig_hm)
    fig_hm.update_layout(
        xaxis_title="Tipo Veicolo B",
        yaxis_title="Tipo Veicolo A",
        xaxis_tickangle=-45,
        height=600,
        coloraxis_colorbar=dict(title=colorbar_title)
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    # Statistiche finali
    with st.expander("📊 Statistiche Dettagliate"):
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("🔗 Coppie Uniche", f"{len(df_pairs):,}")
        with col_stat2:
            st.metric("📈 Incidenti Totali", f"{matrix.sum().sum():,}")
        with col_stat3:
            max_val = matrix.max().max()
            st.metric("🥇 Massimo", f"{max_val:,}")
        with col_stat4:
            avg_val = matrix.values[matrix.values > 0].mean()
            st.metric("📊 Media", f"{avg_val:.1f}")

# =========================
# 🎯 FOOTER
# =========================
st.markdown("""
    <div style="text-align: center; padding: 3rem 0 1rem 0;">
        <div style="height: 2px; width: 100%; background: linear-gradient(90deg, #667eea, #764ba2); margin: 2rem 0;"></div>
        <p style="color: #666; font-size: 0.9rem;">
            📊 Dashboard Incidenti Stradali Italia • Dati 2018-2023 •
            <span style="color: #0ea5e9;">Analisi Interattiva</span>
        </p>
    </div>
""", unsafe_allow_html=True)