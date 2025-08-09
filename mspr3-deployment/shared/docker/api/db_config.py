# db_config.py - Connexion à la base de données

import psycopg2

def get_connexion():
    """Retourne une connexion à la base"""
    try:
        conn = psycopg2.connect(
            dbname='pandemies_db',
            user='postgres',
            password='loading',
            host='localhost',
            port='5432',
            connect_timeout=5
        )
        return conn
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def test_connexion():
    """Test de connexion"""
    try:
        conn = psycopg2.connect(
            dbname='pandemies_db',
            user='postgres',
            password='loading',
            host='localhost',
            port='5432',
            connect_timeout=5
        )
        print("🎉 CONNEXION REUSSIE !")
        
        # Test des tables
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pays")
        nb_pays = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM maladie")
        nb_maladies = cursor.fetchone()[0]
        
        print(f"📊 Pays en base: {nb_pays}")
        print(f"🦠 Maladies en base: {nb_maladies}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_connexion()