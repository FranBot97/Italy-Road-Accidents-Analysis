import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import plotly.express as px

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
def load_yearly_accident_data_from_db():
    conn = sqlite3.connect("dbAccidents.db")
    query = """
    SELECT
        anno,
        COUNT(*) AS total_incidents,
        SUM(Morti) AS total_deaths
    FROM
        incidenti
    GROUP BY
        anno
    ORDER BY
        anno;
    """
    df_yearly = pd.read_sql_query(query, conn)
    conn.close()
    return df_yearly

df_yearly_accidents = load_yearly_accident_data_from_db()

# Calculate percentages
df_yearly_accidents['percentuali_morti'] = (df_yearly_accidents['total_deaths'] / df_yearly_accidents['total_incidents']) * 100

# Rename columns for Plotly
df_yearly_accidents = df_yearly_accidents.rename(columns={
    'anno': 'Anno',
    'total_incidents': 'Incidenti',
    'total_deaths': 'Morti',
    'percentuali_morti': 'Percentuale morti'
})

# Create the interactive chart
fig = px.bar(
    df_yearly_accidents,
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

# Re-establish connection for the next section if it was closed
# (or ensure it's only opened once and closed at the end of the script)
# For now, keeping it separate for clarity of each section's data needs.
# conn = sqlite3.connect("dbAccidents.db") # This line is already present above the province map

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

st.header("🗓️ Incidenti per Giorno della Settimana")

# Get available years from the database
conn = sqlite3.connect("dbAccidents.db")
available_years_query = "SELECT DISTINCT anno FROM incidenti ORDER BY anno DESC;"
available_years_df = pd.read_sql_query(available_years_query, conn)
available_years = available_years_df['anno'].tolist()

# Year selection for the day of week graph
selected_years_day_of_week = st.multiselect(
    "Seleziona gli anni per l'analisi per giorno della settimana",
    options=available_years,
    default=available_years # Default to all years for average
)

if not selected_years_day_of_week:
    st.warning("Seleziona almeno un anno per visualizzare i dati per giorno della settimana.")
else:
    years_str_day_of_week = ','.join(map(str, selected_years_day_of_week))

    query_day_of_week = f"""
    SELECT
        g.giorno,
        COUNT(*) AS numero_incidenti
    FROM
        incidenti i
    JOIN
        giorno g ON i.idGiorno = g.id
    WHERE
        i.anno IN ({years_str_day_of_week})
    GROUP BY
        g.giorno
    ORDER BY
        g.id;
    """
    df_day_of_week = pd.read_sql_query(query_day_of_week, conn)

    # Define the correct order of days of the week
    day_order = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    df_day_of_week['giorno'] = pd.Categorical(df_day_of_week['giorno'], categories=day_order, ordered=True)
    df_day_of_week = df_day_of_week.sort_values('giorno')

    # Calculate average if multiple years are selected
    if len(selected_years_day_of_week) > 1:
        df_day_of_week['numero_incidenti'] = df_day_of_week['numero_incidenti'] / len(selected_years_day_of_week)
        y_axis_title_day_of_week = "Numero medio di incidenti"
        chart_title_day_of_week = f"Numero medio di incidenti per Giorno della Settimana ({', '.join(map(str, selected_years_day_of_week))})"
    else:
        y_axis_title_day_of_week = "Numero di incidenti"
        chart_title_day_of_week = f"Numero di incidenti per Giorno della Settimana ({selected_years_day_of_week[0]})"

    fig_day_of_week = px.bar(
        df_day_of_week,
        x="giorno",
        y="numero_incidenti",
        title=chart_title_day_of_week,
        labels={
            "giorno": "Giorno della Settimana",
            "numero_incidenti": y_axis_title_day_of_week
        },
        color_discrete_sequence=px.colors.qualitative.Pastel # A nice color palette
    )
    fig_day_of_week.update_layout(xaxis_title="Giorno della Settimana", yaxis_title=y_axis_title_day_of_week)
    st.plotly_chart(fig_day_of_week, use_container_width=True)

st.header("⏰ Incidenti per Ora del Giorno")

# Year selection for the time of day graph (re-using available_years)
selected_years_time_of_day = st.multiselect(
    "Seleziona gli anni per l'analisi oraria",
    options=available_years,
    default=available_years # Default to all years for average
)

# Day of week selection for the time of day graph
day_order_full = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
selected_days_time_of_day = st.multiselect(
    "Seleziona i giorni della settimana per l'analisi oraria",
    options=day_order_full,
    default=day_order_full # Default to all days
)

if not selected_years_time_of_day or not selected_days_time_of_day:
    st.warning("Seleziona almeno un anno e un giorno della settimana per visualizzare i dati orari.")
else:
    years_str_time_of_day = ','.join(map(str, selected_years_time_of_day))
    
    # Map day names back to their IDs for the SQL query
    day_to_id_map = {
        "Lunedì": 1, "Martedì": 2, "Mercoledì": 3, "Giovedì": 4,
        "Venerdì": 5, "Sabato": 6, "Domenica": 7
    }
    selected_day_ids = [str(day_to_id_map[day]) for day in selected_days_time_of_day]
    days_str_time_of_day = ','.join(selected_day_ids)

    query_time_of_day = f"""
    SELECT
        i.Ora,
        COUNT(*) AS numero_incidenti
    FROM
        incidenti i
    WHERE
        i.anno IN ({years_str_time_of_day}) AND i.idGiorno IN ({days_str_time_of_day})
    GROUP BY
        i.Ora
    ORDER BY
        i.Ora;
    """
    df_time_of_day = pd.read_sql_query(query_time_of_day, conn)
    conn.close()

    # Ensure all 24 hours are present, even if no accidents occurred
    all_hours_df = pd.DataFrame({'Ora': range(24)})
    df_time_of_day = pd.merge(all_hours_df, df_time_of_day, on='Ora', how='left').fillna(0)

    # Calculate average if multiple years are selected
    if len(selected_years_time_of_day) > 1:
        df_time_of_day['numero_incidenti'] = df_time_of_day['numero_incidenti'] / len(selected_years_time_of_day)
        y_axis_title_time_of_day = "Numero medio di incidenti"
        chart_title_time_of_day = f"Numero medio di incidenti per Ora del Giorno ({', '.join(selected_days_time_of_day)}) - Anni: ({', '.join(map(str, selected_years_time_of_day))})"
    else:
        y_axis_title_time_of_day = "Numero di incidenti"
        chart_title_time_of_day = f"Numero di incidenti per Ora del Giorno ({', '.join(selected_days_time_of_day)}) - Anno: ({selected_years_time_of_day[0]})"

    fig_time_of_day = px.line(
        df_time_of_day,
        x="Ora",
        y="numero_incidenti",
        title=chart_title_time_of_day,
        labels={
            "Ora": "Ora del Giorno",
            "numero_incidenti": y_axis_title_time_of_day
        },
        line_shape="spline" # Makes the lines smooth and continuous
    )

    fig_time_of_day.update_xaxes(
        tickmode="linear",
        dtick=1, # Show every hour
        range=[0, 23] # Ensure full 24-hour range is shown
    )
    fig_time_of_day.update_yaxes(rangemode="tozero") # Start y-axis from zero
    fig_time_of_day.update_layout(hovermode="x unified") # Unified hover for better comparison

    st.plotly_chart(fig_time_of_day, use_container_width=True)
