-- Script d'initialisation - Tables vides pour l'ETL
-- Exécuté automatiquement au premier démarrage

-- Création des tables (structure seulement)
CREATE TABLE IF NOT EXISTS pays (
    id_pays SERIAL PRIMARY KEY,
    nom_pays VARCHAR(100) NOT NULL UNIQUE,
    continent VARCHAR(50),
    population BIGINT
);

CREATE TABLE IF NOT EXISTS maladie (
    id_maladie SERIAL PRIMARY KEY,
    nom_maladie VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS statistique (
    id_statistique SERIAL PRIMARY KEY,
    date_stat DATE NOT NULL,
    id_pays INTEGER NOT NULL,
    id_maladie INTEGER NOT NULL,
    
    -- Statistiques de base
    cas_totaux NUMERIC DEFAULT 0,
    nouveaux_cas NUMERIC DEFAULT 0,
    deces_totaux NUMERIC DEFAULT 0,
    nouveaux_deces NUMERIC DEFAULT 0,
    cas_actifs NUMERIC DEFAULT 0,
    cas_par_million DECIMAL(10,2) DEFAULT 0,
    
    -- Colonnes spécifiques COVID
    total_gueris NUMERIC DEFAULT 0,
    cas_graves NUMERIC DEFAULT 0,
    
    -- Colonnes spécifiques Monkeypox
    nouveaux_cas_lisses DECIMAL(10,2) DEFAULT 0,
    nouveaux_cas_lisses_par_million DECIMAL(10,2) DEFAULT 0,
    
    -- Contraintes
    FOREIGN KEY (id_pays) REFERENCES pays(id_pays),
    FOREIGN KEY (id_maladie) REFERENCES maladie(id_maladie),
    UNIQUE(date_stat, id_pays, id_maladie)
);

-- Juste insérer les 2 maladies de base
INSERT INTO maladie (nom_maladie) VALUES ('covid_19'), ('monkeypox')
ON CONFLICT (nom_maladie) DO NOTHING;

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_statistique_date ON statistique(date_stat);
CREATE INDEX IF NOT EXISTS idx_statistique_pays ON statistique(id_pays);
CREATE INDEX IF NOT EXISTS idx_statistique_maladie ON statistique(id_maladie);

-- Message de confirmation
SELECT 'Tables créées - Prêt pour ETL containerisé !' as message;


-- ============================================
-- NOUVELLES TABLES (authentification)
-- ============================================

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id_user SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    country VARCHAR(20) NOT NULL CHECK (country IN ('FRANCE', 'SUISSE', 'USA')),
    role VARCHAR(30) NOT NULL,
    email VARCHAR(100),
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Table des sessions
CREATE TABLE IF NOT EXISTS sessions (
    id_session SERIAL PRIMARY KEY,
    token VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id_user) ON DELETE CASCADE
);

-- ============================================
-- DONNÉES DE BASE
-- ============================================

-- Maladies
INSERT INTO maladie (nom_maladie) VALUES ('covid_19'), ('monkeypox') 
ON CONFLICT (nom_maladie) DO NOTHING;

-- Utilisateurs par défaut (mots de passe : admin123, chercheur123)
-- Hash bcrypt pour 'admin123' : $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewGkLz9g8L8xhXpS
-- Hash bcrypt pour 'chercheur123' : $2b$12$EixZt4krO2LA5J7j9kXJ2esWzqT4y5LnXwBYl.5T1c6Rq8J9hK8uO

INSERT INTO users (username, password_hash, country, role, email, full_name) VALUES
-- Admins par pays
('admin_france', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewGkLz9g8L8xhXpS', 'FRANCE', 'admin_france', 'admin@france.gov', 'Administrateur France'),
('admin_suisse', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewGkLz9g8L8xhXpS', 'SUISSE', 'admin_suisse', 'admin@suisse.ch', 'Administrateur Suisse'),
('admin_usa', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewGkLz9g8L8xhXpS', 'USA', 'admin_usa', 'admin@usa.gov', 'Administrator USA'),

-- Chercheurs de démonstration
('chercheur_fr1', '$2b$12$EixZt4krO2LA5J7j9kXJ2esWzqT4y5LnXwBYl.5T1c6Rq8J9hK8uO', 'FRANCE', 'chercheur_france', 'chercheur1@france.fr', 'Dr. Marie Dupont'),
('chercheur_fr2', '$2b$12$EixZt4krO2LA5J7j9kXJ2esWzqT4y5LnXwBYl.5T1c6Rq8J9hK8uO', 'FRANCE', 'chercheur_france', 'chercheur2@france.fr', 'Dr. Pierre Martin'),

('chercheur_ch1', '$2b$12$EixZt4krO2LA5J7j9kXJ2esWzqT4y5LnXwBYl.5T1c6Rq8J9hK8uO', 'SUISSE', 'chercheur_suisse', 'chercheur1@suisse.ch', 'Dr. Hans Mueller'),

('chercheur_us1', '$2b$12$EixZt4krO2LA5J7j9kXJ2esWzqT4y5LnXwBYl.5T1c6Rq8J9hK8uO', 'USA', 'chercheur_usa', 'researcher1@usa.gov', 'Dr. John Smith'),
('chercheur_us2', '$2b$12$EixZt4krO2LA5J7j9kXJ2esWzqT4y5LnXwBYl.5T1c6Rq8J9hK8uO', 'USA', 'chercheur_usa', 'researcher2@usa.gov', 'Dr. Sarah Johnson')

ON CONFLICT (username) DO NOTHING;

-- ============================================
-- INDEX ET OPTIMISATIONS
-- ============================================

-- Index existants
CREATE INDEX IF NOT EXISTS idx_statistique_date ON statistique(date_stat);
CREATE INDEX IF NOT EXISTS idx_statistique_pays ON statistique(id_pays);
CREATE INDEX IF NOT EXISTS idx_statistique_maladie ON statistique(id_maladie);

-- Nouveaux index pour l'authentification
CREATE INDEX IF NOT EXISTS idx_users_country_role ON users(country, role);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- ============================================
-- NETTOYAGE AUTOMATIQUE DES SESSIONS EXPIRÉES
-- ============================================

-- Fonction pour nettoyer les sessions expirées
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VUES UTILES POUR L'ADMINISTRATION
-- ============================================

-- Vue des utilisateurs actifs par pays
CREATE OR REPLACE VIEW v_users_by_country AS
SELECT 
    country,
    role,
    COUNT(*) as user_count,
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_count,
    COUNT(*) FILTER (WHERE last_login > NOW() - INTERVAL '30 days') as recent_login_count
FROM users 
GROUP BY country, role
ORDER BY country, role;

-- Vue des sessions actives
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT 
    s.token,
    u.username,
    u.country,
    u.role,
    s.created_at,
    s.expires_at,
    s.ip_address
FROM sessions s
JOIN users u ON s.user_id = u.id_user
WHERE s.expires_at > NOW()
ORDER BY s.created_at DESC;



SELECT 'Base de données initialisée avec authentification !' as message,
       'Comptes créés: admin_france/admin123, admin_suisse/admin123, admin_usa/admin123' as admin_info,
       'Comptes chercheurs de demo créés avec mot de passe: chercheur123' as chercheur_info;
