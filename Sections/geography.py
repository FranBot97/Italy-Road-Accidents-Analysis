import streamlit as st
import pandas as pd
import folium
from folium import plugins
import json
import streamlit_folium as st_folium
from Utils import utils

def show():
    st.markdown('<div class="section-header">Distribuzione Geografica</div>', unsafe_allow_html=True)

    # Layout: filtri a sinistra, mappa a destra
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

        normalizza = False
        if view_mode == "Regioni":
            normalizza = st.toggle("Normalizza per popolazione", value=False)

    # Parsing selezione anni
    if year_selection_geo == "Media di tutti gli anni":
        selected_years_geo, is_average_geo, display_text_geo = available_years, True, "Media 2019-2023"
    else:
        year_value = year_selection_geo - 2000
        selected_years_geo, is_average_geo, display_text_geo = [year_value], False, str(year_selection_geo)

    years_str = ','.join(map(str, selected_years_geo))

    # Query e preparazione dati
    if view_mode == "Province":
        query_province = f"""
        SELECT pr.idProvincia, pr.provincia, COUNT(*) AS incidenti
        FROM incidenti i
        JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
        WHERE i.anno IN ({years_str})
        GROUP BY pr.idProvincia, pr.provincia
        """
        df_geo = utils.run_query(query_province)
        df_geo["idProvincia"] = df_geo["idProvincia"].astype(int)
        
        if is_average_geo:
            df_geo['incidenti'] = df_geo['incidenti'] / len(selected_years_geo)

        with open("Geo/limits_IT_provinces.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        
        # Aggiungi nome provincia e incidenti al geojson per tooltip
        data_dict = dict(zip(df_geo['idProvincia'], df_geo['incidenti']))
        provincia_dict = dict(zip(df_geo['idProvincia'], df_geo['provincia']))
        
        for feature in geojson_data['features']:
            prov_id = feature['properties']['prov_istat_code_num']
            feature['properties']['incidenti'] = data_dict.get(prov_id, 0)
            feature['properties']['nome_display'] = provincia_dict.get(prov_id, "N/A")
        
        location_key = 'prov_istat_code_num'
        value_label = "Incidenti"
        
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

        with open("Geo/limits_IT_regions.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        
        # Prepara i dati per folium
        if normalizza:
            data_dict = dict(zip(df_geo['idRegione'], df_geo['incidenti_per_100k']))
            value_label = "Incidenti ogni 100k ab."
        else:
            data_dict = dict(zip(df_geo['idRegione'], df_geo['incidenti']))
            value_label = "Incidenti"
        
        # Aggiungi nome regione e dati al geojson per tooltip
        nome_dict = dict(zip(df_geo['idRegione'], df_geo['nome_regione']))
        
        for feature in geojson_data['features']:
            reg_id = feature['properties']['reg_istat_code']
            feature['properties']['incidenti'] = data_dict.get(reg_id, 0)
            feature['properties']['nome_display'] = nome_dict.get(reg_id, "N/A")
        
        location_key = 'reg_istat_code'

    # Crea la mappa Folium ULTRA-MINIMALE
    m = folium.Map(
        location=[41.9, 12.5],  # Centro Italia
        zoom_start=6,
        tiles=None,  # Nessuna tile di base
        scrollWheelZoom=False,  # Disabilita zoom con scroll
        dragging=False,         # Disabilita trascinamento
        zoomControl=False,      # Nasconde controlli zoom
        doubleClickZoom=False,  # Disabilita doppio click zoom
        keyboard=False,         # Disabilita controlli tastiera
        attributionControl=False  # Nasconde attribuzione
    )

    # Aggiungi tile personalizzata minimale - SOLO ITALIA
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
        attr='me',  # Nessuna attribuzione
        name="Minimal",
        overlay=False,
        control=False  # Nasconde controllo layer
    ).add_to(m)

    # ALTERNATIVA ancora più minimale - solo sfondo bianco:
    # folium.TileLayer(
    #     tiles='https://tiles.stadiamaps.com/tiles/stamen_toner_background/{z}/{x}/{y}{r}.png',
    #     attr='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>',
    #     name="Minimal White",
    #     overlay=False,
    #     control=True
    # ).add_to(m)

    # Crea il choropleth
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=df_geo,
        columns=[df_geo.columns[0], 'incidenti'] if view_mode == "Province" else 
                [df_geo.columns[0], 'incidenti_per_100k' if normalizza else 'incidenti'],
        key_on=f'properties.{location_key}',
        fill_color='Reds',  # Cambiato da Blues a Reds per più contrasto
        fill_opacity=0.8,
        line_opacity=0.9,
        line_color='white',
        line_weight=2,
        legend_name=f'{value_label} - {display_text_geo}'
    ).add_to(m)

    # Tooltip migliorato con nomi E TESTO CORTO
    if view_mode == "Regioni" and normalizza:
        tooltip_aliases = ['📍 Nome:', '🚗 Inc./100k:']  # Testo abbreviato
    else:
        tooltip_aliases = ['📍 Nome:', f'🚗 {value_label}:']
    
    tooltip = folium.GeoJsonTooltip(
        fields=['nome_display', 'incidenti'],
        aliases=tooltip_aliases,
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
            max-width: 180px;
            white-space: nowrap;
        """,
        max_width=180
    )

    # Layer con highlight SUBTILE - solo illuminazione
    geojson_layer = folium.GeoJson(
        geojson_data,
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'transparent', 
            'weight': 0,
            'fillOpacity': 0,
        },
        highlight_function=lambda x: {
            'fillColor': 'rgba(255, 255, 255, 0.3)',  # Bianco translucido per illuminare
            'color': 'rgba(255, 255, 255, 0.8)',      # Bordo bianco sottile
            'weight': 1,
            'fillOpacity': 0.4,
        },
        tooltip=tooltip
    ).add_to(m)

    # Stile CSS per la mappa FISSA
    st.markdown("""
    <style>
    .folium-map {
        border: 2px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        pointer-events: auto;
    }
    
    /* Nasconde TUTTI i controlli */
    .leaflet-control-attribution,
    .leaflet-control-zoom,
    .leaflet-control-layers {
        display: none !important;
    }
    
    /* Disabilita cursore di trascinamento */
    .leaflet-container {
        cursor: default !important;
    }
    
    .leaflet-dragging .leaflet-container {
        cursor: default !important;
    }
    
    /* Stile tooltip personalizzato */
    .leaflet-tooltip {
        animation: fadeIn 0.3s ease-in;
        font-size: 13px !important;
        line-height: 1.3 !important;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    with col_chart:
        # Renderizza la mappa FISSA
        map_data = st_folium.st_folium(
            m, 
            width=700, 
            height=600,
            returned_objects=["last_object_clicked"],
            key="italy_map"  # Key unica per evitare ricaricamenti
        )
        
        # Info compatta sulla selezione
        if map_data.get('last_object_clicked'):
            clicked_data = map_data['last_object_clicked']
            if 'properties' in clicked_data:
                props = clicked_data['properties']
                nome = props.get('nome_display', 'N/A')
                incidenti = props.get('incidenti', 0)
                
                st.markdown(f"""
                <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 12px; border-radius: 8px; 
                           text-align: center; margin-top: 10px;'>
                    <strong>📍 {nome}</strong><br>
                    <span style='font-size: 18px;'>{incidenti:,.1f}</span> {value_label.lower()}
                </div>
                """, unsafe_allow_html=True)