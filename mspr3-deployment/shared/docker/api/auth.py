# auth.py - Système d'authentification pour l'API

from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2.extras
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from functools import wraps
import secrets

# Configuration JWT
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_HOURS = 24

# Configuration base de données (réutilise la logique existante)
def get_db_connection():
    """Connexion à la base PostgreSQL - réutilise la config existante"""
    try:
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'pandemies_db')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'loading')
        
        conn = psycopg2.connect(
            dbname=database,
            user=user,
            password=password,
            host=host,
            port=port,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données: {e}")

# ============================================
# UTILITAIRES JWT
# ============================================

def create_jwt_token(user_data: Dict[str, Any]) -> str:
    """Crée un token JWT"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        'user_id': user_data['id_user'],
        'username': user_data['username'],
        'country': user_data['country'],
        'role': user_data['role'],
        'exp': expire,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Vérifie et décode un token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ============================================
# GESTION DES SESSIONS
# ============================================

def create_session(user_id: int, ip_address: str = None, user_agent: str = None) -> str:
    """Crée une session en base"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Générer un token unique
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
        
        cursor.execute("""
            INSERT INTO sessions (token, user_id, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (token, user_id, expires_at, ip_address, user_agent))
        
        conn.commit()
        return token
        
    finally:
        conn.close()

def verify_session(token: str) -> Optional[Dict[str, Any]]:
    """Vérifie une session en base"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.id_user, u.username, u.country, u.role, u.is_active,
                   s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id_user
            WHERE s.token = %s AND s.expires_at > NOW()
        """, (token,))
        
        result = cursor.fetchone()
        if result and result['is_active']:
            return dict(result)
        return None
        
    finally:
        conn.close()

def delete_session(token: str):
    """Supprime une session (logout)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.commit()
    finally:
        conn.close()

# ============================================
# AUTHENTIFICATION
# ============================================

def authenticate_user(username: str, password: str, country: str) -> Optional[Dict[str, Any]]:
    """Authentifie un utilisateur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id_user, username, password_hash, country, role, 
                   email, full_name, is_active
            FROM users 
            WHERE username = %s AND country = %s AND is_active = TRUE
        """, (username, country))
        
        user = cursor.fetchone()
        if not user:
            return None
        
        # Vérifier le mot de passe
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Mettre à jour last_login
            cursor.execute("""
                UPDATE users SET last_login = NOW() WHERE id_user = %s
            """, (user['id_user'],))
            conn.commit()
            
            return dict(user)
        
        return None
        
    finally:
        conn.close()

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# ============================================
# MIDDLEWARE ET DÉCORATEURS
# ============================================

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Récupère l'utilisateur actuel depuis le token"""
    # Essayer d'abord le cookie
    token = request.cookies.get('auth_token')
    
    # Sinon essayer le header Authorization
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        return None
    
    # Vérifier la session en base
    user_data = verify_session(token)
    return user_data

def require_auth(request: Request) -> Dict[str, Any]:
    """Middleware obligatoire - lève une exception si pas authentifié"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

def require_role(allowed_roles: list):
    """Décorateur pour vérifier le rôle"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Récupérer l'utilisateur depuis les kwargs
            user = kwargs.get('current_user')
            if not user or user['role'] not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Role required: {', '.join(allowed_roles)}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_country(request: Request, current_user: Dict[str, Any]) -> Dict[str, Any]:
    """Vérifie que l'utilisateur appartient au bon pays"""
    api_country = os.getenv('COUNTRY', 'FRANCE')
    
    if current_user['country'] != api_country:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: This is {api_country} instance, you belong to {current_user['country']}"
        )
    
    return current_user

# ============================================
# GESTION DES UTILISATEURS
# ============================================

def get_users_by_country(country: str, role: str = None) -> list:
    """Récupère les utilisateurs d'un pays"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if role:
            cursor.execute("""
                SELECT id_user, username, country, role, email, full_name, 
                       is_active, created_at, last_login
                FROM users 
                WHERE country = %s AND role = %s
                ORDER BY created_at DESC
            """, (country, role))
        else:
            cursor.execute("""
                SELECT id_user, username, country, role, email, full_name, 
                       is_active, created_at, last_login
                FROM users 
                WHERE country = %s
                ORDER BY role, created_at DESC
            """, (country,))
        
        return [dict(row) for row in cursor.fetchall()]
        
    finally:
        conn.close()

def create_user(username: str, password: str, country: str, role: str, 
                email: str = None, full_name: str = None) -> Dict[str, Any]:
    """Crée un nouvel utilisateur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Vérifier si l'username existe déjà
        cursor.execute("SELECT id_user FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash du mot de passe
        password_hash = hash_password(password)
        
        # Insérer l'utilisateur
        cursor.execute("""
            INSERT INTO users (username, password_hash, country, role, email, full_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_user, username, country, role, email, full_name, created_at
        """, (username, password_hash, country, role, email, full_name))
        
        user = cursor.fetchone()
        conn.commit()
        
        return dict(user)
        
    finally:
        conn.close()

def delete_user(user_id: int, admin_country: str) -> bool:
    """Supprime un utilisateur (seulement par admin du même pays)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Vérifier que l'utilisateur appartient au même pays
        cursor.execute("""
            SELECT username, country, role FROM users WHERE id_user = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user['country'] != admin_country:
            raise HTTPException(status_code=403, detail="Can only delete users from your country")
        
        if user['role'].startswith('admin_'):
            raise HTTPException(status_code=403, detail="Cannot delete admin users")
        
        # Supprimer l'utilisateur (cascade supprimera les sessions)
        cursor.execute("DELETE FROM users WHERE id_user = %s", (user_id,))
        conn.commit()
        
        return True
        
    finally:
        conn.close()

# ============================================
# CLEANUP AUTOMATIQUE
# ============================================

def cleanup_expired_sessions():
    """Nettoie les sessions expirées"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT cleanup_expired_sessions()")
        deleted_count = cursor.fetchone()[0]
        conn.commit()
        return deleted_count
    finally:
        conn.close()