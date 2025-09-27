import streamlit as st
import pandas as pd
from Utils import utils
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json
import matplotlib.colors as mcolors
import numpy as np

def show():
    # Ottieni anni disponibili
    available_years = utils.get_available_years()

    st.markdown('<div class="section-header">Giorni e orari</div>', unsafe_allow_html=True)
    # st.set_page_config(
    #     page_title="Incidenti Stradali Italia",
    #     layout="wide",
    #     initial_sidebar_state="expanded"
    # )

    col_ctrl_temp1, col_ctrl_temp2, col_ctrl_temp3 = st.columns(3)

    with col_ctrl_temp1:
        # Usa lo stesso sistema del grafico geografico
        year_options_temp = ["Tutti gli anni"] + [2000 + year for year in sorted(available_years, reverse=True)]
        
        year_selection_temp = st.selectbox(
            "Seleziona Periodo",
            options=year_options_temp,
            index=0,  # Default a "Tutti gli anni"
            help="Scegli un anno specifico o tutti gli anni per la media",
            key="temp_year_selector"
        )

    # Parse della selezione anno per analisi temporale
    if year_selection_temp == "Tutti gli anni":
        selected_years_temp, is_average_temp, display_text_temp = available_years, True, "Media 2019-2023"
    else:
        year_value = year_selection_temp - 2000
        selected_years_temp, is_average_temp, display_text_temp = [year_value], False, str(year_selection_temp)

    if selected_years_temp:
        years_str = ','.join(map(str, selected_years_temp))
        
        # === ANALISI GIORNALIERA MIGLIORATA ===
        
        query_day = f"""
        SELECT g.giorno, g.id as day_id, COUNT(*) AS numero_incidenti,
                SUM(i.Morti) as morti_totali
        FROM incidenti i
        JOIN giorno g ON i.idGiorno = g.id
        WHERE i.anno IN ({years_str})
        GROUP BY g.giorno, g.id
        ORDER BY g.id;
        """
        df_day = utils.run_query(query_day)

        # Se è modalità media, dividi per il numero di anni
        if is_average_temp:
            df_day['numero_incidenti'] = df_day['numero_incidenti'] / len(selected_years_temp)
            df_day['morti_totali'] = df_day['morti_totali'] / len(selected_years_temp)

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
                            f"Incidenti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
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
                            f"Morti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
                            "<extra></extra>"
        ))

        fig_day_combo.update_layout(
            title=f"📊 Incidenti e Vittime per Giorno della Settimana - {display_text_temp}",
            xaxis_title="Giorno della Settimana",
            yaxis_title=f"Numero Incidenti{' (Media)' if is_average_temp else ''}",
            yaxis2=dict(
                title=f"Numero Morti{' (Media)' if is_average_temp else ''}",
                overlaying='y',
                side='right',
                showgrid=False
            ),
            height=500,
            hovermode='x unified'
        )
        
        fig_day_combo = utils.apply_light_theme_to_fig(fig_day_combo)
        st.plotly_chart(fig_day_combo, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # === ANALISI ORARIA MIGLIORATA ===
    
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
        df_hour = utils.run_query(query_hour)

        # Tutte le 24 ore
        all_hours_df = pd.DataFrame({'Ora': range(24)})
        df_hour = pd.merge(all_hours_df, df_hour, on='Ora', how='left').fillna(0)

        # Se è modalità media, dividi per il numero di anni
        if is_average_temp:
            df_hour['numero_incidenti'] = df_hour['numero_incidenti'] / len(selected_years_temp)
            df_hour['morti_totali'] = df_hour['morti_totali'] / len(selected_years_temp)

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
                            f"Incidenti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
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
                            f"Trend: %{{y:.{'1f' if is_average_temp else '1f'}}}<br>" +
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
                            f"Incidenti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
                            "<extra></extra>"
        ))

        fig_hour_area.update_layout(
            title=f"🕐 Distribuzione Oraria degli Incidenti con Trend - {display_text_temp}",
            xaxis_title="Ora del Giorno",
            yaxis_title=f"Numero Incidenti{' (Media)' if is_average_temp else ''}",
            xaxis=dict(tickmode="linear", dtick=2),
            height=500,
            hovermode='x unified'
        )
        
        fig_hour_area = utils.apply_light_theme_to_fig(fig_hour_area)
        st.plotly_chart(fig_hour_area, use_container_width=True)

        

    # === ANALISI COMPARATIVA FASCE ORARIE ===

    st.markdown("### 📊 Confronto per Fasce Orarie")

    # --- 1) PREPARAZIONE DATI ---
    # Raggruppa per fasce
    fascia_data = (
        df_hour.groupby('fascia')
        .agg(numero_incidenti=('numero_incidenti', 'sum'),
                morti_totali=('morti_totali', 'sum'))
        .reset_index()
    )

    # Se vuoto, esci con messaggio
    if fascia_data.empty:
        st.info("Nessun dato disponibile per le fasce orarie selezionate.")
        st.stop()

    # Calcola tasso di mortalità in %
    fascia_data['tasso_mortalita'] = (
        fascia_data['morti_totali'] / fascia_data['numero_incidenti'].replace(0, 1) * 100
    )

    # Ordina secondo sequenza logica
    fascia_order = ['🌅 Mattina', '☀️ Pomeriggio', '🌆 Sera', '🌙 Notte']
    fascia_data_ordered = (
        fascia_data.set_index('fascia')
        .reindex(fascia_order)
        .fillna(0)
        .reset_index()
    )

    labels = fascia_data_ordered['fascia'].tolist()
    incidents = fascia_data_ordered['numero_incidenti'].to_numpy(dtype=float)
    mortality = fascia_data_ordered['tasso_mortalita'].to_numpy(dtype=float)

    total_incidents = incidents.sum()
    if total_incidents <= 0:
        st.info("Non ci sono incidenti nelle fasce selezionate.")
        st.stop()

    # --- 2) ANGOLI REALI DELLE FETTE (in gradi) ---
    percentages = incidents / max(total_incidents, 1e-9)
    angles_extent = percentages * 360.0

    # (Facoltativo) estensione minima per fette minuscole: lascia 0 per non alterare le proporzioni
    MIN_DEG = 0
    if MIN_DEG > 0:
        extra = np.maximum(angles_extent, MIN_DEG)
        angles_extent = extra * (360.0 / extra.sum())

    start_angles = np.concatenate(([0.0], np.cumsum(angles_extent)[:-1]))
    end_angles   = np.cumsum(angles_extent)
    mid_angles   = (start_angles + end_angles) / 2.0  # centri angolari per le punte


    legend_added = False


