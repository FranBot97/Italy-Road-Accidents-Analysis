import streamlit as st
import pandas as pd
import json
from Utils import utils
import plotly.graph_objects as go

# ==========================
# CACHE DI BASE
# ==========================

@st.cache_data
def load_geojson(filepath: str):
    """Carica il GeoJSON una sola volta."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=600)
def get_province_data(region_id, years_str, num_years):
    """Province di una singola regione (per il grafico laterale)."""
    query = f"""
    SELECT pr.provincia, pr.popolazione, COUNT(*) AS incidenti
    FROM incidenti i
    JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
    WHERE i.anno IN ({years_str}) AND pr.idRegione = {int(region_id)}
    GROUP BY pr.provincia, pr.popolazione
    ORDER BY COUNT(*) DESC
    """
    return utils.run_query(query)


@st.cache_data(ttl=600)
def get_geo_data(view_mode: str, years_str: str, num_years: int):
    """Calcola i dati geografici (regioni/province)."""
    if view_mode == "Province":
        query_province = f"""
        SELECT pr.idProvincia, pr.provincia, pr.popolazione, COUNT(*) AS incidenti
        FROM incidenti i
        JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
        WHERE i.anno IN ({years_str})
        GROUP BY pr.idProvincia, pr.provincia, pr.popolazione
        """
        df_geo = utils.run_query(query_province)
        df_geo["idProvincia"] = df_geo["idProvincia"].astype(int)
        
        if num_years > 1:
            df_geo['incidenti'] = df_geo['incidenti'] / num_years
        
        df_geo["incidenti_per_100k"] = df_geo["incidenti"] / df_geo["popolazione"] * 100_000
        
        geojson_data = load_geojson("Geo/limits_IT_provinces.geojson")
        location_key = 'prov_istat_code_num'
        id_col = 'idProvincia'
        name_col = 'provincia'
        
    else:
        query_regioni = f"""
        SELECT pr.idRegione, pr.regione AS nome_regione, COUNT(*) AS incidenti
        FROM incidenti i
        JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
        WHERE i.anno IN ({years_str})
        GROUP BY pr.idRegione, pr.regione
        """
        df_regioni = utils.run_query(query_regioni)
        df_regioni["idRegione"] = df_regioni["idRegione"].astype(str).str.zfill(2)
        
        if num_years > 1:
            df_regioni['incidenti'] = df_regioni['incidenti'] / num_years
        
        query_pop = "SELECT id AS idRegione, popolazione FROM regioni"
        df_pop = utils.run_query(query_pop)
        df_pop["idRegione"] = df_pop["idRegione"].astype(str).str.zfill(2)
        
        df_geo = df_regioni.merge(df_pop, on="idRegione", how="left")
        df_geo["incidenti_per_100k"] = df_geo["incidenti"] / df_geo["popolazione"] * 100_000
        
        geojson_data = load_geojson("Geo/limits_IT_regions.geojson")
        location_key = 'reg_istat_code'
        id_col = 'idRegione'
        name_col = 'nome_regione'
    
    return df_geo, geojson_data, location_key, id_col, name_col


def show():
    st.markdown('<div class="section-header">Distribuzione Geografica</div>', unsafe_allow_html=True)

    col_chart, col_filters = st.columns([2, 1])

    # ==========================
    # FILTRI
    # ==========================
    with col_filters:
        st.markdown("<br><br>", unsafe_allow_html=True)
        available_years = utils.available_years
        year_options = ["Media di tutti gli anni"] + [2000 + year for year in sorted(available_years, reverse=True)]
        year_selection_geo = st.selectbox(
            "Seleziona Periodo",
            options=year_options,
            index=0,
            help="Scegli un anno specifico o tutti gli anni per la media"
        )

        view_mode = st.radio("Visualizza per:", ["Regioni", "Province"])
        assoluti = st.toggle("Valori assoluti", value=False)

    # ==========================
    # SCELTA ANNI
    # ==========================
    if year_selection_geo == "Media di tutti gli anni":
        selected_years_geo = available_years
        num_years = len(available_years)
        display_text_geo = "Media 2019-2023"
    else:
        year_value = year_selection_geo - 2000
        selected_years_geo = [year_value]
        num_years = 1
        display_text_geo = str(year_selection_geo)

    years_str = ','.join(map(str, selected_years_geo))

    # ==========================
    # DATI GEO (CACHE)
    # ==========================
    df_geo, geojson_data, location_key, id_col, name_col = get_geo_data(
        view_mode=view_mode,
        years_str=years_str,
        num_years=num_years
    )

    # Scegli la metrica da visualizzare
    if assoluti:
        color_col = 'incidenti'
        hover_label = 'Incidenti'
    else:
        color_col = 'incidenti_per_100k'
        hover_label = 'Incidenti/100k ab.'

    # Prepara customdata per avere entrambi i valori nel tooltip
    df_geo['hover_incidenti'] = df_geo['incidenti'].round(1)
    df_geo['hover_incidenti_100k'] = df_geo['incidenti_per_100k'].round(1)

    # ==========================
    # MAPPA PLOTLY CHOROPLETH
    # ==========================
    fig_map = go.Figure(go.Choroplethmapbox(
        geojson=geojson_data,
        locations=df_geo[id_col],
        z=df_geo[color_col],
        featureidkey=f"properties.{location_key}",
        colorscale="Reds",
        marker_opacity=0.7,
        marker_line_width=1,
        marker_line_color='white',
        text=df_geo[name_col],
        customdata=df_geo[['hover_incidenti', 'hover_incidenti_100k']],
        hovertemplate=(
            '<b>%{text}</b><br>' +
            'Incidenti/100k ab.: %{customdata[1]}<br>' +
            'Incidenti totali: %{customdata[0]}<br>' +
            '<extra></extra>'
        ),
        colorbar=dict(
            title=hover_label,
            thickness=15,
            len=0.7,
            x=0.02,
            xanchor='left'
        ),
        showscale=True
    ))

    fig_map.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=4.8,
        mapbox_center={"lat": 42.5, "lon": 12.5},
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        height=700,
        title=dict(
            text=f"{display_text_geo}",
            font=dict(size=16),
            x=0.5,
            xanchor='center'
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Segoe UI"
        )
    )

    # ==========================
    # RENDER MAPPA + CLICK
    # ==========================
    with col_chart:
        if view_mode == "Regioni":
            # Plotly gestisce i click nativamente!
            map_click = st.plotly_chart(
                fig_map, 
                use_container_width=True, 
                key=f"map_{year_selection_geo}_{assoluti}",
                on_select="rerun",
                selection_mode="points"
            )
            
            # Gestione click
            if map_click and 'selection' in map_click and map_click['selection']['points']:
                clicked_point = map_click['selection']['points'][0]
                region_code = clicked_point.get('location')
                
                if region_code and st.session_state.get('selected_region') != region_code:
                    st.session_state.selected_region = region_code
                    st.rerun()
        else:
            # Province: solo visualizzazione
            st.plotly_chart(
                fig_map, 
                use_container_width=True,
                key=f"map_{year_selection_geo}_{assoluti}"
            )

    # ==========================
    # GRAFICO PROVINCE DELLA REGIONE SELEZIONATA
    # ==========================
    if view_mode == "Regioni" and 'selected_region' in st.session_state:
        with col_filters:
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Reset button
            if st.button("🔄 Deseleziona regione", use_container_width=True):
                del st.session_state.selected_region
                st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)

            df_province_region = get_province_data(
                st.session_state.selected_region,
                years_str,
                num_years
            )

            if not df_province_region.empty:
                if num_years > 1:
                    df_province_region['incidenti'] = df_province_region['incidenti'] / num_years

                df_province_region['incidenti_100k'] = (
                    df_province_region['incidenti'] / df_province_region['popolazione']
                ) * 100_000

                df_province_region = df_province_region.sort_values('incidenti_100k', ascending=True)

                # Nome regione
                nome_regione = df_geo[df_geo[id_col] == st.session_state.selected_region][name_col].iloc[0]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_province_region['incidenti_100k'],
                    y=df_province_region['provincia'],
                    orientation='h',
                    marker=dict(color='#ef4444'),
                    text=df_province_region['incidenti_100k'].round(1),
                    textposition='outside',
                    textfont=dict(size=11),
                    hovertemplate="<b>%{y}</b><br>" +
                                 "Inc./100k: %{x:.1f}<br>" +
                                 "<extra></extra>"
                ))

                fig.update_layout(
                    title=dict(
                        text=f"Province - {nome_regione}",
                        font=dict(size=14),
                        x=0,
                        xanchor='left'
                    ),
                    xaxis_title="Incidenti ogni 100k ab.",
                    yaxis_title="",
                    height=max(350, len(df_province_region) * 35),
                    margin=dict(l=0, r=0, t=80, b=40),
                    showlegend=False,
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True),
                    dragmode=False
                )

                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})