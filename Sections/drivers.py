import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Utils import utils


# =========================
# CACHE: CARICAMENTO DATI
# =========================

@st.cache_data(ttl=3600)
def load_sesso_conducenti():
    """
    Esegue la query per la distribuzione per sesso dei conducenti
    (A + B dove il veicolo B è presente).
    """
    query = """
    SELECT Sesso, COUNT(*) AS conteggio
    FROM (
        SELECT SessoConducenteA AS Sesso
        FROM incidenti
        UNION ALL
        SELECT SessoConducenteB AS Sesso
        FROM incidenti
        WHERE idTipoVeicoloB <> '' 
          AND idTipoVeicoloB IS NOT NULL
    ) AS T1
    GROUP BY Sesso;
    """
    df = utils.run_query(query)

    # Normalizza eventuali valori vuoti / null
    if "Sesso" in df.columns:
        df["Sesso"] = (
            df["Sesso"]
            .fillna("Non dichiarato")
            .replace({"": "Non dichiarato"})
        )

    # Ordina per conteggio desc
    if "conteggio" in df.columns:
        df = df.sort_values("conteggio", ascending=False).reset_index(drop=True)

    return df


@st.cache_data(ttl=3600)
def load_eta_conducenti():
    """
    Esegue la query per la distribuzione per età e sesso dei conducenti
    (A + B dove il veicolo B è presente).
    """
    query = """
    SELECT Eta, Sesso, COUNT(*) as Totale
    FROM (
        SELECT EtaConducenteA as Eta, SessoConducenteA as Sesso
        FROM incidenti
        UNION ALL
        SELECT EtaConducenteB as Eta, SessoConducenteB as Sesso
        FROM incidenti
        WHERE idTipoVeicoloB <> ''
        AND idTipoVeicoloB IS NOT NULL
    ) as T1
    WHERE Sesso <> '' AND Eta <> '' AND Eta NOT LIKE '%n.i%'
    GROUP BY Eta, Sesso
    ORDER BY Eta;
    """
    df = utils.run_query(query)
    return df


# =========================
# FRAGMENT: RENDER GRAFICI
# =========================

@st.fragment
def render_pie(df: pd.DataFrame):
    """Render del pie/donut chart moderno con icone e etichette esterne."""
    if df is None or df.empty:
        st.info("Nessun dato disponibile.")
        return

    color_map = {
        "M": "#3b82f6",
        "F": "#ec4899",
        "Non dichiarato": "#94a3b8"
    }
    colors = [color_map.get(sesso, "#94a3b8") for sesso in df["Sesso"]]

    fig = go.Figure(data=[go.Pie(
        labels=df["Sesso"],
        values=df["conteggio"],
        hole=0.5,
        marker=dict(colors=colors, line=dict(color='white', width=3)),
        textposition='outside',
        texttemplate='<b>%{label}</b><br>%{percent:.1%}<br>(%{value:,})',
        textfont=dict(size=16, family="Arial, sans-serif"),
        hovertemplate='<b>%{label}</b><br>Conducenti: %{value:,}<br>Percentuale: %{percent:.1%}<extra></extra>',
        pull=[0.05 if df["Sesso"].iloc[i] in ["M", "F"] else 0 for i in range(len(df))]
    )])

    total = df["conteggio"].sum()
    fig.update_layout(
        annotations=[
            dict(
                text=f'<span style="font-size:20px; color:#475569"><b>{total:,}</b></span><br><span style="font-size:14px; color:#64748b">Totale<br>conducenti</span>',
                x=0.5, y=0.5, font=dict(size=16), showarrow=False
            )
        ],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=14)),
        margin=dict(t=80, b=80, l=60, r=60),
        height=550,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="drivers_pie_chart")


@st.fragment
def render_age_bar(df: pd.DataFrame):
    """Render bar chart età con opzione suddivisione per sesso."""
    if df is None or df.empty:
        st.info("Nessun dato disponibile.")
        return
    
    view_type = st.radio(
        "Visualizza per:",
        options=["Per età e sesso","Solo per età"],
        horizontal=True,
        key="age_view_toggle",
        index=0
    )
    
    # Aggrega 0-17
    df_processed = df.copy()
    fasce_minorenni = ["0-5  ", "6-9  ", "10-14", "15-17"]
    df_processed.loc[df_processed["Eta"].isin(fasce_minorenni), "Eta"] = "0-17"
    
    # Ordine fasce
    eta_order = ["0-17", "18-29", "30-44", "45-54", "55-64", "65+  "]
    
    # Filtra solo fasce valide
    df_processed = df_processed[df_processed["Eta"].isin(eta_order)]
    
    if view_type == "Solo per età":
        df_plot = df_processed.groupby("Eta", as_index=False)["Totale"].sum()
        df_plot["Eta"] = pd.Categorical(df_plot["Eta"], categories=eta_order, ordered=True)
        df_plot = df_plot.sort_values("Eta")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_plot["Eta"],
            y=df_plot["Totale"],
            marker=dict(color="#4B5563"),
            text=df_plot["Totale"].apply(lambda x: f'{x:,}'),
            textposition='outside',
            textfont=dict(size=10),
            hovertemplate='<b>%{x} anni</b><br>Conducenti: %{y:,}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text="<b>Distribuzione per età</b>", font=dict(size=18, color="#1e293b"), x=0.5, xanchor='center'),
            xaxis=dict(title="Fascia d'età", tickfont=dict(size=12)),
            yaxis=dict(title="Numero conducenti coinvolti", tickformat=',', gridcolor='rgba(0,0,0,0.1)'),
            showlegend=False,
            height=500,
            margin=dict(t=80, b=60, l=80, r=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255,255,255,0.9)'
        )
    
    else:  # Per sesso
        df_pivot = df_processed.groupby(["Eta", "Sesso"], as_index=False)["Totale"].sum()
        df_pivot["Eta"] = pd.Categorical(df_pivot["Eta"], categories=eta_order, ordered=True)
        df_pivot = df_pivot.sort_values("Eta")

        # FIX: Calcola totale per età e converti in dizionario
        tot_by_eta_dict = df_pivot.groupby("Eta", observed=True)["Totale"].sum().to_dict()
        
        df_m = df_pivot[df_pivot["Sesso"] == "M"].copy()
        df_f = df_pivot[df_pivot["Sesso"] == "F"].copy()
        
        # FIX: Usa il dizionario per calcolare le percentuali
        df_m["perc"] = df_m.apply(lambda row: row["Totale"] / tot_by_eta_dict.get(row["Eta"], 1), axis=1)
        df_f["perc"] = df_f.apply(lambda row: row["Totale"] / tot_by_eta_dict.get(row["Eta"], 1), axis=1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Maschi",
            x=df_m["Eta"],
            y=df_m["Totale"],
            marker=dict(color="#3b82f6"),
            text=df_m["perc"].apply(lambda p: f"{p:.1%}"),
            textposition='outside',
            textfont=dict(size=9),
            hovertemplate='<b>Maschi - %{x} anni</b><br>Conducenti: %{y:,}<extra></extra>'
        ))
        fig.add_trace(go.Bar(
            name="Femmine",
            x=df_f["Eta"],
            y=df_f["Totale"],
            marker=dict(color="#ec4899"),
            text=df_f["perc"].apply(lambda p: f"{p:.1%}"),
            textposition='outside',
            textfont=dict(size=9),
            hovertemplate='<b>Femmine - %{x} anni</b><br>Conducenti: %{y:,}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text="<b>Distribuzione per età e sesso</b>", font=dict(size=18, color="#1e293b"), x=0.5, xanchor='center'),
            xaxis=dict(title="Fascia d'età", tickfont=dict(size=12)),
            yaxis=dict(title="Numero conducenti coinvolti", tickformat=',', gridcolor='rgba(0,0,0,0.1)'),
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            height=500,
            margin=dict(t=100, b=60, l=80, r=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255,255,255,0.9)'
        )
    
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="drivers_age_chart")


@st.fragment
def render_minors_pie(df: pd.DataFrame):
    """Dettaglio conducenti minorenni coinvolti"""
    if df is None or df.empty:
        st.info("Nessun dato disponibile.")
        return

    classi_minori = ["0-5  ", "6-9  ", "10-14", "15-17"]
    df_min = (df[df["Eta"].isin(classi_minori)]
              .groupby("Eta", as_index=False)["Totale"].sum())
    if df_min.empty:
        st.info("Nessun dato disponibile per la fascia 0–17.")
        return

    # Ordine coerente
    df_min["Eta"] = pd.Categorical(df_min["Eta"], categories=classi_minori, ordered=True)
    df_min = df_min.sort_values("Eta").reset_index(drop=True)

    # Palette arancione
    colors = ["#FED7AA", "#FDBA74", "#FB923C", "#F97316"]

    fig = go.Figure(data=[go.Pie(
        labels=df_min["Eta"].astype(str).str.strip() + " anni",
        values=df_min["Totale"],
        hole=0.45,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textposition='outside',
        texttemplate='<b>%{label}</b><br>%{percent:.1%}<br>(%{value:,})',
        hovertemplate='<b>%{label}</b><br>Conducenti: %{value:,}<br>Percentuale: %{percent:.1%}<extra></extra>'
    )])

    fig.update_layout(
        title="Dettaglio conducenti minorenni coinvolti",
        showlegend=False,
        margin=dict(t=70, b=50, l=50, r=50),
        height=430,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="drivers_minors_pie")


# =========================
# MAIN: SHOW
# =========================

def show():
    """Entry point usato da main.py -> drivers.show()"""
    st.markdown('<div class="section-header">Profilo conducenti coinvolti</div>', unsafe_allow_html=True)

    # Layout a 2 colonne
    col1, col2 = st.columns(2)
    
    with col1:
        df_sesso = load_sesso_conducenti()
        render_pie(df_sesso)
    
    with col2:
        df_eta = load_eta_conducenti()
        render_age_bar(df_eta)

    # --- NUOVO BLOCCO SOTTO: dettaglio minorenni 0–17 ---
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    render_minors_pie(df_eta)