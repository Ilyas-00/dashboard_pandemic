# api_pandemies.py - API FastAPI avec authentification intégrée

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional
from datetime import date
import uvicorn
import os

# Import du système d'authentification
from auth import (
    authenticate_user, create_session, delete_session, get_current_user, 
    require_auth, require_country, get_users_by_country, create_user, 
    delete_user, cleanup_expired_sessions
)

# Configuration
app = FastAPI(
    title="API Pandémies avec Authentification",
    description="API pour visualiser les données COVID-19 et Monkeypox avec système d'auth",
    version="2.0.0"
)

# CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration base de données avec variables d'environnement
def get_db_connection():
    """Connexion à la base PostgreSQL"""
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
# MODÈLES PYDANTIC
# ============================================

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id_user: int
    username: str
    country: str
    role: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool

# ============================================
# ENDPOINTS D'AUTHENTIFICATION
# ============================================

@app.post("/auth/login")
async def login(request: Request, response: Response, login_data: LoginRequest):
    """Connexion utilisateur"""
    country = os.getenv('COUNTRY', 'FRANCE')
    
    # Authentifier l'utilisateur
    user = authenticate_user(login_data.username, login_data.password, country)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials or wrong country"
        )
    
    # Créer une session
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get('User-Agent', '')
    
    session_token = create_session(
        user['id_user'], 
        ip_address=ip_address, 
        user_agent=user_agent
    )
    
    # Définir le cookie
    response.set_cookie(
        key="auth_token",
        value=session_token,
        httponly=True,
        secure=False,  # True en production avec HTTPS
        samesite="lax",
        max_age=24 * 60 * 60  # 24 heures
    )
    
    return {
        "message": "Login successful",
        "user": {
            "username": user['username'],
            "country": user['country'],
            "role": user['role'],
            "full_name": user['full_name']
        }
    }

@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Déconnexion utilisateur"""
    token = request.cookies.get('auth_token')
    if token:
        delete_session(token)
    
    response.delete_cookie("auth_token")
    return {"message": "Logout successful"}

@app.get("/auth/me")
async def get_current_user_info(request: Request, current_user: dict = Depends(require_auth)):
    """Informations utilisateur actuel"""
    # Vérifier le pays
    current_user = require_country(request, current_user)
    
    return {
        "user": {
            "username": current_user['username'],
            "country": current_user['country'],
            "role": current_user['role']
        }
    }

# ============================================
# ENDPOINTS GESTION UTILISATEURS (ADMIN ONLY)
# ============================================

@app.get("/auth/users")
async def get_users(request: Request, current_user: dict = Depends(require_auth)):
    """Liste des utilisateurs (admin seulement)"""
    current_user = require_country(request, current_user)
    
    # Vérifier que c'est un admin
    if not current_user['role'].startswith('admin_'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = get_users_by_country(current_user['country'])
    return {"users": users}

@app.post("/auth/users")
async def create_new_user(
    request: Request, 
    user_data: CreateUserRequest,
    current_user: dict = Depends(require_auth)
):
    """Créer un utilisateur (admin seulement)"""
    current_user = require_country(request, current_user)
    
    # Vérifier que c'est un admin
    if not current_user['role'].startswith('admin_'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Le nouveau user doit être du même pays que l'admin
    country = current_user['country']
    
    # Vérifier que le rôle est valide pour ce pays
    valid_roles = [f'chercheur_{country.lower()}', f'admin_{country.lower()}']
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid role. Valid roles for {country}: {valid_roles}"
        )
    
    try:
        new_user = create_user(
            username=user_data.username,
            password=user_data.password,
            country=country,
            role=user_data.role,
            email=user_data.email,
            full_name=user_data.full_name
        )
        return {"message": "User created successfully", "user": new_user}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")

@app.delete("/auth/users/{user_id}")
async def delete_user_endpoint(
    user_id: int,
    request: Request,
    current_user: dict = Depends(require_auth)
):
    """Supprimer un utilisateur (admin seulement)"""
    current_user = require_country(request, current_user)
    
    # Vérifier que c'est un admin
    if not current_user['role'].startswith('admin_'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        delete_user(user_id, current_user['country'])
        return {"message": "User deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {e}")

# ============================================
# ENDPOINTS PANDÉMIES (PROTÉGÉS)
# ============================================

@app.get("/")
def root():
    """Page d'accueil de l'API"""
    country = os.getenv('COUNTRY', 'FRANCE')
    return {
        "message": f"API Pandémies - {country}",
        "version": "2.0.0 with Authentication",
        "auth_endpoints": {
            "login": "/auth/login",
            "logout": "/auth/logout", 
            "me": "/auth/me",
            "users": "/auth/users (admin)"
        },
        "data_endpoints": {
            "statistiques": "/stats",
            "pays": "/pays/{maladie}",
            "evolution": "/evolution/{maladie}/{pays}",
            "top_pays": "/top/{maladie}",
            "donnees_recentes": "/recent/{maladie}"
        }
    }

@app.get("/stats")
def get_statistiques_generales(request: Request, current_user: dict = Depends(require_auth)):
    """Statistiques générales de la base (protégé)"""
    current_user = require_country(request, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                m.nom_maladie,
                COUNT(*) as nb_records,
                COUNT(DISTINCT s.id_pays) as nb_pays,
                MIN(s.date_stat) as premiere_date,
                MAX(s.date_stat) as derniere_date
            FROM statistique s 
            JOIN maladie m ON s.id_maladie = m.id_maladie 
            GROUP BY m.nom_maladie
        """)
        
        stats = cursor.fetchall()
        return {"statistiques": [dict(row) for row in stats]}
        
    finally:
        conn.close()

@app.get("/pays/{maladie}")
def get_pays_par_maladie(maladie: str, request: Request, current_user: dict = Depends(require_auth)):
    """Liste des pays qui ont des données pour une maladie spécifique (protégé)"""
    current_user = require_country(request, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT p.nom_pays, p.continent, p.population 
            FROM pays p
            JOIN statistique s ON p.id_pays = s.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s
            ORDER BY p.nom_pays
        """, (maladie,))
        
        pays = cursor.fetchall()
        return {"pays": [dict(row) for row in pays]}
        
    finally:
        conn.close()

@app.get("/evolution/{maladie}/{pays}")
def get_evolution_pays(maladie: str, pays: str, request: Request, current_user: dict = Depends(require_auth), limit: int = 100):
    """Évolution temporelle pour un pays et une maladie (protégé)"""
    current_user = require_country(request, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                s.date_stat,
                CASE 
                    WHEN s.cas_totaux IS NULL OR s.cas_totaux = 'NaN' THEN 0 
                    ELSE s.cas_totaux::bigint 
                END as cas_totaux,
                CASE 
                    WHEN s.nouveaux_cas IS NULL OR s.nouveaux_cas = 'NaN' THEN 0 
                    ELSE s.nouveaux_cas::bigint 
                END as nouveaux_cas,
                CASE 
                    WHEN s.deces_totaux IS NULL OR s.deces_totaux = 'NaN' THEN 0 
                    ELSE s.deces_totaux::bigint 
                END as deces_totaux,
                CASE 
                    WHEN s.nouveaux_deces IS NULL OR s.nouveaux_deces = 'NaN' THEN 0 
                    ELSE s.nouveaux_deces::bigint 
                END as nouveaux_deces
            FROM statistique s
            JOIN pays p ON s.id_pays = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s AND p.nom_pays = %s
            ORDER BY s.date_stat DESC
            LIMIT %s
        """, (maladie, pays, limit))
        
        evolution = cursor.fetchall()
        
        if not evolution:
            raise HTTPException(status_code=404, detail=f"Aucune donnée pour {maladie} - {pays}")
        
        return {
            "maladie": maladie,
            "pays": pays,
            "donnees": [dict(row) for row in evolution]
        }
        
    finally:
        conn.close()

@app.get("/top/{maladie}")
def get_top_pays(maladie: str, request: Request, current_user: dict = Depends(require_auth), limit: int = 10):
    """Top des pays les plus touchés par une maladie (protégé)"""
    current_user = require_country(request, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                p.nom_pays,
                p.continent,
                MAX(CASE 
                    WHEN s.cas_totaux IS NULL OR s.cas_totaux = 'NaN' THEN 0 
                    ELSE s.cas_totaux::bigint 
                END) as max_cas,
                MAX(CASE 
                    WHEN s.deces_totaux IS NULL OR s.deces_totaux = 'NaN' THEN 0 
                    ELSE s.deces_totaux::bigint 
                END) as max_deces
            FROM statistique s
            JOIN pays p ON s.id_pays = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s 
            AND s.cas_totaux IS NOT NULL
            GROUP BY p.nom_pays, p.continent
            ORDER BY max_cas DESC
            LIMIT %s
        """, (maladie, limit))
        
        top_pays = cursor.fetchall()
        
        return {
            "maladie": maladie,
            "top_pays": [dict(row) for row in top_pays]
        }
        
    finally:
        conn.close()

@app.get("/recent/{maladie}")
def get_donnees_recentes(maladie: str, request: Request, current_user: dict = Depends(require_auth), jours: int = 30):
    """Données récentes pour une maladie (derniers X jours) (protégé)"""
    current_user = require_country(request, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                s.date_stat,
                p.nom_pays,
                p.continent,
                s.cas_totaux,
                s.nouveaux_cas,
                s.deces_totaux
            FROM statistique s
            JOIN pays p ON s.id_pays = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s 
            AND s.date_stat >= (
                SELECT MAX(date_stat) - INTERVAL '%s days' 
                FROM statistique s2 
                JOIN maladie m2 ON s2.id_maladie = m2.id_maladie 
                WHERE m2.nom_maladie = %s
            )
            ORDER BY s.date_stat DESC, s.cas_totaux DESC
            LIMIT 100
        """, (maladie, jours, maladie))
        
        donnees_recentes = cursor.fetchall()
        
        return {
            "maladie": maladie,
            "periode": f"Derniers {jours} jours",
            "donnees": [dict(row) for row in donnees_recentes]
        }
        
    finally:
        conn.close()

# ============================================
# NETTOYAGE AUTOMATIQUE
# ============================================

@app.get("/auth/cleanup")
async def cleanup_sessions(request: Request, current_user: dict = Depends(require_auth)):
    """Nettoie les sessions expirées (admin seulement)"""
    current_user = require_country(request, current_user)
    
    if not current_user['role'].startswith('admin_'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    deleted_count = cleanup_expired_sessions()
    return {"message": f"Cleaned {deleted_count} expired sessions"}

if __name__ == "__main__":
    print("🚀 Démarrage API Pandémies avec authentification...")
    uvicorn.run("api_pandemies:app", host="0.0.0.0", port=8000, reload=True)