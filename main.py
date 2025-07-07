import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

st.set_page_config(page_title="Incidenti in Italia", layout="wide")
st.title("🚗 Incidenti stradali in Italia (2018–2022)")

st.markdown("""
    <style>
        body {
            background-color: white !important;
        }
        .main {
            background-color: white !important;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_clean_data():
    # Read datasets
    paths = [f"Dataset/INCSTRAD_Microdati_{anno}.csv" for anno in range(2019, 2023)]
    anni = list(range(2019, 2023))
    data = [pd.read_csv(p) for p in paths]

    # Clean function
    def remove_rows(df):
        df = df.dropna(subset=["veicolo__a___et__conducente", "Ora", "giorno"])
        df = df[df["tipo_veicoli__b_"].notnull()].dropna(subset=["veicolo__b___sesso_conducente", "veicolo__b___et__conducente"])
        return df

    data = [remove_rows(df) for df in data]
    return dict(zip(anni, data))

dati = load_and_clean_data()

# Calcola numero incidenti e percentuale di morti
anni = list(dati.keys())
incidenti = [dati[anno].shape[0] for anno in anni]
percentuali_morti = [dati[anno]["morti"].sum() / dati[anno].shape[0] * 100 for anno in anni]

import plotly.express as px

# Ricalcola i dati se non li hai già
incidenti_totali = [dati[anno].shape[0] for anno in anni]
incidenti_mortali = [dati[anno]["morti"].sum() for anno in anni]
percentuali_morti = [m / tot * 100 for m, tot in zip(incidenti_mortali, incidenti_totali)]

# Crea un DataFrame per Plotly
df_plot = pd.DataFrame({
    "Anno": anni,
    "Incidenti": incidenti_totali,
    "Morti": incidenti_mortali,
    "Percentuale morti": percentuali_morti
})

# Crea il grafico interattivo
fig = px.bar(
    df_plot,
    x="Anno",
    y="Incidenti",
    text="Morti",
    hover_data={
        "Anno": False,
        "Incidenti": True,
        "Morti": True,
        "Percentuale morti": ':.2f'
    },
    labels={"Incidenti": "Numero di incidenti"},
    title="Incidenti stradali per anno"
)

fig.update_traces(marker_color='lightskyblue', textposition='outside',  width=0.4)
fig.update_layout(yaxis_title="Numero di incidenti", height=500)

st.plotly_chart(fig, use_container_width=True)

st.header("🗺️ Mappa interattiva degli incidenti per provincia")

# Connetti al database
conn = sqlite3.connect("dbAccidents.db")

# Slider anno (inserito qui per coerenza visiva)
anno_sel = st.slider("Seleziona l'anno", min_value=2018, max_value=2023, value=2022, step=1)

# Query incidenti per provincia
query_province = f"""
SELECT pr.idProvincia, pr.provincia, COUNT(*) AS incidenti
FROM incidenti i
JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
WHERE i.anno = {anno_sel % 100}
GROUP BY pr.idProvincia, pr.provincia
"""
df_province = pd.read_sql_query(query_province, conn)
df_province["idProvincia"] = df_province["idProvincia"].astype(int)


import json 

# Carica GeoJSON province
with open("Geo/limits_IT_provinces.geojson", "r", encoding="utf-8") as f:
    geojson_province = json.load(f)

# Mappa province
fig_provincia = px.choropleth(
    df_province,
    geojson=geojson_province,
    locations="idProvincia",
    featureidkey="properties.prov_istat_code_num",
    color="incidenti",
    hover_name="provincia",
    color_continuous_scale="Reds",
    title=f"Incidenti stradali per provincia - {anno_sel}"
)
fig_provincia.update_geos(fitbounds="locations", visible=False)
fig_provincia.update_layout(margin={"r":0,"t":50,"l":0,"b":0}, height=600)
st.plotly_chart(fig_provincia, use_container_width=True)

import sqlite3

st.header("🗺️ Mappa interattiva degli incidenti per regione")

# Query incidenti per regione
query_regioni = f"""
SELECT pr.idRegione, pr.regione AS nome_regione, COUNT(*) AS incidenti
FROM incidenti i
JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
WHERE i.anno = {anno_sel % 100}
GROUP BY pr.idRegione, pr.regione
"""
df_regioni = pd.read_sql_query(query_regioni, conn)
df_regioni["idRegione"] = df_regioni["idRegione"].astype(str).str.zfill(2)

# Query popolazione
query_pop = "SELECT id AS idRegione, popolazione FROM regioni"
df_pop = pd.read_sql_query(query_pop, conn)
df_pop["idRegione"] = df_pop["idRegione"].astype(str).str.zfill(2)


# Merge e calcolo normalizzati
df_regioni = df_regioni.merge(df_pop, on="idRegione", how="left")
df_regioni["incidenti_per_100k"] = df_regioni["incidenti"] / df_regioni["popolazione"] * 100_000

# Calcola range massimo per la scala colore
max_incidenti = df_regioni["incidenti"].max()
max_per_100k = df_regioni["incidenti_per_100k"].max()
df_regioni["incidenti"] = df_regioni["incidenti"].astype(float)
df_regioni["incidenti_per_100k"] = df_regioni["incidenti_per_100k"].astype(float)


# Toggle
normalizza = st.toggle("Normalizza per popolazione (per 100.000 abitanti)", value=False)

# Carica GeoJSON regioni
with open("Geo/limits_IT_regions.geojson", "r", encoding="utf-8") as f:
    geojson_regioni = json.load(f)

# Mappa regioni
fig_regioni = px.choropleth(
    df_regioni,
    geojson=geojson_regioni,
    locations="idRegione",
    featureidkey="properties.reg_istat_code",
    color="incidenti_per_100k" if normalizza else "incidenti",
    hover_name="nome_regione",
    hover_data={
        "incidenti": True,
        "incidenti_per_100k": ':.2f',
        "popolazione": True,
        "idRegione": False
    },
    color_continuous_scale="Oranges",
    range_color=[0, max_incidenti if not normalizza else max_per_100k],
    title=f"Incidenti stradali per regione - {anno_sel} ({'normalizzati' if normalizza else 'assoluti'})"
)



fig_regioni.update_geos(fitbounds="locations", visible=False)
fig_regioni.update_layout(
    margin={"r":0,"t":50,"l":0,"b":0},
    height=600
)
st.plotly_chart(fig_regioni, use_container_width=True)
