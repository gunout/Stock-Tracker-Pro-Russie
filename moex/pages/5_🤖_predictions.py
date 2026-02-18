"""
Page des prédictions ML
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_squared_error, r2_score
import plotly.graph_objs as go

from src.api.moex_client import MOEXClient
from src.utils.formatters import format_currency

def show():
    """Affiche la page des prédictions"""
    
    st.markdown("# 🤖 Prédictions Machine Learning")
    
    st.markdown("""
    Cette page utilise des modèles simples de machine learning pour prédire les tendances futures.
    **Note :** Ces prédictions sont à titre indicatif seulement et ne constituent pas des conseils d'investissement.
    """)
    
    # Sidebar pour les paramètres
    with st.sidebar:
        st.markdown("## ⚙️ Paramètres du modèle")
        
        # Sélection de l'action
        client = MOEXClient()
        try:
            securities_df = client.get_securities()
            if not securities_df.empty:
                ticker_options = securities_df['SECID'].tolist()
                selected_ticker = st.selectbox(
                    "Action",
                    options=ticker_options,
                    index=0 if ticker_options else 0
                )
            else:
                selected_ticker = st.selectbox(
                    "Action",
                    options=st.session_state.watchlist,
                    index=0
                )
        except:
            selected_ticker = st.selectbox(
                "Action",
                options=st.session_state.watchlist,
                index=0
            )
        
        # Paramètres du modèle
        col1, col2 = st.columns(2)
        
        with col1:
            days_history = st.number_input(
                "Jours d'historique",
                min_value=30,
                max_value=500,
                value=100,
                step=10
            )
            
            days_prediction = st.number_input(
                "Jours à prédire",
                min_value=1,
                max_value=30,
                value=7,
                step=1
            )
        
        with col2:
            model_degree = st.slider(
                "Complexité du modèle",
                min_value=1,
                max_value=5,
                value=2,
                help="Degré du polynôme (plus élevé = plus complexe)"
            )
            
            confidence = st.checkbox("Afficher intervalle de confiance", value=True)
    
    try:
        # Chargement des données
        with st.spinner("Chargement des données historiques..."):
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_history)).strftime('%Y-%m-%d')
            
            hist_data = client.get_candles(
                selected_ticker,
                interval=24*60,
                from_date=start_date,
                to_date=end_date
            )
        
        if hist_data.empty or len(hist_data) < 30:
            st.warning("Pas assez de données historiques pour faire des prédictions fiables")
            return
        
        # Préparation des données
        df = hist_data[['close']].copy()
        df['days'] = (df.index - df.index.min()).days
        
        X = df['days'].values.reshape(-1, 1)
        y = df['close'].values
        
        # Création et entraînement du modèle
        model = make_pipeline(
            PolynomialFeatures(degree=model_degree),
            LinearRegression()
        )
        model.fit(X, y)
        
        # Prédictions
        last_day = X[-1][0]
        future_days = np.arange(last_day + 1, last_day + days_prediction + 1).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        # Métriques du modèle
        y_pred = model.predict(X)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y, y_pred)
        
        # Affichage des métriques
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric("RMSE", format_currency(rmse))
        
        with col_m2:
            st.metric("MAE", format_currency(np.mean(np.abs(y - y_pred))))
        
        with col_m3:
            st.metric("R²", f"{r2:.3f}")
        
        # Création du graphique
        fig = go.Figure()
        
        # Données historiques
        fig.add_trace(go.Scatter(
            x=df.index,
            y=y,
            mode='lines',
            name='Historique',
            line=dict(color='blue', width=2)
        ))
        
        # Prédictions
        last_date = df.index[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_prediction)]
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions,
            mode='lines+markers',
            name='Prédictions',
            line=dict(color='red', dash='dash'),
            marker=dict(size=8)
        ))
        
        # Intervalle de confiance
        if confidence:
            residuals = y - y_pred
            std_residuals = np.std(residuals)
            
            upper_bound = predictions + 2 * std_residuals
            lower_bound = predictions - 2 * std_residuals
            
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=np.concatenate([upper_bound, lower_bound[::-1]]),
                fill='toself',
                fillcolor='rgba(255,0,0,0.2)',
                line=dict(color='rgba(255,0,0,0)'),
                name='Intervalle de confiance 95%'
            ))
        
        fig.update_layout(
            title=f"Prédictions pour {selected_ticker} - {days_prediction} jours",
            xaxis_title="Date",
            yaxis_title="Prix (₽)",
            height=600,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tableau des prédictions
        st.markdown("### 📋 Prédictions détaillées")
        
        current_price = y[-1]
        pred_df = pd.DataFrame({
            'Date': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Prix prédit': [format_currency(p) for p in predictions],
            'Variation %': [f"{(p/current_price - 1)*100:.2f}%" for p in predictions],
            'Limite inférieure': [format_currency(p - 2*std_residuals) for p in predictions] if confidence else ['N/A'] * days_prediction,
            'Limite supérieure': [format_currency(p + 2*std_residuals) for p in predictions] if confidence else ['N/A'] * days_prediction
        })
        
        st.dataframe(pred_df, use_container_width=True)
        
        # Analyse de la tendance
        st.markdown("### 📈 Analyse de la tendance")
        
        last_price = current_price
        last_pred = predictions[-1]
        
        if last_pred > last_price * 1.05:
            trend = "🚀 Forte tendance haussière"
            color = "green"
        elif last_pred > last_price:
            trend = "📈 Légère tendance haussière"
            color = "lightgreen"
        elif last_pred < last_price * 0.95:
            trend = "🔻 Forte tendance baissière"
            color = "red"
        elif last_pred < last_price:
            trend = "📉 Légère tendance baissière"
            color = "salmon"
        else:
            trend = "➡️ Tendance latérale"
            color = "gray"
        
        st.markdown(f"<h3 style='color: {color};'>{trend}</h3>", unsafe_allow_html=True)
        
        # Avertissement
        st.warning("""
        **⚠️ Avertissement important :**
        - Les prédictions sont basées uniquement sur les données historiques de prix
        - Elles ne prennent pas en compte les fondamentaux de l'entreprise
        - Les marchés financiers sont imprévisibles et peuvent varier considérablement
        - Ces informations ne constituent pas des conseils d'investissement
        """)
        
    except Exception as e:
        st.error(f"Erreur lors du chargement: {str(e)}")