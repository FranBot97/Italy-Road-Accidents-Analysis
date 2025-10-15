import streamlit as st
from Utils import utils
import pandas as pd
import plotly.express as px
import numpy as np

def show():
    st.markdown('<div class="section-header"> Veicoli </div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Analisi delle coppie di veicoli coinvolti negli incidenti</div>', unsafe_allow_html=True)

    col_ctrl_temp1, col_ctrl_temp2, col_ctrl_temp3 = st.columns(3)

    with col_ctrl_temp1:
        year_options_temp = ["Tutti gli anni"] + [2000 + year for year in sorted(utils.available_years, reverse=True)]
        year_selection_temp = st.selectbox(
            "Seleziona periodo",
            options=year_options_temp,
            index=0,
            help="Scegli un anno specifico o tutti gli anni per la media",
            key="temp_year_selector_v"
        )

    if year_selection_temp == "Tutti gli anni":
        selected_years_temp, is_average_temp, display_text_temp = utils.available_years, True, "Media 2019-2023"
    else:
        year_value = year_selection_temp - 2000
        selected_years_temp, is_average_temp, display_text_temp = [year_value], False, str(year_selection_temp)

    heatmap_years_str = ','.join(map(str, selected_years_temp))

    query_heatmap = f"""
        SELECT va.gruppo AS tipoA, vb.gruppo AS tipoB, COUNT(*) AS n
        FROM incidenti i
        JOIN tipo_veicolo va ON i.idTipoVeicoloA = va.id
        JOIN tipo_veicolo vb ON i.idTipoVeicoloB = vb.id
        WHERE i.anno IN ({heatmap_years_str})
        AND i.idTipoVeicoloA IS NOT NULL
        AND i.idTipoVeicoloB IS NOT NULL
        GROUP BY va.gruppo, vb.gruppo

        UNION ALL

        SELECT vb.gruppo AS tipoA, va.gruppo AS tipoB, COUNT(*) AS n
        FROM incidenti i
        JOIN tipo_veicolo va ON i.idTipoVeicoloA = va.id
        JOIN tipo_veicolo vb ON i.idTipoVeicoloB = vb.id
        WHERE i.anno IN ({heatmap_years_str})
        AND i.idTipoVeicoloA IS NOT NULL
        AND i.idTipoVeicoloB IS NOT NULL
        GROUP BY vb.gruppo, va.gruppo;
    """
    df_pairs = utils.run_query(query_heatmap)
    
    if df_pairs.empty:
        st.warning("Nessun dato disponibile con i criteri selezionati.")
    else:
        if is_average_temp:
            df_pairs['n'] = df_pairs['n'] / len(selected_years_temp)
        
        matrix = df_pairs.pivot_table(index="tipoA", columns="tipoB", values="n", fill_value=0)

        row_order = matrix.sum(axis=1).sort_values(ascending=False).index
        col_order = matrix.sum(axis=0).sort_values(ascending=False).index
        matrix = matrix.loc[row_order, col_order]

        icons_map = {
            "Automobile": ("🚗", "Automobile"),
            "Moto": ("🏍️", "Motociclo"),
            "Mezzo pesante": ("🚚", "Camion"),
            "Trasporto pubblico": ("🚌", "Autobus"),
            "Bicicletta": ("🚲", "Bicicletta"),
            "Pedone": ("🚶", "Pedone"),
            "Monopattino": ("🛴", "Monopattino")
        }

        row_labels = [icons_map.get(x, (x, x))[0] for x in matrix.index]
        col_labels = [icons_map.get(x, (x, x))[0] for x in matrix.columns]
        row_hover  = [icons_map.get(x, (x, x))[1] for x in matrix.index]
        col_hover  = [icons_map.get(x, (x, x))[1] for x in matrix.columns]

        values = matrix.values

        fig_hm = px.imshow(
            values,
            x=col_labels,
            y=row_labels,
            color_continuous_scale="Reds",
            aspect="equal",
            title=f"Frequenza incidenti per veicolo - {display_text_temp}"
        )

        #non va tooltip
        fig_hm.update_traces(
            customdata=[[f"{row_hover[i]} - {col_hover[j]}" for j in range(len(col_hover))]
                        for i in range(len(row_hover))],
            hovertemplate="<b style='font-size:16px'>%{customdata}</b><br>" +
                          "<span style='font-size:14px'>Incidenti: %{z}</span><extra></extra>"
        )

        annotations = []
        threshold = values.max() / 2
        for i, row in enumerate(values):
            for j, val in enumerate(row):
                color = "white" if val > threshold else "black"
                annotations.append(dict(
                    x=col_labels[j],
                    y=row_labels[i],
                    text=f"{val:.0f}",
                    showarrow=False,
                    font=dict(color=color, size=14),
                    xanchor="center",
                    yanchor="middle"
                ))

        fig_hm.update_layout(annotations=annotations)

        #fig_hm = utils.apply_light_theme_to_fig(fig_hm)
        fig_hm.update_layout(
            xaxis_title="Tipo Veicolo B",
            yaxis_title="Tipo Veicolo A",
            height=700,
            width=700,
            coloraxis_colorbar=dict(title=f"N° Incidenti{' (Media)' if is_average_temp else ''}"),
            xaxis=dict(tickfont=dict(size=40)),  
            yaxis=dict(tickfont=dict(size=40)),  
        )

        fig_hm.update_layout(
        coloraxis_colorbar=dict(
            ticks="outside",
            tickfont=dict(size=12),
            thickness=15,  
            len=1,       
            y=0.5,          
            yanchor="middle"
        ),
            margin=dict(t=50, b=50, l=50, r=80)  
    )


        # Disabilita tutti i controlli / toolbar
        st.plotly_chart(fig_hm, use_container_width=True, config={
            "displayModeBar": False,
            "staticPlot": True,
        
        })
        
       
