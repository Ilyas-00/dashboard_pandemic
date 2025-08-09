FROM postgres:15-alpine

LABEL maintainer="mspr-team@example.com"
LABEL version="1.0"
LABEL description="PostgreSQL Database pour Pandémies - ETL Ready"

# Variables d'environnement
ENV POSTGRES_DB=pandemies_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=loading
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Copier le script d'initialisation
COPY init-db.sql /docker-entrypoint-initdb.d/

# Copier les configurations
COPY postgresql.conf /etc/postgresql/postgresql.conf
COPY pg_hba.conf /etc/postgresql/pg_hba.conf

# Créer le répertoire de données
RUN mkdir -p /var/lib/postgresql/data/pgdata && \
    chown -R postgres:postgres /var/lib/postgresql/data

# Health check pour PostgreSQL
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1

EXPOSE 5432

VOLUME ["/var/lib/postgresql/data"]
