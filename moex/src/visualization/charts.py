"""
Fonctions de création de graphiques
"""
import plotly.graph_objs as go
import pandas as pd

def create_price_chart(df: pd.DataFrame, title: str = "Évolution du prix", show_volume: bool = True):
    """
    Crée un graphique de prix en ligne
    
    Args:
        df: DataFrame avec colonne 'Close'
        title: Titre du graphique
        show_volume: Afficher le volume
    
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
    
    # Volume (optionnel)
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
        height=500,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_candle_chart(df: pd.DataFrame, title: str = "Graphique en bougies", show_volume: bool = True):
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
        increasing_line_color='#0039A6',
        decreasing_line_color='#D52B1E'
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
        height=500,
        hovermode='x unified',
        template='plotly_white',
        xaxis_rangeslider_visible=False
    )
    
    return fig
