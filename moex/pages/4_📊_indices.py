"""
Page des indices MOEX et RTS
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.api.moex_client import MOEXClient
from src.visualization.charts import create_price_chart
from src.utils.formatters import format_currency

def show():
    """Affiche la page des indices"""
    
    st.markdown("# 📊 Indices MOEX & RTS")
    
    # Liste des indices disponibles
    indices = {
        'IMOEX': 'MOEX Russia Index (Roubles)',
        'RTSI': 'RTS Index (Dollars)',
        'RGBI': 'Russian Government Bond Index',
        'MOEX10': 'MOEX 10 Index',
        'MOEXBC': 'MOEX Blue Chip Index',
        'MOEXFNL': 'MOEX Financials Index',
        'MOEXOG': 'MOEX Oil & Gas Index',
        'MOEXMM': 'MOEX Metals & Mining Index'
    }
    
    # Sidebar pour les contrôles
    with st.sidebar:
        st.markdown("## 📈 Configuration indices")
        
        selected_index = st.selectbox(
            "Choisir un indice",
            options=list(indices.keys()),
            format_func=lambda x: f"{x} - {indices[x]}"
        )
        
        period = st.selectbox(
            "Période",
            options=["1m", "3m", "6m", "1y", "5y"],
            index=2
        )
        
        compare_with = st.multiselect(
            "Comparer avec",
            options=[i for i in indices.keys() if i != selected_index],
            default=[]
        )
    
    # Initialisation client
    client = MOEXClient()
    
    # Mapping période -> jours
    period_days = {
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "5y": 1825
    }
    
    # Date de fin = aujourd'hui
    end_date = datetime.now().strftime('%Y-%m-%d')
    # Date de début = aujourd'hui - période
    start_date = (datetime.now() - timedelta(days=period_days[period])).strftime('%Y-%m-%d')
    
    try:
        with st.spinner(f"Chargement des données pour {selected_index}..."):
            # Récupérer les données de l'indice principal
            index_data = client.get_candles(
                selected_index,
                interval=24*60,
                from_date=start_date,
                to_date=end_date
            )
        
        if index_data.empty:
            st.warning(f"Données non disponibles pour {selected_index}")
            return
        
        # Métriques principales
        current_value = index_data['close'].iloc[-1]
        prev_value = index_data['close'].iloc[-2] if len(index_data) > 1 else current_value
        change = current_value - prev_value
        change_pct = (change / prev_value * 100) if prev_value != 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                f"{selected_index}",
                f"{current_value:,.2f}",
                delta=f"{change:+.2f} ({change_pct:+.2f}%)"
            )
        
        with col2:
            st.metric("Plus haut période", f"{index_data['high'].max():,.2f}")
        
        with col3:
            st.metric("Plus bas période", f"{index_data['low'].min():,.2f}")
        
        with col4:
            st.metric("Volume total", f"{index_data['volume'].sum()/1e6:.1f}M")
        
        # Graphique principal
        data_dict = {indices[selected_index]: index_data['close']}
        
        # Ajouter les indices de comparaison
        for idx in compare_with:
            try:
                comp_data = client.get_candles(
                    idx,
                    interval=24*60,
                    from_date=start_date,
                    to_date=end_date
                )
                if not comp_data.empty:
                    data_dict[indices[idx]] = comp_data['close']
            except:
                st.warning(f"Impossible de charger {idx}")
        
        # Créer le graphique
        fig = create_price_chart(index_data, title=f"Évolution {selected_index}", show_volume=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques
        with st.expander("📊 Statistiques détaillées"):
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown("**Statistiques de l'indice**")
                stats_df = pd.DataFrame({
                    'Métrique': ['Moyenne', 'Médiane', 'Écart-type', 'Volatilité'],
                    'Valeur': [
                        f"{index_data['close'].mean():,.2f}",
                        f"{index_data['close'].median():,.2f}",
                        f"{index_data['close'].std():,.2f}",
                        f"{index_data['close'].pct_change().std()*100:.2f}%"
                    ]
                })
                st.dataframe(stats_df, use_container_width=True)
            
            with col_s2:
                st.markdown("**Performance**")
                perf_df = pd.DataFrame({
                    'Période': ['1 semaine', '1 mois', '3 mois', '6 mois', '1 an'],
                    'Performance': [
                        f"{(index_data['close'].iloc[-1] / index_data['close'].iloc[-5] - 1) * 100:.2f}%" if len(index_data) > 5 else "N/A",
                        f"{(index_data['close'].iloc[-1] / index_data['close'].iloc[-20] - 1) * 100:.2f}%" if len(index_data) > 20 else "N/A",
                        f"{(index_data['close'].iloc[-1] / index_data['close'].iloc[-60] - 1) * 100:.2f}%" if len(index_data) > 60 else "N/A",
                        f"{(index_data['close'].iloc[-1] / index_data['close'].iloc[-120] - 1) * 100:.2f}%" if len(index_data) > 120 else "N/A",
                        f"{(index_data['close'].iloc[-1] / index_data['close'].iloc[-250] - 1) * 100:.2f}%" if len(index_data) > 250 else "N/A"
                    ]
                })
                st.dataframe(perf_df, use_container_width=True)
        
        # Composition de l'indice (si disponible)
        with st.expander("📋 Composition de l'indice"):
            st.info("Données de composition non disponibles via l'API standard")
            st.markdown("""
            Les principaux composants typiques sont :
            - **SBER** - Sberbank
            - **GAZP** - Gazprom
            - **LKOH** - Lukoil
            - **GMKN** - Norilsk Nickel
            - **ROSN** - Rosneft
            - **YNDX** - Yandex
            """)
    
    except Exception as e:
        st.error(f"Erreur lors du chargement: {str(e)}")