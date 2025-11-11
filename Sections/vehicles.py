import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from Utils import utils

def show():
    # -------- HEADER --------
    st.markdown(
        """
        <style>
        .section-header {
            font-size: 2.1rem;
            font-weight: bold;
            padding-bottom: 0.3em;
            color: #273c75;
            letter-spacing: 1px;
        }
        .section-subtitle {
            font-size: 1.1rem;
            color: #535c68;
            padding-bottom: 1.2em;
            margin-bottom: 12px;
        }
        .custom-selectbox > div {
            font-size: 1.04rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-header">Veicoli</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>"
        "Tipologie di veicoli coinvolti tra loro"
        "</div>",
        unsafe_allow_html=True
    )

    st.write("")  # Spaziatura

    # -------- SELEZIONE ANNO + Infobox --------
    with st.container():
        col1, col_info = st.columns([2, 1])
        with col1:
            year_options = ["Media di tutti gli anni"] + [
                2000 + y for y in sorted(utils.available_years, reverse=True)
            ]
            year_selection = st.selectbox(
                "Seleziona periodo:",
                options=year_options,
                index=0,
                help="Scegli un anno specifico o tutti gli anni per la media",
                key="veicoli_year_selector",
            )

        with col_info:
            st.markdown(
                """
                <div style="
                    background: linear-gradient(90deg, #f8fafc 60%, #e0e7ef 100%);
                    border-radius: 12px;
                    padding: 13px 15px;
                    font-size: 14px;
                    color: #405867;
                    border: 1.5px solid #e5e9f3;
                    margin-top: 6px;
                    box-shadow: 0 2px 9px rgba(28,42,84,0.075);
                ">
                    <span style="font-size:20px; vertical-align: middle;">🔎</span>
                    <b>Come leggere il grafico</b><br>
                    Ogni cella indica il numero di incidenti in cui sono coinvolti i due tipi di veicoli in riga e in colonna.
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    # -------- DEFINIZIONE ANNI --------
    if year_selection == "Media di tutti gli anni":
        selected_years, is_avg = utils.available_years, True
        subtitle_period = "media annua (2019–2023)"
    else:
        selected_years, is_avg = [year_selection - 2000], False
        subtitle_period = f"anno {year_selection}"

    years_str = ",".join(map(str, selected_years))

    # -------- QUERY --------
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
        st.warning("⚠️ Nessun dato disponibile per il periodo selezionato.")
        return

    if is_avg:
        df["n"] = df["n"] / len(selected_years)

    # -------- COSTRUZIONE MATRICE --------
    custom_order = [
        "Automobile", "Moto", "Mezzo pesante", "Trasporto pubblico",
        "Bicicletta", "Monopattino"
    ]
    matrix = df.pivot_table(index="tipoA", columns="tipoB", values="n", fill_value=0)
    matrix = matrix.reindex(index=custom_order, columns=custom_order)

    # -------- MAPPATURA EMOJI VERTICALI --------
    emoji_map = {
        "Automobile": "🚗",
        "Moto": "🏍️",
        "Mezzo pesante": "🚚",
        "Trasporto pubblico": "🚌",
        "Bicicletta": "🚲",
        "Monopattino": "🛴",
    }
    def label_with_emoji_vertical(label: str) -> str:
        emoji = emoji_map.get(label, "")
        return f"{emoji}\n{label}" if emoji else label

    matrix_display = matrix.copy()
    matrix_display.columns = [label_with_emoji_vertical(c) for c in matrix.columns]
    matrix_display.index = [label_with_emoji_vertical(i) for i in matrix.index]

    # -------- COLORI HEATMAP --------
    colorscale = [
        [0.0, "#fff5f5"],   # rosa chiarissimo
        [0.11, "#fbb6b6"],  # rosa chiaro
        [0.33, "#f87171"],  # rosso medio chiaro
        [0.53, "#ef4444"],  # rosso vivo
        [0.8, "#b91c1c"],   # rosso scuro
        [1.0, "#7f1d1d"]    # rosso molto scuro
    ]

    z_vals = matrix_display.values
    z_max = float(np.max(z_vals)) if np.size(z_vals) > 0 else 0
    z_min = float(np.min(z_vals)) if np.size(z_vals) > 0 else 0
    mid_val = (z_max + z_min) / 2 if z_max > 0 else 0

    # -------- FIGURE --------
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=z_vals,
            x=matrix_display.columns,
            y=matrix_display.index,
            colorscale=colorscale,
            colorbar=dict(
                title="N° incidenti",
                thickness=16,
                len=0.8,
                tickfont=dict(size=12),
                tickcolor="#64748b"
            ),
            hovertemplate=(
                "<b>Veicolo A:</b> %{y}<br>"
                "<b>Veicolo B:</b> %{x}<br>"
                "<b>Incidenti:</b> %{z:.0f}<extra></extra>"
            ),
            showscale=True,
            zmin=0,
            zmax=z_max if z_max > 0 else None,
        )
    )

    # Annotazioni valori heatmap
    for y_idx, y_label in enumerate(matrix_display.index):
        for x_idx, x_label in enumerate(matrix_display.columns):
            val = matrix_display.iloc[y_idx, x_idx]
            if val <= 0:
                continue
            text_color = "white" if (z_max > 0 and val >= mid_val) else "#2d3642"
            fig.add_annotation(
                x=x_label,
                y=y_label,
                text=f"{val:.0f}",
                showarrow=False,
                font=dict(size=12, color=text_color),
                xanchor="center",
                yanchor="middle",
            )

    # Stile degli assi
    fig.update_xaxes(
        showticklabels=True,
        tickangle=0,
        tickfont=dict(size=16, family="Segoe UI Emoji"),
        side="top",
        categoryorder="array",
        categoryarray=[label_with_emoji_vertical(c) for c in custom_order],
    )
    fig.update_yaxes(
        showticklabels=True,
        tickfont=dict(size=16, family="Segoe UI Emoji"),
        automargin=True,
        categoryorder="array",
        categoryarray=[label_with_emoji_vertical(i) for i in custom_order],
        autorange="reversed"
    )

    # Layout generale: altezza aumentata per celle maggiori
    fig.update_layout(
        height=500,
        title=dict(
            text=(
                f"<span style='font-size:15px; color:#64748b;'>{subtitle_period}</span>"
            ),
            x=0.5,
            y=0.99,
            xanchor="center",
            yanchor="top",
            font=dict(size=25, family="Segoe UI"),
            pad=dict(t=30, b=10),
        ),
        margin=dict(l=170, r=80, t=120, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Segoe UI", size=15, color="#222f3e"),
    )

    # -------- OUTPUT --------
    st.plotly_chart(fig, use_container_width=True,  
                    config={
                        "displayModeBar": False,  # nasconde la toolbar
                        "staticPlot": True        # niente zoom/pan/select
    })
