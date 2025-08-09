# app_simple.py - Streamlit simple avec 2 pages

import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Configuration
st.set_page_config(
    page_title="Dashboard Pandémies",
    page_icon="🦠",
    layout="wide"
)

# Configuration API
API_BASE_URL = "http://localhost:8000"

# ==================================================
# FONCTIONS API
# ==================================================

@st.cache_data(ttl=300)
def get_api_data(endpoint):
    """Appelle l'API et retourne les données"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Erreur API: {endpoint}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ API non disponible. Lancez : python3 api_pandemies.py")
        return None
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return None

def test_api():
    """Test connexion API"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================================================
# INTERFACE PRINCIPALE
# ==================================================

def main():
    st.title("🦠 Dashboard Pandémies")
    
    # Test API
    if not test_api():
        st.error("🚨 API non disponible !")
        st.stop()
    
    st.success("✅ API connectée")
    
    # Navigation simple
    page = st.sidebar.selectbox(
        "📊 Choisir une page",
        ["📈 Vue par pays", "⚖️ Comparaison pays"]
    )
    
    # Sélection maladie avec info période
    maladie = st.sidebar.selectbox(
        "🦠 Maladie",
        ["covid_19", "monkeypox"],
        index=0,
        format_func=lambda x: {
            "covid_19": "🦠 COVID-19 (2020-2022)",
            "monkeypox": "🐒 Monkeypox (2022-2023)"
        }[x]
    )
    
    # ==================================================
    # PAGE 1 : VUE PAR PAYS
    # ==================================================
    if page == "📈 Vue par pays":
        st.header(f"📈 Données {maladie.replace('_', '-').upper()}")
        
        # Récupérer les pays pour cette maladie spécifique
        pays_data = get_api_data(f"/pays/{maladie}")
        
        if pays_data and 'pays' in pays_data:
            pays_list = [p['nom_pays'] for p in pays_data['pays']]
            
            # Sélection pays
            pays_choisi = st.selectbox("🌍 Choisir un pays", pays_list)
            
            if pays_choisi:
                # Récupérer évolution (TOUTES les données, pas de limite)
                evolution_data = get_api_data(f"/evolution/{maladie}/{pays_choisi}?limit=5000")
                
                if evolution_data and 'donnees' in evolution_data:
                    df = pd.DataFrame(evolution_data['donnees'])
                    df['date_stat'] = pd.to_datetime(df['date_stat'])
                    df = df.sort_values('date_stat')
                    
                    if not df.empty:
                        # Chiffres clés
                        col1, col2, col3, col4 = st.columns(4)
                        
                        max_cas = df['cas_totaux'].max()
                        max_deces = df['deces_totaux'].max()
                        derniere_date = df['date_stat'].max().strftime('%Y-%m-%d')
                        derniers_nouveaux = df['nouveaux_cas'].iloc[-1] if not df['nouveaux_cas'].isna().all() else 0
                        
                        with col1:
                            st.metric("🔴 Cas totaux", f"{max_cas:,.0f}" if pd.notna(max_cas) else "N/A")
                        with col2:
                            st.metric("⚫ Décès totaux", f"{max_deces:,.0f}" if pd.notna(max_deces) else "N/A")
                        with col3:
                            st.metric("📅 Dernière donnée", derniere_date)
                        with col4:
                            st.metric("📊 Derniers nouveaux cas", f"{derniers_nouveaux:,.0f}" if pd.notna(derniers_nouveaux) else "N/A")
                        
                        # Graphique principal
                        st.subheader(f"📈 Évolution des cas - {pays_choisi}")
                        
                        fig = px.line(
                            df,
                            x='date_stat',
                            y='cas_totaux',
                            title=f"Cas totaux cumulés - {pays_choisi} ({maladie.upper()})",
                            color_discrete_sequence=['#ff6b6b']
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Graphique nouveaux cas
                        st.subheader(f"📊 Nouveaux cas quotidiens")
                        
                        fig2 = px.bar(
                            df.tail(30),  # Dernier mois seulement
                            x='date_stat',
                            y='nouveaux_cas',
                            title=f"Nouveaux cas quotidiens (30 derniers jours) - {pays_choisi}",
                            color_discrete_sequence=['#4ecdc4']
                        )
                        fig2.update_layout(height=400)
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
    elif page == "⚖️ Comparaison pays":
        st.header(f"⚖️ Comparaison {maladie.replace('_', '-').upper()}")
        
        # Récupérer les pays pour cette maladie spécifique
        pays_data = get_api_data(f"/pays/{maladie}")
        
        if pays_data and 'pays' in pays_data:
            pays_list = [p['nom_pays'] for p in pays_data['pays']]
            
            # Sélection 2 pays
            col1, col2 = st.columns(2)
            
            with col1:
                pays1 = st.selectbox("🌍 Premier pays", pays_list, key="pays1")
            with col2:
                pays2 = st.selectbox("🌍 Deuxième pays", pays_list, index=1 if len(pays_list) > 1 else 0, key="pays2")
            
            if pays1 and pays2 and pays1 != pays2:
                # Récupérer données des 2 pays (TOUTES les données)
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
                    
                    # Combiner les données
                    df_combined = pd.concat([df1, df2])
                    
                    if not df_combined.empty:
                        # Métriques comparatives
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader(f"📊 {pays1}")
                            max_cas1 = df1['cas_totaux'].max()
                            max_deces1 = df1['deces_totaux'].max()
                            st.metric("Cas max", f"{max_cas1:,.0f}" if pd.notna(max_cas1) else "N/A")
                            st.metric("Décès max", f"{max_deces1:,.0f}" if pd.notna(max_deces1) else "N/A")
                        
                        with col2:
                            st.subheader(f"📊 {pays2}")
                            max_cas2 = df2['cas_totaux'].max()
                            max_deces2 = df2['deces_totaux'].max()
                            st.metric("Cas max", f"{max_cas2:,.0f}" if pd.notna(max_cas2) else "N/A")
                            st.metric("Décès max", f"{max_deces2:,.0f}" if pd.notna(max_deces2) else "N/A")
                        
                        # Sélection du type de graphique
                        graphique_type = st.selectbox(
                            "📈 Type de données à comparer",
                            ["cas_totaux", "nouveaux_cas", "deces_totaux", "nouveaux_deces"],
                            format_func=lambda x: {
                                "cas_totaux": "🔴 Cas totaux",
                                "nouveaux_cas": "📊 Nouveaux cas",
                                "deces_totaux": "⚫ Décès totaux",
                                "nouveaux_deces": "💀 Nouveaux décès"
                            }[x]
                        )
                        
                        # Graphique de comparaison
                        st.subheader(f"📈 Comparaison {graphique_type.replace('_', ' ')}")
                        
                        fig_comparison = px.line(
                            df_combined,
                            x='date_stat',
                            y=graphique_type,
                            color='pays',
                            title=f"Comparaison {graphique_type.replace('_', ' ')} - {pays1} vs {pays2}",
                            color_discrete_map={pays1: '#ff6b6b', pays2: '#4ecdc4'}
                        )
                        fig_comparison.update_layout(height=500)
                        st.plotly_chart(fig_comparison, use_container_width=True)
                        
                        # Graphique en barres (derniers 30 jours)
                        if graphique_type in ['nouveaux_cas', 'nouveaux_deces']:
                            st.subheader(f"📊 Derniers 30 jours - {graphique_type.replace('_', ' ')}")
                            
                            df_recent = df_combined[df_combined['date_stat'] >= df_combined['date_stat'].max() - pd.Timedelta(days=30)]
                            
                            fig_bars = px.bar(
                                df_recent,
                                x='date_stat',
                                y=graphique_type,
                                color='pays',
                                title=f"{graphique_type.replace('_', ' ').title()} - 30 derniers jours",
                                barmode='group',
                                color_discrete_map={pays1: '#ff6b6b', pays2: '#4ecdc4'}
                            )
                            fig_bars.update_layout(height=400)
                            st.plotly_chart(fig_bars, use_container_width=True)
                        
                    else:
                        st.warning("⚠️ Aucune donnée pour la comparaison")
                else:
                    st.error("❌ Erreur récupération données")
            else:
                st.info("👆 Sélectionnez deux pays différents pour comparer")
        else:
            st.error("❌ Impossible de récupérer les pays")

if __name__ == "__main__":
    main()