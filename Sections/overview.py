from Utils import utils
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def show():  
    st.markdown('<div class="section-header">Panoramica</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Trend degli incidenti e delle vittime nel tempo</div>', unsafe_allow_html=True)

    df_yearly_accidents = utils.load_yearly_accident_data_from_db()
    df_yearly_accidents['percentuali_morti'] = (df_yearly_accidents['total_deaths'] / df_yearly_accidents['total_incidents']) * 100
    df_yearly_accidents = df_yearly_accidents.rename(columns={
        'anno': 'Anno',
        'total_incidents': 'Incidenti',
        'total_deaths': 'Morti',
        'percentuali_morti': 'Percentuale morti'
    })

    # Colonne cards 
    col1, col2, col3 = st.columns(3)

    with col1:
        total_incidents = df_yearly_accidents['Incidenti'].sum()
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #667eea; margin: 0;">🚨 Incidenti Totali</h3>
                <h2 style="color: #333; margin: 0.5rem 0;">{str(f"{total_incidents:,}").replace(",", ".")}</h2>
                <p style="color: #666; margin: 0; font-size: 1rem;">2019-2023</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        total_deaths = df_yearly_accidents['Morti'].sum()
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #e74c3c; margin: 0;">💀 Vittime Totali</h3>
                <h2 style="color: #333; margin: 0.5rem 0;">{str(f"{total_deaths:,}").replace(",", ".")}</h2>
                <p style="color: #666; margin: 0; font-size: 1rem;">2019-2023</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_mortality = df_yearly_accidents['Percentuale morti'].mean()
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #f39c12; margin: 0;">Tasso mortalità medio</h3>
                <h2 style="color: #333; margin: 0.5rem 0;">{avg_mortality:.2f}%</h2>
                <p style="color: #666; margin: 0; font-size: 1rem;">2019-2023</p>
            </div>
        """, unsafe_allow_html=True)

    # Layout a 2 colonne: grafico temporale + pie chart geografico
    col_trend, col_geo = st.columns([2, 1])

    with col_trend:
        # Grafico temporale
        fig_yearly = go.Figure()

        fig_yearly.add_trace(go.Scatter(
            x=df_yearly_accidents["Anno"],
            y=df_yearly_accidents["Incidenti"],
            mode='lines+markers+text',   
            name="Incidenti",
            line=dict(color='rgba(102, 126, 234, 0.9)', width=4),
            marker=dict(size=10, color='rgba(102, 126, 234, 1)'),
            text=[f"{v:,}".replace(",", ".") for v in df_yearly_accidents["Incidenti"]],
            textposition="top center",                  
            textfont=dict(size=14, color="black"),
            hovertemplate="<b>Anno %{x}</b><br>Incidenti: %{y:,}<extra></extra>"
        ))

        fig_yearly.add_trace(go.Scatter(
            x=df_yearly_accidents["Anno"],
            y=df_yearly_accidents["Percentuale morti"],
            mode='lines+markers+text',   
            name="Tasso mortalità (%)",
            line=dict(color='rgba(231, 76, 60, 0.9)', width=4, dash="dash"),
            marker=dict(size=10, color='rgba(231, 76, 60, 1)'),
            yaxis="y2",
            text=[f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "%" 
                  for v in df_yearly_accidents["Percentuale morti"]],
            textposition="top center",
            textfont=dict(size=14, color="rgba(231, 76, 60, 1)"),
            hovertemplate="<b>Anno %{x}</b><br>Tasso mortalità: %{y:.2f}%<extra></extra>"
        ))

        fig_yearly.update_layout(
            title=dict(
                text="",
                #text="<b>Trend temporale</b>",
                font=dict(size=18, color="#1e293b"),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title=dict(text="Anno", font=dict(size=16)),
                tickfont=dict(size=14),  
                type="category"   
            ),
            yaxis=dict(
                title=dict(text="Numero di Incidenti", font=dict(size=16)),
                tickfont=dict(size=14)  
            ),
            yaxis2=dict(  
                title=dict(
                    text="Tasso di Mortalità (%)",
                    font=dict(size=16, color="rgba(231, 76, 60, 1)")
                ),
                tickfont=dict(size=14, color="rgba(231, 76, 60, 1)"),
                overlaying="y",
                side="right",
                showgrid=False,
                tickmode="array",
                tickvals=[],        
                ticktext=[]     
            ),
            height=600,
            margin=dict(t=80, b=80, l=80, r=80),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=14)
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255,255,255,0.9)'
        )

        st.plotly_chart(fig_yearly, use_container_width=True, config={
            "displayModeBar": False,
            "staticPlot": True
        })

    with col_geo:
        # Query per ottenere incidenti per area geografica
        query_geo = """
        SELECT r.Area, COUNT(*) AS incidenti
        FROM incidenti i
        JOIN province_regioni pr ON i.idProvincia = pr.idProvincia
        JOIN regioni r ON pr.idRegione = r.id
        GROUP BY r.Area
        ORDER BY r.Area
        """
        df_geo = utils.run_query(query_geo)
        
        # Pulisci eventuali spazi bianchi e normalizza "Sud" in "Sud e isole"
        df_geo['Area'] = df_geo['Area'].str.strip()
        df_geo['Area'] = df_geo['Area'].replace('Sud', 'Sud e isole')
        
        # Ordine desiderato - usa un dizionario per il sort
        area_order = {"Nord": 1, "Centro": 2, "Sud e isole": 3}
        df_geo['sort_order'] = df_geo['Area'].map(area_order)
        df_geo = df_geo.sort_values('sort_order').drop(columns='sort_order')
        
        # Colori per aree
        color_map = {
            "Nord": "#3b82f6",           # Blu
            "Centro": "#22c55e",         # Verde
            "Sud e isole": "#f97316"     # Arancione
        }
        colors = [color_map.get(area, "#94a3b8") for area in df_geo['Area']]
        
        # Pie chart
        fig_geo = go.Figure(data=[go.Pie(
            labels=df_geo['Area'],
            values=df_geo['incidenti'],
            hole=0.45,
            marker=dict(colors=colors, line=dict(color='white', width=3)),
            textposition='outside',
            texttemplate='<b>%{label}</b><br>%{percent:.1%}<br>(%{value:,})',
            textfont=dict(size=14, family="Arial, sans-serif"),
            hovertemplate='<b>%{label}</b><br>Incidenti: %{value:,}<br>Percentuale: %{percent:.1%}<extra></extra>',
            pull=[0.05] * len(df_geo)
        )])
        
        total_geo = df_geo['incidenti'].sum()
        
        fig_geo.update_layout(
            title=dict(
                text="",
                #text="<b>Distribuzione geografica</b>",
                font=dict(size=18, color="#1e293b"),
                x=0.5,
                xanchor='center'
            ),
            annotations=[
                dict(
                    text=f'<b style="font-size:24px">🇮🇹</b><br><span style="font-size:18px; color:#475569"><b>{total_geo:,}</b></span><br><span style="font-size:12px; color:#64748b">Incidenti<br>totali</span>',
                    x=0.5, y=0.5,
                    font=dict(size=14),
                    showarrow=False
                )
            ],
            showlegend=False,
            height=600,
            margin=dict(t=80, b=60, l=40, r=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_geo, use_container_width=True, config={"displayModeBar": False})