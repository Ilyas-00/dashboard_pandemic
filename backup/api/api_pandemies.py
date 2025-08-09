# api_pandemies.py - API FastAPI simple et clean

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional
from datetime import date
import uvicorn

# Configuration
app = FastAPI(
    title="API Pandémies",
    description="API pour visualiser les données COVID-19 et Monkeypox",
    version="1.0.0"
)

# CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration base de données
def get_db_connection():
    """Connexion à la base PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname='pandemies_db',
            user='postgres',
            password='loading',
            host='localhost',
            port='5432',
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données: {e}")

# ==================================================
# ENDPOINTS PRINCIPAUX
# ==================================================

@app.get("/")
def root():
    """Page d'accueil de l'API"""
    return {
        "message": "API Pandémies",
        "endpoints": {
            "statistiques": "/stats",
            "pays": "/pays",
            "evolution": "/evolution/{maladie}/{pays}",
            "top_pays": "/top/{maladie}",
            "donnees_recentes": "/recent/{maladie}"
        }
    }

@app.get("/stats")
def get_statistiques_generales():
    """Statistiques générales de la base"""
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
def get_pays_par_maladie(maladie: str):
    """Liste des pays qui ont des données pour une maladie spécifique"""
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
def get_evolution_pays(maladie: str, pays: str, limit: int = 100):
    """Évolution temporelle pour un pays et une maladie"""
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
def get_top_pays(maladie: str, limit: int = 10):
    """Top des pays les plus touchés par une maladie"""
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
def get_donnees_recentes(maladie: str, jours: int = 30):
    """Données récentes pour une maladie (derniers X jours)"""
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

@app.get("/continents/{maladie}")
def get_stats_par_continent(maladie: str):
    """Statistiques agrégées par continent"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                p.continent,
                COUNT(DISTINCT p.nom_pays) as nb_pays,
                SUM(p.population) as population_totale,
                MAX(s.cas_totaux) as max_cas_pays,
                SUM(CASE WHEN s.date_stat = (
                    SELECT MAX(s2.date_stat) 
                    FROM statistique s2 
                    WHERE s2.id_pays = s.id_pays 
                    AND s2.id_maladie = s.id_maladie
                ) THEN s.cas_totaux ELSE 0 END) as cas_totaux_continent
            FROM statistique s
            JOIN pays p ON s.id_pays = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s 
            AND p.continent IS NOT NULL
            GROUP BY p.continent
            ORDER BY cas_totaux_continent DESC
        """, (maladie,))
        
        stats_continents = cursor.fetchall()
        
        return {
            "maladie": maladie,
            "continents": [dict(row) for row in stats_continents]
        }
        
    finally:
        conn.close()

# ==================================================
# LANCEMENT DE L'API
# ==================================================

if __name__ == "__main__":
    print("🚀 Démarrage API Pandémies...")
    print("📊 Endpoints disponibles:")
    print("   - http://localhost:8000 (documentation)")
    print("   - http://localhost:8000/docs (Swagger UI)")
    print("   - http://localhost:8000/stats (statistiques)")
    print("   - http://localhost:8000/evolution/covid_19/france")
    print("   - http://localhost:8000/top/covid_19")
    
    uvicorn.run(
        "api_pandemies:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )