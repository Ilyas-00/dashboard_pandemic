import psycopg2
import os

def get_connexion():
    """Connexion à PostgreSQL avec variables d'environnement Docker"""
    try:
        # Utiliser les variables d'environnement Docker
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'pandemies_db')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'loading')
        
        print(f"🔌 Tentative connexion: {host}:{port}/{database}")
        
        connexion = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            connect_timeout=10
        )
        print("✅ Connexion OK")
        return connexion
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def test_connexion():
    """Test de connexion"""
    try:
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'pandemies_db')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'loading')
        
        print(f"🔌 Test connexion: {host}:{port}/{database}")
        
        connexion = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            connect_timeout=10
        )
        print("🎉 CONNEXION REUSSIE !")
        
        # Test des tables
        cursor = connexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM pays")
        nb_pays = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM maladie")
        nb_maladies = cursor.fetchone()[0]
        print(f"📊 Pays en base: {nb_pays}")
        print(f"🦠 Maladies en base: {nb_maladies}")
        connexion.close()
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_connexion()
