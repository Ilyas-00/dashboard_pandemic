# app.py - Streamlit avec authentification intégrée

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

# Import de l'authentification
from streamlit_auth import require_auth_streamlit, admin_panel, get_current_language

# Configuration pays et langues
COUNTRY = os.getenv('COUNTRY', 'FRANCE')
LANGUAGES = os.getenv('LANGUAGES', 'fr')
RGPD_MODE = os.getenv('RGPD_MODE', 'false')
MOBILE_OPTIMIZED = os.getenv('MOBILE_OPTIMIZED', 'false')
INCLUDE_DATAVIZ = os.getenv('INCLUDE_DATAVIZ', 'true')

# Configuration
st.set_page_config(
    page_title="Dashboard Pandémies",
    page_icon="🦠",
    layout="wide"
)

# Configuration API
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# ==================================================
# VÉRIFICATION AUTHENTIFICATION
# ==================================================

# ⚠️ IMPORTANT : Vérifier l'auth AVANT tout le reste
current_user = require_auth_streamlit()

# ==================================================
# TRADUCTIONS
# ==================================================

translations = {
    'fr': {
        'title': '🦠 Dashboard Pandémies',
        'api_url': '🔗 URL API',
        'api_unavailable': '🚨 API non disponible !',
        'api_connected': '✅ API connectée',
        'choose_page': '📊 Choisir une page',
        'view_by_country': '📈 Vue par pays',
        'country_comparison': '⚖️ Comparaison pays',
        'admin_panel': '👑 Administration',
        'disease': '🦠 Maladie',
        'data': 'Données',
        'choose_country': '🌍 Choisir un pays',
        'total_cases': '🔴 Cas totaux',
        'total_deaths': '⚫ Décès totaux',
        'last_data': '📅 Dernière donnée',
        'new_cases': '📊 Derniers nouveaux cas',
        'evolution': 'Évolution des cas',
        'cumulative_cases': 'Cas totaux cumulés',
        'daily_new_cases': 'Nouveaux cas quotidiens',
        'last_30_days': '30 derniers jours',
        'comparison': 'Comparaison',
        'first_country': '🌍 Premier pays',
        'second_country': '🌍 Deuxième pays',
        'max_cases': 'Cas max',
        'max_deaths': 'Décès max',
        'data_type': '📈 Type de données à comparer',
        'select_different': '👆 Sélectionnez deux pays différents pour comparer',
        'language': '🌐 Langue',
        'rgpd_notice': '🔒 Conformité RGPD : Nous respectons votre vie privée.',
        'accept_cookies': 'Accepter les cookies'
    },
    'en': {
        'title': '🦠 Pandemic Dashboard',
        'api_url': '🔗 API URL',
        'api_unavailable': '🚨 API unavailable!',
        'api_connected': '✅ API connected',
        'choose_page': '📊 Choose page',
        'view_by_country': '📈 View by country',
        'country_comparison': '⚖️ Country comparison',
        'admin_panel': '👑 Administration',
        'disease': '🦠 Disease',
        'data': 'Data',
        'choose_country': '🌍 Choose country',
        'total_cases': '🔴 Total cases',
        'total_deaths': '⚫ Total deaths',
        'last_data': '📅 Last data',
        'new_cases': '📊 Recent new cases',
        'evolution': 'Case evolution',
        'cumulative_cases': 'Cumulative total cases',
        'daily_new_cases': 'Daily new cases',
        'last_30_days': 'Last 30 days',
        'comparison': 'Comparison',
        'first_country': '🌍 First country',
        'second_country': '🌍 Second country',
        'max_cases': 'Max cases',
        'max_deaths': 'Max deaths',
        'data_type': '📈 Data type to compare',
        'select_different': '👆 Select two different countries to compare',
        'language': '🌐 Language',
        'rgpd_notice': '🔒 GDPR Compliance: We respect your privacy.',
        'accept_cookies': 'Accept cookies'
    },
    'de': {
        'title': '🦠 Pandemie Dashboard',
        'api_url': '🔗 API URL',
        'api_unavailable': '🚨 API nicht verfügbar!',
        'api_connected': '✅ API verbunden',
        'choose_page': '📊 Seite wählen',
        'view_by_country': '📈 Ansicht nach Land',
        'country_comparison': '⚖️ Länder vergleichen',
        'admin_panel': '👑 Administration',
        'disease': '🦠 Krankheit',
        'data': 'Daten',
        'choose_country': '🌍 Land wählen',
        'total_cases': '🔴 Gesamtfälle',
        'total_deaths': '⚫ Gesamttodesfälle',
        'last_data': '📅 Letzte Daten',
        'new_cases': '📊 Neue Fälle',
        'evolution': 'Fallentwicklung',
        'cumulative_cases': 'Kumulative Gesamtfälle',
        'daily_new_cases': 'Tägliche neue Fälle',
        'last_30_days': 'Letzte 30 Tage',
        'comparison': 'Vergleich',
        'first_country': '🌍 Erstes Land',
        'second_country': '🌍 Zweites Land',
        'max_cases': 'Max Fälle',
        'max_deaths': 'Max Todesfälle',
        'data_type': '📈 Zu vergleichende Daten',
        'select_different': '👆 Wählen Sie zwei verschiedene Länder zum Vergleich',
        'language': '🌐 Sprache',
        'rgpd_notice': '🔒 DSGVO-Konformität: Wir respektieren Ihre Privatsphäre.',
        'accept_cookies': 'Cookies akzeptieren'
    },
    'it': {
        'title': '🦠 Dashboard Pandemie',
        'api_url': '🔗 URL API',
        'api_unavailable': '🚨 API non disponibile!',
        'api_connected': '✅ API connessa',
        'choose_page': '📊 Scegli pagina',
        'view_by_country': '📈 Vista per paese',
        'country_comparison': '⚖️ Confronto paesi',
        'admin_panel': '👑 Amministrazione',
        'disease': '🦠 Malattia',
        'data': 'Dati',
        'choose_country': '🌍 Scegli paese',
        'total_cases': '🔴 Casi totali',
        'total_deaths': '⚫ Decessi totali',
        'last_data': '📅 Ultimi dati',
        'new_cases': '📊 Nuovi casi recenti',
        'evolution': 'Evoluzione casi',
        'cumulative_cases': 'Casi totali cumulativi',
        'daily_new_cases': 'Nuovi casi giornalieri',
        'last_30_days': 'Ultimi 30 giorni',
        'comparison': 'Confronto',
        'first_country': '🌍 Primo paese',
        'second_country': '🌍 Secondo paese',
        'max_cases': 'Casi max',
        'max_deaths': 'Decessi max',
        'data_type': '📈 Tipo di dati da confrontare',
        'select_different': '👆 Seleziona due paesi diversi per confrontare',
        'language': '🌐 Lingua',
        'rgpd_notice': '🔒 Conformità GDPR: Rispettiamo la tua privacy.',
        'accept_cookies': 'Accetta cookies'
    }
}

# ==================================================
# FONCTIONS UTILITAIRES
# ==================================================

def get_translation(key, lang='fr'):
    """Récupère la traduction pour la langue donnée"""
    return translations.get(lang, translations['fr']).get(key, key)

def add_mobile_css():
    """Ajoute du CSS pour l'optimisation mobile (France)"""
    st.markdown("""
    <style>
    /* CSS Mobile pour France */
    @media (max-width: 768px) {
        .stSelectbox > div > div > div {
            font-size: 14px;
        }
        .metric-container {
            padding: 0.5rem;
        }
        .stPlotlyChart {
            height: 300px !important;
        }
        .main > div {
            padding-top: 1rem;
        }
    }
    
    /* Interface compacte pour mobile */
    .stMetric {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# FONCTIONS API (AVEC AUTHENTIFICATION)
# ==================================================

@st.cache_data(ttl=300)
def get_api_data(endpoint):
    """Appelle l'API avec authentification"""
    try:
        # Ajouter le token d'auth
        cookies = {'auth_token': st.session_state.get('auth_token', '')}
        
        response = requests.get(f"{API_BASE_URL}{endpoint}", cookies=cookies, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("❌ Session expirée - Veuillez vous reconnecter")
            st.stop()
        else:
            st.error(f"❌ Erreur API: {endpoint}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ API non disponible à {API_BASE_URL}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return None

def test_api():
    """Test connexion API avec auth"""
    try:
        cookies = {'auth_token': st.session_state.get('auth_token', '')}
        response = requests.get(f"{API_BASE_URL}/", cookies=cookies, timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================================================
# INTERFACE PRINCIPALE
# ==================================================

def main():
    # Récupérer la langue actuelle
    current_lang = get_current_language()
    
    # Ajouter CSS mobile pour la France
    if COUNTRY == 'FRANCE' and MOBILE_OPTIMIZED == 'true':
        add_mobile_css()
    
    # Titre adapté par langue
    st.title(get_translation('title', current_lang))
    
    # Sélecteur de langue pour la Suisse
    if COUNTRY == 'SUISSE':
        lang_options = {'Français': 'fr', 'Deutsch': 'de', 'Italiano': 'it'}
        selected_lang_name = st.sidebar.selectbox(
            get_translation('language', current_lang),
            list(lang_options.keys()),
            index=list(lang_options.values()).index(current_lang)
        )
        # Mettre à jour seulement si la langue a changé
        if lang_options[selected_lang_name] != current_lang:
            st.session_state.selected_language = lang_options[selected_lang_name]
            st.rerun()
        current_lang = st.session_state.selected_language
    
    # Dialog RGPD simple pour la France (maintenu)
    if COUNTRY == 'FRANCE' and RGPD_MODE == 'true':
        # Initialiser l'état des cookies si pas encore fait
        if 'cookies_consent' not in st.session_state:
            st.session_state.cookies_consent = None
        
        # Si pas encore de consentement, afficher le dialog
        if st.session_state.cookies_consent is None:
            # CSS pour le dialog simple
            st.markdown("""
            <style>
            .cookie-dialog {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                z-index: 9999;
                max-width: 300px;
                border: 2px solid #ddd;
            }
            .cookie-title {
                font-weight: bold;
                margin-bottom: 0.5rem;
                color: #333;
            }
            .cookie-text {
                margin-bottom: 1rem;
                color: #666;
                font-size: 14px;
            }
            .cookie-buttons {
                display: flex;
                gap: 10px;
            }
            .stButton > button {
                width: 100%;
                border-radius: 5px;
                border: none;
                padding: 0.5rem;
                font-size: 14px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # HTML du dialog
            st.markdown("""
            <div class="cookie-dialog">
                <div class="cookie-title">🍪 Cookies</div>
                <div class="cookie-text">Ce site utilise des cookies. Acceptez-vous ?</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Boutons positionnés dans le dialog
            st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)
            
            # Boutons dans la zone du dialog
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("✅ OK", key="accept_cookies"):
                    st.session_state.cookies_consent = "accepted"
                    st.rerun()
            with col3:
                if st.button("❌", key="refuse_cookies"):
                    st.session_state.cookies_consent = "refused"
                    st.rerun()
            
            # Arrêter l'exécution du reste de l'app
            st.stop()
        
        # Si consentement donné, afficher le statut
        elif st.session_state.cookies_consent == "accepted":
            st.success("✅ Cookies acceptés - Merci ! Expérience complète activée.")
        elif st.session_state.cookies_consent == "refused":
            st.warning("❌ Cookies refusés - Fonctionnalités limitées.")
            
        # Bouton pour changer d'avis (petit lien en bas)
        if st.button("🔄 Modifier mes préférences cookies", key="change_consent"):
            st.session_state.cookies_consent = None
            st.rerun()
    
    # Debug info
    st.info(f"{get_translation('api_url', current_lang)}: {API_BASE_URL}")
    
    # Test API
    if not test_api():
        st.error(get_translation('api_unavailable', current_lang))
        st.stop()
    
    st.success(get_translation('api_connected', current_lang))
    
    # Navigation avec ajout du panneau admin
    pages = ["view_by_country", "country_comparison"]
    
    # Ajouter l'admin panel si l'utilisateur est admin
    if current_user['role'].startswith('admin_'):
        pages.append("admin_panel")
    
    page = st.sidebar.selectbox(
        get_translation('choose_page', current_lang),
        pages,
        format_func=lambda x: get_translation(x, current_lang)
    )
    
    # Sélection maladie
    maladie = st.sidebar.selectbox(
        get_translation('disease', current_lang),
        ["covid_19", "monkeypox"],
        index=0,
        format_func=lambda x: {
            "covid_19": "🦠 COVID-19 (2020-2022)",
            "monkeypox": "🐒 Monkeypox (2022-2023)"
        }[x]
    )
    
    # ==================================================
    # PAGE ADMIN
    # ==================================================
    if page == "admin_panel":
        admin_panel()
        return
    
    # ==================================================
    # PAGE 1 : VUE PAR PAYS
    # ==================================================
    if page == "view_by_country":
        st.header(f"📈 {get_translation('data', current_lang)} {maladie.replace('_', '-').upper()}")
        
        # Récupérer les pays
        pays_data = get_api_data(f"/pays/{maladie}")
        
        if pays_data and 'pays' in pays_data:
            pays_list = [p['nom_pays'] for p in pays_data['pays']]
            
            # Sélection pays
            pays_choisi = st.selectbox(get_translation('choose_country', current_lang), pays_list)
            
            if pays_choisi:
                # Récupérer évolution
                evolution_data = get_api_data(f"/evolution/{maladie}/{pays_choisi}?limit=5000")
                
                if evolution_data and 'donnees' in evolution_data:
                    df = pd.DataFrame(evolution_data['donnees'])
                    df['date_stat'] = pd.to_datetime(df['date_stat'])
                    df = df.sort_values('date_stat')
                    
                    if not df.empty:
                        # Métriques - adaptation mobile pour France
                        if COUNTRY == 'FRANCE' and MOBILE_OPTIMIZED == 'true':
                            # Version mobile compacte
                            col1, col2 = st.columns(2)
                        else:
                            # Version desktop normale
                            col1, col2, col3, col4 = st.columns(4)
                        
                        max_cas = df['cas_totaux'].max()
                        max_deces = df['deces_totaux'].max()
                        derniere_date = df['date_stat'].max().strftime('%Y-%m-%d')
                        derniers_nouveaux = df['nouveaux_cas'].iloc[-1] if not df['nouveaux_cas'].isna().all() else 0
                        
                        with col1:
                            st.metric(get_translation('total_cases', current_lang), 
                                    f"{max_cas:,.0f}" if pd.notna(max_cas) else "N/A")
                        with col2:
                            st.metric(get_translation('total_deaths', current_lang), 
                                    f"{max_deces:,.0f}" if pd.notna(max_deces) else "N/A")
                        
                        # Pour mobile, afficher les autres métriques en dessous
                        if COUNTRY == 'FRANCE' and MOBILE_OPTIMIZED == 'true':
                            col3, col4 = st.columns(2)
                        
                        if COUNTRY != 'FRANCE' or MOBILE_OPTIMIZED != 'true':
                            with col3:
                                st.metric(get_translation('last_data', current_lang), derniere_date)
                            with col4:
                                st.metric(get_translation('new_cases', current_lang), 
                                        f"{derniers_nouveaux:,.0f}" if pd.notna(derniers_nouveaux) else "N/A")
                        else:
                            with col3:
                                st.metric(get_translation('last_data', current_lang), derniere_date)
                            with col4:
                                st.metric(get_translation('new_cases', current_lang), 
                                        f"{derniers_nouveaux:,.0f}" if pd.notna(derniers_nouveaux) else "N/A")
                        
                        # Graphiques adaptés selon le pays
                        if COUNTRY == 'SUISSE' and INCLUDE_DATAVIZ == 'false':
                            # Graphiques simples pour la Suisse
                            st.subheader(f"📊 {get_translation('evolution', current_lang)} - {pays_choisi}")
                            
                            # Graphique simple en ligne
                            fig_simple = px.line(
                                df.tail(100),  # Seulement 100 derniers points
                                x='date_stat',
                                y='cas_totaux',
                                title=f"{get_translation('cumulative_cases', current_lang)} - {pays_choisi}",
                                color_discrete_sequence=['#2E86AB']
                            )
                            fig_simple.update_layout(height=350)
                            st.plotly_chart(fig_simple, use_container_width=True)
                            
                        else:
                            # Graphiques complets pour USA et France
                            st.subheader(f"📈 {get_translation('evolution', current_lang)} - {pays_choisi}")
                            
                            fig = px.line(
                                df,
                                x='date_stat',
                                y='cas_totaux',
                                title=f"{get_translation('cumulative_cases', current_lang)} - {pays_choisi} ({maladie.upper()})",
                                color_discrete_sequence=['#ff6b6b']
                            )
                            # Hauteur adaptée pour mobile
                            height = 350 if MOBILE_OPTIMIZED == 'true' else 500
                            fig.update_layout(height=height)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Graphique nouveaux cas
                            st.subheader(f"📊 {get_translation('daily_new_cases', current_lang)}")
                            
                            fig2 = px.bar(
                                df.tail(30),
                                x='date_stat',
                                y='nouveaux_cas',
                                title=f"{get_translation('daily_new_cases', current_lang)} ({get_translation('last_30_days', current_lang)}) - {pays_choisi}",
                                color_discrete_sequence=['#4ecdc4']
                            )
                            height2 = 300 if MOBILE_OPTIMIZED == 'true' else 400
                            fig2.update_layout(height=height2)
                            st.plotly_chart(fig2, use_container_width=True)
                        
                    else:
                        st.warning(f"⚠️ Aucune donnée pour {pays_choisi}")
                else:
                    st.error(f"❌ Erreur données pour {pays_choisi}")
        else:
            st.error("❌ Impossible de récupérer les pays")
    
    # ==================================================
    # PAGE 2 : COMPARAISON PAYS
    # ==================================================
    elif page == "country_comparison":
        st.header(f"⚖️ {get_translation('comparison', current_lang)} {maladie.replace('_', '-').upper()}")
        
        # Récupérer les pays
        pays_data = get_api_data(f"/pays/{maladie}")
        
        if pays_data and 'pays' in pays_data:
            pays_list = [p['nom_pays'] for p in pays_data['pays']]
            
            # Sélection 2 pays - adapté mobile
            if MOBILE_OPTIMIZED == 'true':
                pays1 = st.selectbox(get_translation('first_country', current_lang), pays_list, key="pays1")
                pays2 = st.selectbox(get_translation('second_country', current_lang), pays_list, 
                                   index=1 if len(pays_list) > 1 else 0, key="pays2")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    pays1 = st.selectbox(get_translation('first_country', current_lang), pays_list, key="pays1")
                with col2:
                    pays2 = st.selectbox(get_translation('second_country', current_lang), pays_list, 
                                       index=1 if len(pays_list) > 1 else 0, key="pays2")
            
            if pays1 and pays2 and pays1 != pays2:
                # Récupérer données des 2 pays
                evolution1 = get_api_data(f"/evolution/{maladie}/{pays1}?limit=5000")
                evolution2 = get_api_data(f"/evolution/{maladie}/{pays2}?limit=5000")
                
                if evolution1 and evolution2 and 'donnees' in evolution1 and 'donnees' in evolution2:
                    # Préparer les dataframes
                    df1 = pd.DataFrame(evolution1['donnees'])
                    df1['date_stat'] = pd.to_datetime(df1['date_stat'])
                    df1['pays'] = pays1
                    df1 = df1.sort_values('date_stat')
                    
                    df2 = pd.DataFrame(evolution2['donnees'])
                    df2['date_stat'] = pd.to_datetime(df2['date_stat'])
                    df2['pays'] = pays2
                    df2 = df2.sort_values('date_stat')
                    
                    if not df1.empty and not df2.empty:
                        # Métriques comparatives
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader(f"📊 {pays1}")
                            max_cas1 = df1['cas_totaux'].max()
                            max_deces1 = df1['deces_totaux'].max()
                            st.metric(get_translation('max_cases', current_lang), 
                                    f"{max_cas1:,.0f}" if pd.notna(max_cas1) else "N/A")
                            st.metric(get_translation('max_deaths', current_lang), 
                                    f"{max_deces1:,.0f}" if pd.notna(max_deces1) else "N/A")
                        
                        with col2:
                            st.subheader(f"📊 {pays2}")
                            max_cas2 = df2['cas_totaux'].max()
                            max_deces2 = df2['deces_totaux'].max()
                            st.metric(get_translation('max_cases', current_lang), 
                                    f"{max_cas2:,.0f}" if pd.notna(max_cas2) else "N/A")
                            st.metric(get_translation('max_deaths', current_lang), 
                                    f"{max_deces2:,.0f}" if pd.notna(max_deces2) else "N/A")
                        
                        # Graphique de comparaison pour la Suisse (version simplifiée)
                        if COUNTRY == 'SUISSE':
                            # Version simplifiée pour la Suisse - seulement 2 options
                            graphique_type = st.selectbox(
                                get_translation('data_type', current_lang),
                                ["cas_totaux", "deces_totaux"],  # Seulement 2 options pour la Suisse
                                format_func=lambda x: {
                                    "cas_totaux": "🔴 Cas totaux",
                                    "deces_totaux": "⚫ Décès totaux"
                                }[x]
                            )
                            
                            # Données limitées pour la Suisse (100 derniers points)
                            df_combined = pd.concat([df1.tail(100), df2.tail(100)])
                            
                            st.subheader(f"📈 {get_translation('comparison', current_lang)} {graphique_type.replace('_', ' ')}")
                            
                            fig_simple_comp = px.line(
                                df_combined,
                                x='date_stat',
                                y=graphique_type,
                                color='pays',
                                title=f"{get_translation('comparison', current_lang)} {graphique_type.replace('_', ' ')} - {pays1} vs {pays2}",
                                color_discrete_map={pays1: '#ff6b6b', pays2: '#4ecdc4'}
                            )
                            fig_simple_comp.update_layout(height=350)
                            st.plotly_chart(fig_simple_comp, use_container_width=True)
                        else:
                            # Graphiques complets pour USA et France
                            df_combined = pd.concat([df1, df2])
                            
                            # Sélection du type de graphique
                            graphique_type = st.selectbox(
                                get_translation('data_type', current_lang),
                                ["cas_totaux", "nouveaux_cas", "deces_totaux", "nouveaux_deces"],
                                format_func=lambda x: {
                                    "cas_totaux": "🔴 Cas totaux",
                                    "nouveaux_cas": "📊 Nouveaux cas",
                                    "deces_totaux": "⚫ Décès totaux",
                                    "nouveaux_deces": "💀 Nouveaux décès"
                                }[x]
                            )
                            
                            # Graphique de comparaison
                            st.subheader(f"📈 {get_translation('comparison', current_lang)} {graphique_type.replace('_', ' ')}")
                            
                            fig_comparison = px.line(
                                df_combined,
                                x='date_stat',
                                y=graphique_type,
                                color='pays',
                                title=f"{get_translation('comparison', current_lang)} {graphique_type.replace('_', ' ')} - {pays1} vs {pays2}",
                                color_discrete_map={pays1: '#ff6b6b', pays2: '#4ecdc4'}
                            )
                            height = 350 if MOBILE_OPTIMIZED == 'true' else 500
                            fig_comparison.update_layout(height=height)
                            st.plotly_chart(fig_comparison, use_container_width=True)
                        
                    else:
                        st.warning("⚠️ Aucune donnée pour la comparaison")
                else:
                    st.error("❌ Erreur récupération données")
            else:
                st.info(get_translation('select_different', current_lang))
        else:
            st.error("❌ Impossible de récupérer les pays")

if __name__ == "__main__":
    main()