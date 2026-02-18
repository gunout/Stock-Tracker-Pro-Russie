"""
Page de configuration
"""
import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

def show():
    """Affiche la page de configuration"""
    
    st.markdown("# ⚙️ Configuration")
    
    # Initialisation des variables de session si nécessaire
    if 'preferences' not in st.session_state:
        st.session_state.preferences = {
            'theme': 'Clair',
            'language': 'Français',
            'chart_style': 'Ligne',
            'refresh_rate': 60,
            'default_period': '1mo',
            'show_indicators': True
        }
    
    if 'email_config' not in st.session_state:
        st.session_state.email_config = {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': '',
            'password': ''
        }
    
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {
            'alpha_vantage': '',
            'twelve_data': '',
            'market_stack': ''
        }
    
    # Onglets de configuration
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎨 Apparence",
        "📧 Notifications",
        "🔑 APIs",
        "📊 Données",
        "ℹ️ À propos"
    ])
    
    with tab1:
        st.markdown("### 🎨 Apparence et préférences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "Thème",
                options=["Clair", "Sombre"],
                index=0 if st.session_state.preferences.get('theme') == "Clair" else 1
            )
            
            language = st.selectbox(
                "Langue",
                options=["Français", "English", "Русский"],
                index=["Français", "English", "Русский"].index(
                    st.session_state.preferences.get('language', 'Français')
                )
            )
            
            default_period = st.selectbox(
                "Période par défaut",
                options=["1j", "5j", "1m", "3m", "6m", "1a"],
                index=["1j", "5j", "1m", "3m", "6m", "1a"].index(
                    st.session_state.preferences.get('default_period', '1m')
                )
            )
        
        with col2:
            chart_style = st.selectbox(
                "Style de graphique par défaut",
                options=["Ligne", "Bougies"],
                index=0 if st.session_state.preferences.get('chart_style') == "Ligne" else 1
            )
            
            refresh_rate = st.slider(
                "Taux de rafraîchissement (secondes)",
                min_value=30,
                max_value=300,
                value=st.session_state.preferences.get('refresh_rate', 60),
                step=30
            )
            
            show_indicators = st.checkbox(
                "Afficher les indicateurs techniques par défaut",
                value=st.session_state.preferences.get('show_indicators', True)
            )
        
        st.markdown("---")
        
        # Devise préférée
        currency = st.radio(
            "Devise préférée",
            options=["RUB (Rouble russe)", "USD (Dollar américain)"],
            horizontal=True,
            index=0
        )
        
        # Sauvegarde des préférences
        if st.button("💾 Sauvegarder les préférences", use_container_width=True):
            st.session_state.preferences.update({
                'theme': theme,
                'language': language,
                'chart_style': chart_style,
                'refresh_rate': refresh_rate,
                'default_period': default_period,
                'show_indicators': show_indicators,
                'currency': 'RUB' if 'RUB' in currency else 'USD'
            })
            st.success("✅ Préférences sauvegardées !")
            st.rerun()
    
    with tab2:
        st.markdown("### 📧 Configuration des notifications email")
        st.mark.markdown("""
        Configurez les notifications par email pour recevoir des alertes lorsque vos actions atteignent certains prix.
        Les emails sont envoyés via SMTP. Pour Gmail, vous devez utiliser un mot de passe d'application.
        """)
        
        with st.form("email_config_form"):
            enabled = st.checkbox(
                "Activer les notifications email",
                value=st.session_state.email_config.get('enabled', False)
            )
            
            st.markdown("#### Paramètres du serveur SMTP")
            
            col1, col2 = st.columns(2)
            
            with col1:
                smtp_server = st.text_input(
                    "Serveur SMTP",
                    value=st.session_state.email_config.get('smtp_server', 'smtp.gmail.com'),
                    help="Ex: smtp.gmail.com, smtp.office365.com, etc."
                )
                
                smtp_port = st.number_input(
                    "Port SMTP",
                    value=st.session_state.email_config.get('smtp_port', 587),
                    min_value=1,
                    max_value=65535,
                    help="587 pour TLS, 465 pour SSL"
                )
            
            with col2:
                email = st.text_input(
                    "Adresse email",
                    value=st.session_state.email_config.get('email', ''),
                    placeholder="votre@email.com"
                )
                
                password = st.text_input(
                    "Mot de passe",
                    type="password",
                    value=st.session_state.email_config.get('password', ''),
                    help="Pour Gmail, utilisez un mot de passe d'application"
                )
            
            st.markdown("#### Options de notification")
            
            notify_on_trigger = st.checkbox(
                "Notifier quand une alerte se déclenche",
                value=True
            )
            
            notify_daily = st.checkbox(
                "Rapport quotidien récapitulatif",
                value=False
            )
            
            test_email = st.text_input(
                "Email de test (optionnel)",
                placeholder="exemple@email.com",
                help="Envoyer un email de test à cette adresse"
            )
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.form_submit_button("💾 Sauvegarder"):
                    st.session_state.email_config = {
                        'enabled': enabled,
                        'smtp_server': smtp_server,
                        'smtp_port': smtp_port,
                        'email': email,
                        'password': password,
                        'notify_on_trigger': notify_on_trigger,
                        'notify_daily': notify_daily
                    }
                    st.success("✅ Configuration email sauvegardée !")
            
            with col_btn2:
                if st.form_submit_button("📨 Tester"):
                    if test_email:
                        try:
                            # Simulation d'envoi d'email
                            st.info(f"📧 Email de test simulé envoyé à {test_email}")
                            st.success("✅ Test réussi (simulation)")
                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")
                    else:
                        st.warning("⚠️ Veuillez entrer un email de test")
            
            with col_btn3:
                if st.form_submit_button("🔄 Réinitialiser"):
                    st.session_state.email_config = {
                        'enabled': False,
                        'smtp_server': 'smtp.gmail.com',
                        'smtp_port': 587,
                        'email': '',
                        'password': ''
                    }
                    st.success("✅ Configuration réinitialisée")
                    st.rerun()
    
    with tab3:
        st.markdown("### 🔑 Configuration des APIs externes")
        
        st.markdown("""
        L'application utilise principalement l'**API publique MOEX** qui ne nécessite pas de clé.
        Pour des fonctionnalités avancées ou des sources de données alternatives, 
        vous pouvez configurer les APIs suivantes :
        """)
        
        # Alpha Vantage
        with st.expander("📈 Alpha Vantage API", expanded=False):
            st.markdown("""
            [Alpha Vantage](https://www.alphavantage.co/) fournit des données financières historiques et en temps réel.
            
            **Comment obtenir une clé :**
            1. Allez sur [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
            2. Remplissez le formulaire avec votre email
            3. Vous recevrez une clé API gratuite par email
            
            **Limites :** 5 requêtes par minute, 500 par jour
            """)
            
            alpha_key = st.text_input(
                "Clé API Alpha Vantage",
                type="password",
                value=st.session_state.api_keys.get('alpha_vantage', ''),
                key="alpha_key"
            )
            
            if st.button("Sauvegarder clé Alpha Vantage", key="save_alpha"):
                st.session_state.api_keys['alpha_vantage'] = alpha_key
                st.success("✅ Clé Alpha Vantage sauvegardée !")
        
        # Twelve Data
        with st.expander("📊 Twelve Data API", expanded=False):
            st.markdown("""
            [Twelve Data](https://twelvedata.com/) offre des données en temps réel et historiques.
            
            **Comment obtenir une clé :**
            1. Allez sur [twelvedata.com/apikey](https://twelvedata.com/apikey)
            2. Créez un compte gratuit
            3. Votre clé API sera disponible dans le dashboard
            
            **Limites :** 800 requêtes par jour
            """)
            
            twelve_key = st.text_input(
                "Clé API Twelve Data",
                type="password",
                value=st.session_state.api_keys.get('twelve_data', ''),
                key="twelve_key"
            )
            
            if st.button("Sauvegarder clé Twelve Data", key="save_twelve"):
                st.session_state.api_keys['twelve_data'] = twelve_key
                st.success("✅ Clé Twelve Data sauvegardée !")
        
        # Market Stack
        with st.expander("🌍 Market Stack API", expanded=False):
            st.markdown("""
            [Market Stack](https://marketstack.com/) fournit des données boursières mondiales.
            
            **Comment obtenir une clé :**
            1. Allez sur [marketstack.com/signup/free](https://marketstack.com/signup/free)
            2. Créez un compte gratuit
            3. Votre clé API sera envoyée par email
            
            **Limites :** 1000 requêtes par mois
            """)
            
            market_key = st.text_input(
                "Clé API Market Stack",
                type="password",
                value=st.session_state.api_keys.get('market_stack', ''),
                key="market_key"
            )
            
            if st.button("Sauvegarder clé Market Stack", key="save_market"):
                st.session_state.api_keys['market_stack'] = market_key
                st.success("✅ Clé Market Stack sauvegardée !")
        
        # Test des APIs
        st.markdown("#### 🧪 Test des connexions API")
        
        if st.button("Tester toutes les APIs configurées", use_container_width=True):
            with st.spinner("Test des connexions API..."):
                results = []
                
                # Test MOEX (toujours disponible)
                results.append({"API": "MOEX Officielle", "Statut": "✅ OK", "Note": "Publique"})
                
                # Test Alpha Vantage
                if st.session_state.api_keys.get('alpha_vantage'):
                    results.append({"API": "Alpha Vantage", "Statut": "🔑 Configurée", "Note": "À tester"})
                else:
                    results.append({"API": "Alpha Vantage", "Statut": "⚪ Non configurée", "Note": ""})
                
                # Test Twelve Data
                if st.session_state.api_keys.get('twelve_data'):
                    results.append({"API": "Twelve Data", "Statut": "🔑 Configurée", "Note": "À tester"})
                else:
                    results.append({"API": "Twelve Data", "Statut": "⚪ Non configurée", "Note": ""})
                
                # Test Market Stack
                if st.session_state.api_keys.get('market_stack'):
                    results.append({"API": "Market Stack", "Statut": "🔑 Configurée", "Note": "À tester"})
                else:
                    results.append({"API": "Market Stack", "Statut": "⚪ Non configurée", "Note": ""})
                
                st.dataframe(pd.DataFrame(results), use_container_width=True)
    
    with tab4:
        st.markdown("### 📊 Gestion des données et cache")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💾 Cache**")
            cache_size = len(st.session_state.get('data_cache', {}))
            st.write(f"Entrées en cache mémoire : {cache_size}")
            
            # Taille estimée du cache fichier
            cache_dir = "cache"
            if os.path.exists(cache_dir):
                file_count = len([f for f in os.listdir(cache_dir) if f.endswith('.pkl')])
                st.write(f"Fichiers cache : {file_count}")
                
                # Taille totale
                total_size = sum(os.path.getsize(os.path.join(cache_dir, f)) 
                                for f in os.listdir(cache_dir) if f.endswith('.pkl'))
                st.write(f"Taille du cache : {total_size / 1024:.2f} KB")
            else:
                st.write("Aucun cache fichier")
            
            if st.button("🗑️ Vider le cache mémoire", use_container_width=True):
                st.session_state.data_cache = {}
                st.cache_data.clear()
                st.success("✅ Cache mémoire vidé !")
                st.rerun()
            
            if st.button("🗑️ Vider tous les caches", use_container_width=True):
                st.session_state.data_cache = {}
                st.cache_data.clear()
                
                # Supprimer les fichiers cache
                if os.path.exists(cache_dir):
                    for f in os.listdir(cache_dir):
                        if f.endswith('.pkl'):
                            os.remove(os.path.join(cache_dir, f))
                
                st.success("✅ Tous les caches ont été vidés !")
                st.rerun()
        
        with col2:
            st.markdown("**📥 Export des données**")
            
            # Export de la configuration utilisateur
            config_export = {
                'watchlist': st.session_state.watchlist,
                'portfolio': st.session_state.portfolio if hasattr(st.session_state, 'portfolio') else {},
                'price_alerts': st.session_state.price_alerts,
                'email_config': {k: v for k, v in st.session_state.email_config.items() if k != 'password'},
                'preferences': st.session_state.preferences,
                'export_date': datetime.now().isoformat()
            }
            
            st.download_button(
                label="📥 Exporter la configuration",
                data=json.dumps(config_export, indent=2, default=str),
                file_name=f"moex_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            st.markdown("**📤 Import de configuration**")
            uploaded_file = st.file_uploader(
                "Choisir un fichier de configuration",
                type=['json'],
                help="Importez une configuration précédemment exportée"
            )
            
            if uploaded_file is not None:
                try:
                    imported_config = json.load(uploaded_file)
                    
                    if st.button("✅ Confirmer l'import"):
                        if 'watchlist' in imported_config:
                            st.session_state.watchlist = imported_config['watchlist']
                        if 'portfolio' in imported_config:
                            st.session_state.portfolio = imported_config['portfolio']
                        if 'price_alerts' in imported_config:
                            st.session_state.price_alerts = imported_config['price_alerts']
                        if 'preferences' in imported_config:
                            st.session_state.preferences.update(imported_config['preferences'])
                        
                        st.success("✅ Configuration importée avec succès !")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'import: {e}")
        
        st.markdown("---")
        
        # Watchlist management
        st.markdown("### 📋 Gestion de la watchlist")
        
        current_watchlist = st.session_state.watchlist.copy()
        
        col_w1, col_w2 = st.columns(2)
        
        with col_w1:
            st.markdown("**Watchlist actuelle :**")
            for i, symbol in enumerate(current_watchlist):
                col_sym, col_del = st.columns([3, 1])
                with col_sym:
                    st.write(f"{i+1}. {symbol}")
                with col_del:
                    if st.button("🗑️", key=f"del_wl_{i}"):
                        st.session_state.watchlist.pop(i)
                        st.rerun()
        
        with col_w2:
            st.markdown("**Ajouter un symbole :**")
            new_symbol = st.text_input("Nouveau symbole", placeholder="Ex: SBER").upper()
            
            if st.button("➕ Ajouter à la watchlist", use_container_width=True):
                if new_symbol and new_symbol not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_symbol)
                    st.success(f"✅ {new_symbol} ajouté à la watchlist")
                    st.rerun()
                elif new_symbol in st.session_state.watchlist:
                    st.warning(f"⚠️ {new_symbol} est déjà dans la watchlist")
        
        if st.button("🔄 Réinitialiser la watchlist par défaut", use_container_width=True):
            st.session_state.watchlist = [
                'SBER', 'GAZP', 'LKOH', 'ROSN', 'GMKN',
                'YNDX', 'MTSS', 'NVTK', 'MGNT', 'TATN'
            ]
            st.success("✅ Watchlist réinitialisée")
            st.rerun()
    
    with tab5:
        st.markdown("### ℹ️ À propos de l'application")
        
        col_a1, col_a2 = st.columns([1, 2])
        
        with col_a1:
            st.image("https://img.icons8.com/color/240/000000/russian-federation.png", width=150)
        
        with col_a2:
            st.markdown("""
            ## 🇷🇺 Dashboard MOEX
            
            **Version :** 1.0.0
            
            Application de suivi en temps réel des actions de la Bourse de Moscou (MOEX)
            utilisant l'API officielle MOEX ISS.
            
            **Fonctionnalités :**
            - 📈 Suivi en temps réel des prix
            - 💰 Portefeuille virtuel
            - 🔔 Alertes de prix personnalisées
            - 📊 Indices MOEX et RTS
            - 🤖 Prédictions ML simples
            - ⚙️ Configuration personnalisable
            
            **Sources de données :**
            - API officielle MOEX ISS (https://iss.moex.com/iss/reference/)
            - APIs alternatives (optionnelles)
            """)
        
        st.markdown("---")
        
        st.markdown("""
        ### 📚 Documentation
        
        - [API MOEX Reference](https://iss.moex.com/iss/reference/)
        - [MOEX Official Website](https://www.moex.com/)
        - [Streamlit Documentation](https://docs.streamlit.io/)
        
        ### 🛠️ Technologies utilisées
        
        - **Frontend :** Streamlit
        - **Visualisation :** Plotly
        - **Traitement données :** Pandas, NumPy
        - **ML :** Scikit-learn
        - **API :** Requests
        
        ### 📝 Licence
        
        MIT License - Copyright (c) 2024
        
        ### 📧 Contact
        
        Pour toute question ou suggestion :
        - Email : votre@email.com
        - GitHub : [votre-repo](https://github.com/)
        
        ### 🙏 Remerciements
        
        - MOEX pour l'API publique
        - La communauté Streamlit
        - Tous les contributeurs
        """)
        
        # Statistiques d'utilisation
        st.markdown("---")
        st.markdown("### 📊 Statistiques d'utilisation")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.metric("Alertes actives", len(st.session_state.price_alerts))
        
        with col_s2:
            portfolio_count = sum(len(positions) for positions in st.session_state.portfolio.values()) if hasattr(st.session_state, 'portfolio') else 0
            st.metric("Positions portefeuille", portfolio_count)
        
        with col_s3:
            st.metric("Symboles watchlist", len(st.session_state.watchlist))
