import streamlit as st
import pandas as pd
from Utils import utils
import sqlite3
import plotly.graph_objects as go

# =========================
# 🚀 FUNZIONI OTTIMIZZATE CON CACHE
# =========================

@st.cache_data(ttl=3600)
def load_all_temporal_data(years_str):
    """Carica tutti i dati temporali in una volta sola - CACHED"""
    conn = sqlite3.connect("dbAccidents.db")
    
    # Query giornaliera
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
    
    # Query oraria CON giorno (tutti i dati insieme)
    query_hour_all = f"""
    SELECT g.id as day_id, i.Ora, COUNT(*) AS numero_incidenti,
            SUM(i.Morti) as morti_totali
    FROM incidenti i
    JOIN giorno g ON i.idGiorno = g.id
    WHERE i.anno IN ({years_str})
    GROUP BY g.id, i.Ora
    ORDER BY g.id, i.Ora;
    """
    df_hour_all = pd.read_sql_query(query_hour_all, conn)
    
    conn.close()
    return df_day, df_hour_all

def process_day_data(df_day, num_years):
    """Processa i dati giornalieri"""
    df_day = df_day.copy()
    df_day['numero_incidenti'] = df_day['numero_incidenti'] / num_years
    df_day['morti_totali'] = df_day['morti_totali'] / num_years
    
    total_incidents_week = df_day['numero_incidenti'].sum()
    df_day['percentuale'] = (df_day['numero_incidenti'] / total_incidents_week) * 100
    
    mean_incidents = df_day['numero_incidenti'].mean()
    df_day['is_critical'] = df_day['numero_incidenti'] > mean_incidents * 1.1
    
    return df_day

def process_hour_data(df_hour_all, selected_day_id, num_years, is_average):
    """Processa i dati orari - filtrati in memoria"""
    if selected_day_id:
        df_hour = df_hour_all[df_hour_all['day_id'] == selected_day_id].copy()
        df_hour = df_hour.groupby('Ora').agg({
            'numero_incidenti': 'sum',
            'morti_totali': 'sum'
        }).reset_index()
    else:
        df_hour = df_hour_all.groupby('Ora').agg({
            'numero_incidenti': 'sum',
            'morti_totali': 'sum'
        }).reset_index()
    
    # Riempi ore mancanti
    df_hour = df_hour.set_index('Ora').reindex(range(24), fill_value=0).reset_index()
    
    if is_average:
        df_hour['numero_incidenti'] = df_hour['numero_incidenti'] / num_years
        df_hour['morti_totali'] = df_hour['morti_totali'] / num_years
    
    return df_hour

def get_bar_colors(df_day, selected_day):
    """Calcola i colori delle barre"""
    if selected_day:
        return [
            '#10b981' if giorno == selected_day else '#3b82f6'
            for giorno, critical in zip(df_day['giorno'], df_day['is_critical'])
        ]
    return ['#3b82f6' for critical in df_day['is_critical']]

# =========================
# 🎨 FRAGMENT PER GRAFICI INTERATTIVI
# =========================

@st.fragment
def render_charts(df_day, df_hour_all, num_years, is_average_temp, display_text_temp):
    """Fragment che gestisce solo i grafici - si aggiorna velocemente"""
    
    # === PROCESSA DATI ORARI ===
    selected_day_id = None
    if st.session_state.selected_day:
        selected_day_id = df_day[df_day['giorno'] == st.session_state.selected_day]['day_id'].iloc[0]
    
    df_hour = process_hour_data(df_hour_all, selected_day_id, num_years, is_average_temp)
    
    # === GRAFICO GIORNALIERO ===
    fig_day_combo = go.Figure()
    
    colors = get_bar_colors(df_day, st.session_state.selected_day)
    
    fig_day_combo.add_trace(go.Bar(
        x=df_day['giorno'],
        y=df_day['numero_incidenti'],
        name='Incidenti',
        marker=dict(
            color=colors,
            line=dict(color='#1f2937', width=0),
            opacity=0.95
        ),
        text=[f"{val:.0f}<br>({perc:.1f}%)" for val, perc in zip(df_day['numero_incidenti'], df_day['percentuale'])],
        textposition='outside',
        textfont=dict(color="#1f2937", size=13),
        hovertemplate=f"Incidenti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
                     "Percentuale: %{customdata:.1f}%<br>" +
                     "<extra></extra>",
        customdata=df_day['percentuale'],
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#3b82f6",
            font=dict(color="#1f2937", size=15)
        )
    ))

    fig_day_combo.add_trace(go.Scatter(
        x=df_day['giorno'],
        y=df_day['morti_totali'],
        mode='lines+markers',
        name='Morti',
        line=dict(color='#dc2626', width=3),
        marker=dict(size=8, color='#dc2626'),
        yaxis='y2',
        hovertemplate=f"Morti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
                     "<extra></extra>"
    ))
    
    fig_day_combo.update_layout(
        title=f"Incidenti e vittime per giorno della settimana - {display_text_temp}",
        font=dict(size=14),
        xaxis_title="Giorno della Settimana",
        yaxis_title=f"Numero Incidenti{' (Media)' if is_average_temp else ''}",
        xaxis=dict(fixedrange=True, tickfont=dict(size=13)),
        yaxis=dict(
            range=[0, df_day['numero_incidenti'].max() * 1.15],
            fixedrange=True,
            tickfont=dict(size=13)
        ),
        yaxis2=dict(
             title=dict(
                text=f"Numero Morti{' (Media)' if is_average_temp else ''}",
                font=dict(color='#dc2626')
            ),
            overlaying='y',
            side='right',
            showgrid=False,
            fixedrange=True,
        ),
        height=650,
        hovermode='x unified',
        hoverdistance=100,
        margin=dict(t=120, b=60, l=60, r=60),
        dragmode=False
    )
    
    # === GRAFICO ORARIO ===
    title_suffix = f" - {st.session_state.selected_day}" if st.session_state.selected_day else " - media settimanale"
    fill_color = 'rgba(16, 185, 129, 0.3)' if st.session_state.selected_day else 'rgba(59, 130, 246, 0.3)'
    line_color = 'rgba(16, 185, 129, 0.8)' if st.session_state.selected_day else 'rgba(59, 130, 246, 0.8)'
    
    fig_hour_area = go.Figure()

    fig_hour_area.add_trace(go.Scatter(
        x=df_hour['Ora'],
        y=df_hour['numero_incidenti'],
        fill='tozeroy',
        fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        mode='lines',
        name='Incidenti',
        hovertemplate="<b>Ore %{x}:00</b><br>" +
                     f"Incidenti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
                     "<extra></extra>"
    ))

    fig_hour_area.add_trace(go.Scatter(
        x=df_hour['Ora'],
        y=df_hour['morti_totali'],
        mode='lines+markers',
        name='Morti',
        line=dict(color='#dc2626', width=3),
        marker=dict(size=8, color='#dc2626'),
        yaxis='y2',
        hovertemplate=f"Morti: %{{y:.{'1f' if is_average_temp else '0f'}}}<br>" +
                     "<extra></extra>"
    ))

    fig_hour_area.update_layout(
        title=f"Dettagli orari {title_suffix}",
        font=dict(size=14),
        xaxis_title="Ora del giorno",
        yaxis_title=f"Numero incidenti{' (Media)' if is_average_temp else ''}",
        yaxis2=dict(
            title=dict(
                text=f"Numero Morti{' (Media)' if is_average_temp else ''}",
                font=dict(color='#dc2626')
            ),
            overlaying='y',
            side='right',
            showgrid=False,
            tickfont=dict(color='#dc2626')
        ),
        xaxis=dict(
            tickmode="linear",
            dtick=2,
            tickfont=dict(size=13),
            fixedrange=True
        ),
        yaxis=dict(
            tickfont=dict(size=13),
            fixedrange=True
        ),
        height=650,
        dragmode=False,
        hovermode='x unified',
        margin=dict(t=80, b=60, l=60, r=60)
    )
    
    # === RENDER GRAFICI AFFIANCATI ===
    col_graph1, col_graph2 = st.columns(2)

    with col_graph1:
        event = st.plotly_chart(
            fig_day_combo,
            use_container_width=True,
            on_select="rerun",
            key="day_chart",
            config={'displayModeBar': False}
        )
        
        # Gestisci il click
        if event and hasattr(event, 'selection') and event.selection:
            points = event.selection.get('points', [])
            if points and len(points) > 0:
                point_index = points[0].get('point_index')
                if point_index is not None:
                    clicked_day = df_day.iloc[point_index]['giorno']
                    if st.session_state.selected_day != clicked_day:
                        st.session_state.selected_day = clicked_day
                        st.rerun()

    with col_graph2:
        st.plotly_chart(
            fig_hour_area,
            use_container_width=True,
            key="hour_chart",
            config={'displayModeBar': False}
        )

# =========================
# 🎨 MAIN FUNCTION
# =========================

def show():
    
    # CSS cursori
    st.markdown("""
    <style>
    /* Forza pointer solo sulle barre */
    .js-plotly-plot .plotly .barlayer,
    .js-plotly-plot .plotly .barlayer * {
        cursor: pointer !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    available_years = utils.get_available_years()

    st.markdown('<div class="section-header">Giorni e orari</div>', unsafe_allow_html=True)

    # Inizializza il session state
    if 'selected_day' not in st.session_state:
        st.session_state.selected_day = None

    # === CONTROLLI ===
    col_ctrl_temp1, col_ctrl_temp2 = st.columns(2)

    with col_ctrl_temp1:
        year_options_temp = ["Tutti gli anni"] + [2000 + year for year in sorted(available_years, reverse=True)]
        
        year_selection_temp = st.selectbox(
            "Seleziona Periodo",
            options=year_options_temp,
            index=0,
            help="Scegli un anno specifico o tutti gli anni per la media",
            key="temp_year_selector"
        )

    with col_ctrl_temp2:
        st.markdown(
            "<div style='font-size:14px; color:#374151; margin-bottom:5px;'>"
            "Clicca su una barra per visualizzare i dettagli orari di quel giorno"
            "</div>",
            unsafe_allow_html=True
        )

        if st.button("🔄 Reset Selezione Giorno"):
            st.session_state.selected_day = None
            st.rerun()

    # Selezione anno
    if year_selection_temp == "Tutti gli anni":
        selected_years_temp, is_average_temp, display_text_temp = available_years, True, "media periodo 2019-2023"
    else:
        year_value = year_selection_temp - 2000
        selected_years_temp, is_average_temp, display_text_temp = [year_value], False, str(year_selection_temp)

    if selected_years_temp:
        years_str = ','.join(map(str, selected_years_temp))
        num_years = len(selected_years_temp)
        
        # === CARICA TUTTI I DATI UNA VOLTA SOLA (CACHED) ===
        df_day_raw, df_hour_all = load_all_temporal_data(years_str)
        
        # === PROCESSA DATI GIORNALIERI ===
        df_day = process_day_data(df_day_raw, num_years if is_average_temp else 1)
        
        # === RENDER GRAFICI NEL FRAGMENT (ricarica veloce) ===
        render_charts(df_day, df_hour_all, num_years, is_average_temp, display_text_temp)