"""Configuração de conexão com o PostgreSQL.

Os valores padrão batem com o docker-compose.yml. Para mudar, defina as
variáveis de ambiente DB_USER, DB_PASSWORD, DB_HOST, DB_PORT e DB_NAME.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def get_engine():
    """Cria o engine do SQLAlchemy para o PostgreSQL do Docker."""
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "iot_db"),
    )
    return create_engine(url)
