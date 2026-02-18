"""
Fonctions de création de graphiques avec Plotly
"""
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

def create_price_chart(
    df: pd.DataFrame,
    title: str = "Évolution du prix",
    show_volume: bool = True,
    show_ma: bool = True
) -> go.Figure:
    """
    Crée un graphique de prix en ligne
    
    Args:
        df: DataFrame avec colonne 'Close'
        title: Titre du graphique
        show_volume: Afficher le volume
        show_ma: Afficher les moyennes mobiles
        
    Returns:
        go.Figure: Graphique Plotly
    """
    fig = go.Figure()
    
    # Prix
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Prix',
        line=dict(color='#D52B1E', width=2)
    ))
    
    # Moyennes mobiles
    if show_ma and len(df) >= 20:
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MA20'],
                mode='lines',
                name='MA 20',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        if 'MA50' in df.columns and len(df) >= 50:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MA50'],
                mode='lines',
                name='MA 50',
                line=dict(color='purple', width=1, dash='dash')
            ))
    
    # Volume
    if show_volume and 'Volume' in df.columns:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color='lightgray', opacity=0.3)
        ))
    
    fig.update_layout(
        title=title,
        yaxis_title="Prix (₽)",
        yaxis2=dict(
            title="Volume",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_title="Date",
        height=600,
        hovermode='x unified',
        template='plotly_white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def create_candle_chart(
    df: pd.DataFrame,
    title: str = "Graphique en bougies",
    show_volume: bool = True
) -> go.Figure:
    """
    Crée un graphique en bougies japonaises
    
    Args:
        df: DataFrame avec colonnes Open, High, Low, Close
        title: Titre du graphique
        show_volume: Afficher le volume
        
    Returns:
        go.Figure: Graphique Plotly
    """
    fig = go.Figure()
    
    # Bougies
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Bougies',
        increasing_line_color='#0039A6',  # Bleu pour hausse
        decreasing_line_color='#D52B1E'   # Rouge pour baisse
    ))
    
    # Volume
    if show_volume and 'Volume' in df.columns:
        colors = ['#0039A6' if df['Close'].iloc[i] >= df['Open'].iloc[i] 
                  else '#D52B1E' for i in range(len(df))]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            yaxis='y2',
            marker=dict(color=colors, opacity=0.3)
        ))
    
    fig.update_layout(
        title=title,
        yaxis_title="Prix (₽)",
        yaxis2=dict(
            title="Volume",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_title="Date",
        height=600,
        hovermode='x unified',
        template='plotly_white',
        xaxis_rangeslider_visible=False
    )
    
    return fig

def create_comparison_chart(
    data: Dict[str, pd.Series],
    title: str = "Comparaison",
    normalize: bool = True
) -> go.Figure:
    """
    Crée un graphique comparant plusieurs séries
    
    Args:
        data: Dictionnaire {nom: série}
        title: Titre du graphique
        normalize: Normaliser les séries à 100
        
    Returns:
        go.Figure: Graphique Plotly
    """
    fig = go.Figure()
    
    for name, series in data.items():
        y_values = series
        if normalize:
            y_values = (series / series.iloc[0]) * 100
        
        fig.add_trace(go.Scatter(
            x=series.index,
            y=y_values,
            mode='lines',
            name=name
        ))
    
    y_title = "Performance (%)" if normalize else "Valeur"
    
    fig.update_layout(
        title=title,
        yaxis_title=y_title,
        xaxis_title="Date",
        height=500,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_allocation_chart(allocation: Dict[str, float]) -> go.Figure:
    """
    Crée un camembert d'allocation de portefeuille
    
    Args:
        allocation: Dictionnaire {symbole: pourcentage}
        
    Returns:
        go.Figure: Graphique Plotly
    """
    symbols = list(allocation.keys())
    values = list(allocation.values())
    
    colors = px.colors.qualitative.Set3[:len(symbols)]
    
    fig = go.Figure(data=[go.Pie(
        labels=symbols,
        values=values,
        hole=0.4,
        marker=dict(colors=colors)
    )])
    
    fig.update_layout(
        title="Allocation du portefeuille",
        height=400,
        showlegend=True,
        legend=dict(
            yanchor="middle",
            y=0.5,
            xanchor="right",
            x=0.9
        )
    )
    
    return fig

def create_heatmap(
    df: pd.DataFrame,
    title: str = "Carte de chaleur des corrélations"
) -> go.Figure:
    """
    Crée une carte de chaleur des corrélations
    
    Args:
        df: DataFrame avec les rendements
        title: Titre du graphique
        
    Returns:
        go.Figure: Graphique Plotly
    """
    corr_matrix = df.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.round(2).values,
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title=title,
        height=600,
        xaxis_title="Symbole",
        yaxis_title="Symbole"
    )
    
    return fig