import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from Utils import utils


def show():
    # --- HEADER ---
    st.markdown('<div class="section-header">🚗 Veicoli</div>', unsafe_allow_html=True)
  
    # --- SELEZIONE ANNO ---
    col1, _, _ = st.columns(3)
    with col1:
        year_options = ["Tutti gli anni"] + [2000 + y for y in sorted(utils.available_years, reverse=True)]
        year_selection = st.selectbox(
            "Seleziona periodo",
            options=year_options,
            index=0,
            help="Scegli un anno specifico o tutti gli anni per la media",
            key="veicoli_year_selector"
        )

    # --- DEFINIZIONE ANNI ---
    if year_selection == "Tutti gli anni":
        selected_years, is_avg = utils.available_years, True
    else:
        selected_years, is_avg = [year_selection - 2000], False

    years_str = ','.join(map(str, selected_years))

    # --- QUERY ---
    query = f"""
        SELECT va.gruppo AS tipoA, vb.gruppo AS tipoB, COUNT(*) AS n
        FROM incidenti i
        JOIN tipo_veicolo va ON i.idTipoVeicoloA = va.id
        JOIN tipo_veicolo vb ON i.idTipoVeicoloB = vb.id
        WHERE i.anno IN ({years_str})
        AND i.idTipoVeicoloA IS NOT NULL
        AND i.idTipoVeicoloB IS NOT NULL
        GROUP BY va.gruppo, vb.gruppo

        UNION ALL

        SELECT vb.gruppo AS tipoA, va.gruppo AS tipoB, COUNT(*) AS n
        FROM incidenti i
        JOIN tipo_veicolo va ON i.idTipoVeicoloA = va.id
        JOIN tipo_veicolo vb ON i.idTipoVeicoloB = vb.id
        WHERE i.anno IN ({years_str})
        AND i.idTipoVeicoloA IS NOT NULL
        AND i.idTipoVeicoloB IS NOT NULL
        GROUP BY vb.gruppo, va.gruppo;
    """

    df = utils.run_query(query)

    if df.empty:
        st.warning("Nessun dato disponibile per il periodo selezionato.")
        return

    if is_avg:
        df["n"] = df["n"] / len(selected_years)

    # --- COSTRUZIONE MATRICE ---
    matrix = df.pivot_table(index="tipoA", columns="tipoB", values="n", fill_value=0)
    row_order = matrix.sum(axis=1).sort_values(ascending=False).index
    col_order = matrix.sum(axis=0).sort_values(ascending=False).index
    matrix = matrix.loc[row_order, col_order]

    # --- MAPPATURA EMOJI ---
    emoji_map = {
        "Automobile": "🚗",
        "Moto": "🏍️",
        "Mezzo pesante": "🚚",
        "Trasporto pubblico": "🚌",
        "Bicicletta": "🚲",
        "Pedone": "🚶",
        "Monopattino": "🛴"
    }

    def label_with_emoji(label):
        return f"{emoji_map.get(label, '')} {label}"

    matrix_emoji = matrix.copy()
    matrix_emoji.columns = [label_with_emoji(c) for c in matrix.columns]
    matrix_emoji.index = [label_with_emoji(i) for i in matrix.index]

    # --- HEATMAP: palette moderna blu ---
    colorscale = [
        [0, "#f0f9ff"],
        [0.2, "#bae6fd"],
        [0.4, "#7dd3fc"],
        [0.6, "#38bdf8"],
        [0.8, "#0ea5e9"],
        [1.0, "#0369a1"]
    ]

    z_vals = matrix_emoji.values
    z_max = np.max(z_vals)
    z_min = np.min(z_vals)
    threshold = (z_max + z_min) / 2  # per decidere testo chiaro/scuro

    # --- Costruzione figure ---
    fig = go.Figure()

    # Heatmap principale
    fig.add_trace(go.Heatmap(
        z=z_vals,
        x=matrix_emoji.columns,
        y=matrix_emoji.index,
        colorscale=colorscale,
        colorbar=dict(title="N° Incidenti", thickness=16, tickfont=dict(size=13)),
        hovertemplate="A: %{y}<br>B: %{x}<br><b>Incidenti:</b> %{z}<extra></extra>",
        showscale=True
    ))

    # --- Aggiungi testo adattivo (nero su chiaro, bianco su scuro) ---
    for y_idx, y in enumerate(matrix_emoji.index):
        for x_idx, x in enumerate(matrix_emoji.columns):
            val = matrix_emoji.iloc[y_idx, x_idx]
            color = "white" if val > threshold else "black"
            fig.add_annotation(
                x=x,
                y=y,
                text=f"<b>{int(val)}</b>",
                showarrow=False,
                font=dict(size=14, color=color),
                xanchor="center",
                yanchor="middle"
            )

    # --- STILE ASSI ---
    fig.update_xaxes(
        showticklabels=True,
        tickangle=30,
        tickfont=dict(size=18, family="Segoe UI Emoji")
    )
    fig.update_yaxes(
        showticklabels=True,
        tickfont=dict(size=18, family="Segoe UI Emoji")
    )

    # --- LAYOUT ---
    fig.update_layout(
        title=dict(
            text=f"Coppie di veicoli coinvolti negli incidenti {'(Media annua)' if is_avg else ''}",
            x=0.5,
            xanchor="center",
            font=dict(size=24, family="Arial Black")
        ),
        margin=dict(l=130, r=90, t=100, b=100),
        plot_bgcolor="white",
        paper_bgcolor="white",
        autosize=True
    )

    # --- OUTPUT ---
    st.plotly_chart(fig, use_container_width=True)
