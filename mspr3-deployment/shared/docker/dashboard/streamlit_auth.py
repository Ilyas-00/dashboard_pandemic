# streamlit_auth.py - Authentification pour Streamlit

import streamlit as st
import requests
import os
from typing import Optional, Dict, Any

# Configuration API
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
COUNTRY = os.getenv('COUNTRY', 'FRANCE')

def get_translation(key: str, lang: str = 'fr') -> str:
    """Traductions pour l'authentification"""
    translations = {
        'fr': {
            'login_title': '🔐 Connexion',
            'username': 'Nom d\'utilisateur',
            'password': 'Mot de passe', 
            'login_button': 'Se connecter',
            'logout_button': 'Se déconnecter',
            'welcome': 'Bienvenue',
            'invalid_credentials': 'Identifiants invalides',
            'connection_error': 'Erreur de connexion à l\'API',
            'admin_panel': '👑 Administration',
            'user_management': 'Gestion des utilisateurs',
            'create_user': 'Créer un utilisateur',
            'delete_user': 'Supprimer',
            'role': 'Rôle',
            'email': 'Email',
            'full_name': 'Nom complet',
            'active': 'Actif',
            'created_at': 'Créé le',
            'last_login': 'Dernière connexion'
        },
        'en': {
            'login_title': '🔐 Login',
            'username': 'Username',
            'password': 'Password',
            'login_button': 'Login',
            'logout_button': 'Logout', 
            'welcome': 'Welcome',
            'invalid_credentials': 'Invalid credentials',
            'connection_error': 'API connection error',
            'admin_panel': '👑 Administration',
            'user_management': 'User Management',
            'create_user': 'Create User',
            'delete_user': 'Delete',
            'role': 'Role',
            'email': 'Email',
            'full_name': 'Full Name',
            'active': 'Active',
            'created_at': 'Created',
            'last_login': 'Last Login'
        },
        'de': {
            'login_title': '🔐 Anmeldung',
            'username': 'Benutzername',
            'password': 'Passwort',
            'login_button': 'Anmelden',
            'logout_button': 'Abmelden',
            'welcome': 'Willkommen',
            'invalid_credentials': 'Ungültige Anmeldedaten',
            'connection_error': 'API-Verbindungsfehler',
            'admin_panel': '👑 Administration',
            'user_management': 'Benutzerverwaltung',
            'create_user': 'Benutzer erstellen',
            'delete_user': 'Löschen',
            'role': 'Rolle',
            'email': 'E-Mail',
            'full_name': 'Vollständiger Name',
            'active': 'Aktiv',
            'created_at': 'Erstellt',
            'last_login': 'Letzte Anmeldung'
        },
        'it': {
            'login_title': '🔐 Accesso',
            'username': 'Nome utente',
            'password': 'Password',
            'login_button': 'Accedi',
            'logout_button': 'Esci',
            'welcome': 'Benvenuto',
            'invalid_credentials': 'Credenziali non valide',
            'connection_error': 'Errore di connessione API',
            'admin_panel': '👑 Amministrazione',
            'user_management': 'Gestione Utenti',
            'create_user': 'Crea Utente',
            'delete_user': 'Elimina',
            'role': 'Ruolo',
            'email': 'Email',
            'full_name': 'Nome Completo',
            'active': 'Attivo',
            'created_at': 'Creato',
            'last_login': 'Ultimo Accesso'
        }
    }
    return translations.get(lang, translations['fr']).get(key, key)

def get_current_language() -> str:
    """Détermine la langue actuelle selon le pays et les préférences"""
    if COUNTRY == 'USA':
        return 'en'
    elif COUNTRY == 'SUISSE':
        return st.session_state.get('selected_language', 'fr')
    else:  # France
        return 'fr'

def check_auth() -> Optional[Dict[str, Any]]:
    """Vérifie si l'utilisateur est authentifié"""
    if 'auth_token' not in st.session_state:
        return None
    
    try:
        # Vérifier le token auprès de l'API
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            cookies={'auth_token': st.session_state.auth_token},
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()['user']
            return user_data
        else:
            # Token invalide, le supprimer
            del st.session_state.auth_token
            return None
            
    except requests.exceptions.RequestException:
        return None

def login_user(username: str, password: str) -> bool:
    """Connecte un utilisateur"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "username": username,
                "password": password
            },
            timeout=10
        )
        
        if response.status_code == 200:
            # Récupérer le cookie de session
            auth_token = None
            for cookie in response.cookies:
                if cookie.name == 'auth_token':
                    auth_token = cookie.value
                    break
            
            if auth_token:
                st.session_state.auth_token = auth_token
                st.session_state.user_data = response.json()['user']
                return True
        
        return False
        
    except requests.exceptions.RequestException:
        return False

def logout_user():
    """Déconnecte l'utilisateur"""
    try:
        # Informer l'API du logout
        requests.post(
            f"{API_BASE_URL}/auth/logout",
            cookies={'auth_token': st.session_state.get('auth_token', '')},
            timeout=5
        )
    except:
        pass  # Peu importe si ça échoue
    
    # Nettoyer la session Streamlit
    if 'auth_token' in st.session_state:
        del st.session_state.auth_token
    if 'user_data' in st.session_state:
        del st.session_state.user_data

def login_page():
    """Affiche la page de connexion"""
    lang = get_current_language()
    
    st.title(get_translation('login_title', lang))
    
    # Formulaire de connexion
    with st.form("login_form"):
        username = st.text_input(get_translation('username', lang))
        password = st.text_input(get_translation('password', lang), type="password")
        submit_button = st.form_submit_button(get_translation('login_button', lang))
        
        if submit_button:
            if username and password:
                with st.spinner("Connexion en cours..."):
                    if login_user(username, password):
                        st.success(f"{get_translation('welcome', lang)} {username}!")
                        st.rerun()
                    else:
                        st.error(get_translation('invalid_credentials', lang))
            else:
                st.warning("Veuillez remplir tous les champs")

def get_users_list() -> Optional[list]:
    """Récupère la liste des utilisateurs (admin seulement)"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/users",
            cookies={'auth_token': st.session_state.get('auth_token', '')},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['users']
        return None
        
    except requests.exceptions.RequestException:
        return None

def create_new_user(username: str, password: str, role: str, email: str = "", full_name: str = "") -> bool:
    """Crée un nouvel utilisateur"""
    try:
        data = {
            "username": username,
            "password": password,
            "role": role
        }
        if email:
            data["email"] = email
        if full_name:
            data["full_name"] = full_name
            
        response = requests.post(
            f"{API_BASE_URL}/auth/users",
            json=data,
            cookies={'auth_token': st.session_state.get('auth_token', '')},
            timeout=10
        )
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException:
        return False

def delete_user_by_id(user_id: int) -> bool:
    """Supprime un utilisateur"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/auth/users/{user_id}",
            cookies={'auth_token': st.session_state.get('auth_token', '')},
            timeout=10
        )
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException:
        return False

def admin_panel():
    """Panneau d'administration pour les admins"""
    lang = get_current_language()
    
    st.header(get_translation('admin_panel', lang))
    
    # Gestion des utilisateurs
    st.subheader(get_translation('user_management', lang))
    
    # Liste des utilisateurs
    users = get_users_list()
    if users:
        st.write(f"**{len(users)} utilisateurs dans {COUNTRY}:**")
        
        for user in users:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                status = "✅" if user['is_active'] else "❌"
                st.write(f"{status} **{user['username']}** ({user['full_name'] or 'N/A'})")
            
            with col2:
                st.write(f"🎭 {user['role']}")
            
            with col3:
                last_login = user['last_login'] 
                if last_login:
                    st.write(f"🕐 {last_login[:10]}")
                else:
                    st.write("🕐 Jamais")
            
            with col4:
                # Ne pas permettre la suppression des admins
                if not user['role'].startswith('admin_'):
                    if st.button(get_translation('delete_user', lang), key=f"del_{user['id_user']}"):
                        if delete_user_by_id(user['id_user']):
                            st.success("Utilisateur supprimé")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la suppression")
    
    st.divider()
    
    # Création d'utilisateur
    st.subheader(get_translation('create_user', lang))
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input(get_translation('username', lang))
            new_password = st.text_input(get_translation('password', lang), type="password")
            new_full_name = st.text_input(get_translation('full_name', lang))
        
        with col2:
            # Rôles disponibles selon le pays
            country_lower = COUNTRY.lower()
            if country_lower == 'suisse':
                country_lower = 'suisse'
            elif country_lower == 'usa':
                country_lower = 'usa'
            else:
                country_lower = 'france'
            
            role_options = [f'chercheur_{country_lower}', f'admin_{country_lower}']
            new_role = st.selectbox(get_translation('role', lang), role_options)
            new_email = st.text_input(get_translation('email', lang))
        
        submit_create = st.form_submit_button(get_translation('create_user', lang))
        
        if submit_create:
            if new_username and new_password:
                if create_new_user(new_username, new_password, new_role, new_email, new_full_name):
                    st.success(f"Utilisateur {new_username} créé avec succès!")
                    st.rerun()
                else:
                    st.error("Erreur lors de la création de l'utilisateur")
            else:
                st.warning("Nom d'utilisateur et mot de passe requis")

def require_auth_streamlit():
    """Middleware Streamlit - redirige vers login si pas authentifié"""
    user = check_auth()
    
    if not user:
        login_page()
        st.stop()
    
    # Afficher info utilisateur connecté
    col1, col2, col3 = st.sidebar.columns([2, 1, 1])
    
    with col1:
        st.sidebar.write(f"👤 **{user['username']}**")
        st.sidebar.write(f"🌍 {user['country']}")
        
    with col2:
        if user['role'].startswith('admin_'):
            st.sidebar.write("👑")
    
    with col3:
        lang = get_current_language()
        if st.sidebar.button(get_translation('logout_button', lang)):
            logout_user()
            st.rerun()
    
    return user