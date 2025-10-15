from Utils import utils
import streamlit as st
import plotly.graph_objects as go

# =========================
# SEZIONE 1: OVERVIEW GENERALE
# =========================

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

    # Grafico 
    fig_yearly = go.Figure()

    # Numero incidenti (sx)
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

    # Tasso mortalità (dx)
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
    xaxis=dict(
        title=dict(
            text="Anno",
            font=dict(size=18),
          
        ),
        tickfont=dict(size=14),  
        type="category"   
    ),
    yaxis=dict(
        title=dict(
            text="Numero di Incidenti",
            font=dict(size=18)   
        ),
        tickfont=dict(size=14)  
    ),
    yaxis2=dict(  
        title=dict(
            text="Tasso di Mortalità (%)",
            font=dict(size=18, color="rgba(231, 76, 60, 1)")
        ),
        tickfont=dict(size=14, color="rgba(231, 76, 60, 1)"),
        overlaying="y",
        side="right",
        showgrid=False,
        tickmode="array",
        tickvals=[],        
        ticktext=[]     
    ),
    font=dict(size=18),
    height=650,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5,
        font=dict(size=14)   #font legenda
    )
)

    #fig_yearly = utils.apply_light_theme_to_fig(fig_yearly)

    st.plotly_chart(fig_yearly, use_container_width=True, config={
        "displayModeBar": False,
        "staticPlot": True
    })
