import streamlit as st
import pandas as pd
import folium
from folium import plugins
import json
import streamlit_folium as st_folium
from Utils import utils
import plotly.graph_objects as go
from shapely.geometry import Point, shape

# CACHE per caricare GeoJSON una sola volta
@st.cache_data
def load_geojson(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# CACHE per query province di una regione
@st.cache_data(ttl=600)
def get_province_data(region_id, years_str, num_years):
    query = f"""
    SELECT pr.provincia, pr.popolazione, COUNT(*) AS incidenti
    FROM incidenti i
    JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
    WHERE i.anno IN ({years_str}) AND pr.idRegione = {int(region_id)}
    GROUP BY pr.provincia, pr.popolazione
    ORDER BY COUNT(*) DESC
    """
    return utils.run_query(query)

def show():
    st.markdown('<div class="section-header">Distribuzione Geografica</div>', unsafe_allow_html=True)

    # Layout
    col_chart, col_filters = st.columns([2,1])

    # ---- FILTRI ----
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

        normalizza = st.toggle("Normalizza per popolazione", value=True)
        
        # Bottone reset per regioni
        # if view_mode == "Regioni" and 'selected_region' in st.session_state:
        #     st.markdown("---")
        #     st.info(f"📍 Regione selezionata")
        #     if st.button("🔄 Reset Selezione"):
        #         del st.session_state.selected_region
        #         st.rerun()

    # Selezione anni
    if year_selection_geo == "Media di tutti gli anni":
        selected_years_geo, is_average_geo, display_text_geo = available_years, True, "Media 2019-2023"
    else:
        year_value = year_selection_geo - 2000
        selected_years_geo, is_average_geo, display_text_geo = [year_value], False, str(year_selection_geo)

    years_str = ','.join(map(str, selected_years_geo))

    # Queries
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
        
        if is_average_geo:
            df_geo['incidenti'] = df_geo['incidenti'] / len(selected_years_geo)
        
        # Calcola incidenti per 100k abitanti
        df_geo["incidenti_per_100k"] = df_geo["incidenti"] / df_geo["popolazione"] * 100_000
        df_geo["incidenti_assoluti"] = df_geo["incidenti"]

        geojson_data = load_geojson("Geo/limits_IT_provinces.geojson")
        
        # Aggiungo nomi province e dati
        if normalizza:
            data_dict = dict(zip(df_geo['idProvincia'], df_geo['incidenti_per_100k']))
            value_label = "Incidenti ogni 100k ab."
        else:
            data_dict = dict(zip(df_geo['idProvincia'], df_geo['incidenti']))
            value_label = "Incidenti"
        
        provincia_dict = dict(zip(df_geo['idProvincia'], df_geo['provincia']))
        incidenti_100k_dict = dict(zip(df_geo['idProvincia'], df_geo['incidenti_per_100k']))
        incidenti_abs_dict = dict(zip(df_geo['idProvincia'], df_geo['incidenti_assoluti']))
        
        for feature in geojson_data['features']:
            prov_id = feature['properties']['prov_istat_code_num']
            feature['properties']['incidenti'] = data_dict.get(prov_id, 0)
            feature['properties']['nome_display'] = provincia_dict.get(prov_id, "N/A")
            feature['properties']['incidenti_100k'] = incidenti_100k_dict.get(prov_id, 0)
            feature['properties']['incidenti_assoluti'] = incidenti_abs_dict.get(prov_id, 0)
        
        location_key = 'prov_istat_code_num'

    # Regioni    
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

        if is_average_geo:
            df_regioni['incidenti'] = df_regioni['incidenti'] / len(selected_years_geo)

        query_pop = "SELECT id AS idRegione, popolazione FROM regioni"
        df_pop = utils.run_query(query_pop)
        df_pop["idRegione"] = df_pop["idRegione"].astype(str).str.zfill(2)

        df_geo = df_regioni.merge(df_pop, on="idRegione", how="left")
        df_geo["incidenti_per_100k"] = df_geo["incidenti"] / df_geo["popolazione"] * 100_000
        df_geo["incidenti_assoluti"] = df_geo["incidenti"]

        geojson_data = load_geojson("Geo/limits_IT_regions.geojson")
        
        if normalizza:
            data_dict = dict(zip(df_geo['idRegione'], df_geo['incidenti_per_100k']))
            value_label = "Incidenti ogni 100k ab."
        else:
            data_dict = dict(zip(df_geo['idRegione'], df_geo['incidenti']))
            value_label = "Incidenti"

        nome_dict = dict(zip(df_geo['idRegione'], df_geo['nome_regione']))
        incidenti_100k_dict = dict(zip(df_geo['idRegione'], df_geo['incidenti_per_100k']))
        incidenti_abs_dict = dict(zip(df_geo['idRegione'], df_geo['incidenti_assoluti']))
        
        for feature in geojson_data['features']:
            reg_id = feature['properties']['reg_istat_code']
            feature['properties']['incidenti'] = data_dict.get(reg_id, 0)
            feature['properties']['nome_display'] = nome_dict.get(reg_id, "N/A")
            feature['properties']['incidenti_100k'] = incidenti_100k_dict.get(reg_id, 0)
            feature['properties']['incidenti_assoluti'] = incidenti_abs_dict.get(reg_id, 0)
        
        location_key = 'reg_istat_code'

    # Mappa config
    m = folium.Map(
        location=[42.0, 12.5],
        zoom_start=5.5,
        tiles=None,  
        scrollWheelZoom=False,  
        dragging=False,      
        zoomControl=False,     
        doubleClickZoom=False,
        keyboard=False,         
        attributionControl=False,
        prefer_canvas=True  # OTTIMIZZAZIONE: usa canvas invece di SVG
    )

    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
        attr='me',
        name="Minimal",
        overlay=False,
        control=False  
    ).add_to(m)

    # Choropleth - SOLO per colorazione, NON per click
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=df_geo,
        columns=[df_geo.columns[0], 'incidenti_per_100k' if normalizza else 'incidenti'],
        key_on=f'properties.{location_key}',
        fill_color='Reds',  
        fill_opacity=0.7,
        line_opacity=0,
        legend_name=f'{value_label} - {display_text_geo}',
        smooth_factor=1.5  # OTTIMIZZAZIONE: semplifica geometrie
    ).add_to(m)

    # Tooltip
    if view_mode == "Regioni":
        tooltip = folium.GeoJsonTooltip(
            fields=['nome_display', 'incidenti_100k', 'incidenti_assoluti'],
            aliases=['Regione:', 'Incidenti/100k ab:', 'Incidenti assoluti:'],
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid #333;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 12px;
                max-width: 280px;
                white-space: nowrap;
            """,
            max_width=280
        )
    else:
        tooltip = folium.GeoJsonTooltip(
            fields=['nome_display', 'incidenti_100k', 'incidenti_assoluti'],
            aliases=['Provincia:', 'Incidenti/100k ab:', 'Incidenti assoluti:'],
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid #333;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 12px;
                max-width: 280px;
                white-space: nowrap;
            """,
            max_width=280
        )
    
    # GeoJson layer SOPRA la choropleth - questo gestisce click e hover
    if view_mode == "Regioni":
        # Ottieni la regione selezionata (se esiste)
        selected_region = st.session_state.get('selected_region', None)
        
        # Per regioni: layer semi-trasparente CLICCABILE con evidenziazione per regione selezionata
        geojson_layer = folium.GeoJson(
            geojson_data,
            style_function=lambda x: {
                'fillColor': 'rgba(255, 215, 0, 0.3)' if x['properties'].get(location_key) == selected_region else 'rgba(0,0,0,0)',
                'color': '#FFD700' if x['properties'].get(location_key) == selected_region else 'white',
                'weight': 3 if x['properties'].get(location_key) == selected_region else 2,
                'fillOpacity': 0.3 if x['properties'].get(location_key) == selected_region else 0,
            },
            highlight_function=lambda x: {
                'fillColor': 'rgba(255, 255, 255, 0.2)',  
                'color': 'yellow',
                'weight': 3,
                'fillOpacity': 0.3,
            },
            tooltip=tooltip,
            smooth_factor=2.0  # OTTIMIZZAZIONE: semplifica ulteriormente
        ).add_to(m)
    else:
        # Per province: solo tooltip, NO click
        geojson_layer = folium.GeoJson(
            geojson_data,
            style_function=lambda x: {
                'fillColor': 'rgba(0,0,0,0)',
                'color': 'white',
                'weight': 2,
                'fillOpacity': 0,
            },
            highlight_function=lambda x: {
                'fillColor': 'rgba(255, 255, 255, 0.2)',
                'color': 'yellow',
                'weight': 3,
                'fillOpacity': 0.3,
            },
            tooltip=tooltip,
            smooth_factor=2.0  # OTTIMIZZAZIONE
        ).add_to(m)

    # CSS per la mappa
    click_enabled = "cursor: pointer !important;" if view_mode == "Regioni" else "cursor: default !important;"
    
    st.markdown(f"""
    <style>
    .folium-map {{
        border: 2px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    
    .leaflet-control-attribution,
    .leaflet-control-zoom,
    .leaflet-control-layers {{
        display: none !important;
    }}
    
    .leaflet-container {{
        cursor: default !important;
    }}
    
    /* ABILITA click sulle regioni */
    .leaflet-interactive {{
        pointer-events: auto !important;
        {click_enabled}
    }}
    
    .leaflet-tooltip {{
        animation: fadeIn 0.3s ease-in;
        font-size: 13px !important;
        line-height: 1.3 !important;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .leaflet-bottom.leaflet-right {{
        left: 10px !important;
        right: auto !important;
        bottom: 10px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Mostra mappa CON gestione click
    with col_chart:
        if view_mode == "Regioni":
            # Abilita la cattura del click
            map_data = st_folium.st_folium(
                m, 
                width=700, 
                height=750,
                returned_objects=["last_object_clicked"],
                key=f"map_{year_selection_geo}_{normalizza}"
            )
            
            # Gestione del click - USANDO LE COORDINATE (con cache)
            if map_data and "last_object_clicked" in map_data and map_data["last_object_clicked"]:
                clicked = map_data["last_object_clicked"]
                
                # Estrai coordinate
                if isinstance(clicked, dict) and "lat" in clicked and "lng" in clicked:
                    clicked_lat = clicked["lat"]
                    clicked_lng = clicked["lng"]
                    
                    # CACHE della ricerca geometrica
                    cache_key = f"{round(clicked_lat, 4)}_{round(clicked_lng, 4)}"
                    if 'click_cache' not in st.session_state:
                        st.session_state.click_cache = {}
                    
                    if cache_key not in st.session_state.click_cache:
                        # Trova la regione dalle coordinate usando il geojson
                        point = Point(clicked_lng, clicked_lat)
                        
                        region_code = None
                        for feature in geojson_data['features']:
                            polygon = shape(feature['geometry'])
                            if polygon.contains(point):
                                region_code = feature['properties'].get(location_key)
                                break
                        
                        st.session_state.click_cache[cache_key] = region_code
                    else:
                        region_code = st.session_state.click_cache[cache_key]
                    
                    # CONTROLLA se è una regione NUOVA prima di fare rerun
                    if region_code and st.session_state.get('selected_region') != region_code:
                        st.session_state.selected_region = region_code
                        st.rerun()
        else:
            # Province: NO click
            st_folium.st_folium(
                m, 
                width=700, 
                height=750,
                key=f"map_{year_selection_geo}_{normalizza}"
            )
    
    # Grafico province della regione selezionata
    if view_mode == "Regioni" and 'selected_region' in st.session_state:
        with col_filters:
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Query CACHED per le province
            df_province_region = get_province_data(
                st.session_state.selected_region,
                years_str,
                len(selected_years_geo)
            )
            
            if not df_province_region.empty:
                if is_average_geo:
                    df_province_region['incidenti'] = df_province_region['incidenti'] / len(selected_years_geo)
                
                # Calcola incidenti per 100k
                df_province_region['incidenti_100k'] = (df_province_region['incidenti'] / df_province_region['popolazione']) * 100_000
                
                # Ordina per incidenti per 100k
                df_province_region = df_province_region.sort_values('incidenti_100k', ascending=True)
                
                # Nome regione
                nome_regione = nome_dict.get(st.session_state.selected_region, "Regione")
                
                # Grafico orizzontale
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df_province_region['incidenti_100k'],
                    y=df_province_region['provincia'],
                    orientation='h',
                    marker=dict(
                        color='#ef4444'
                    ),
                    text=df_province_region['incidenti_100k'].round(1),
                    textposition='outside',
                    textfont=dict(size=11),
                    hovertemplate="<b>%{y}</b><br>" +
                                 "Inc./100k: %{x:.1f}<br>" +
                                 "<extra></extra>"
                ))
                max_value = df_province_region['incidenti_100k'].max();

                fig.update_layout(
                    title=dict(
                        text=f"Province {nome_regione}",
                        font=dict(size=14),
                        x=0,  # Allinea il titolo a sinistra
                        xanchor='left'
                    ),
                    xaxis_title="Incidenti ogni 100k ab.",
                    yaxis_title="",
                    height=max(300, len(df_province_region) * 35),
                    margin=dict(l=0, r=0, t=80, b=40),
                    showlegend=False,
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True),
                    
                    dragmode=False
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})