"""Ingestão: lê o CSV do Kaggle, limpa os dados e carrega no PostgreSQL.

Uso:
    python src/ingest.py                       # usa data/IOT-temp.csv
    python src/ingest.py caminho/do/arquivo.csv
"""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from config import get_engine

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV = BASE_DIR / "data" / "IOT-temp.csv"
VIEWS_SQL = BASE_DIR / "sql" / "01_views.sql"
TABLE = "temperature_readings"

DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    log_id      TEXT PRIMARY KEY,
    room_id     TEXT NOT NULL,
    noted_at    TIMESTAMP NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    location    VARCHAR(3) NOT NULL
);
"""

# Nomes originais do CSV -> nomes usados no banco
COLUMNS = {
    "id": "log_id",
    "room_id/id": "room_id",
    "noted_date": "noted_at",
    "temp": "temperature",
    "out/in": "location",
}


def load_and_clean(csv_path):
    """Lê o CSV e devolve (DataFrame limpo, dict com estatísticas da limpeza)."""
    df = pd.read_csv(csv_path).rename(columns=COLUMNS)
    stats = {"lidas": len(df)}

    # Data no formato dd-mm-aaaa hh:mm; valores inválidos viram NaT
    df["noted_at"] = pd.to_datetime(df["noted_at"], format="%d-%m-%Y %H:%M", errors="coerce")
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df["location"] = df["location"].astype(str).str.strip().str.title()  # In / Out

    antes = len(df)
    df = df.dropna(subset=["log_id", "room_id", "noted_at", "temperature", "location"])
    stats["invalidas"] = antes - len(df)

    antes = len(df)
    df = df.drop_duplicates(subset="log_id", keep="first")
    stats["duplicadas"] = antes - len(df)

    stats["carregadas"] = len(df)
    return df[list(COLUMNS.values())], stats


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not csv_path.exists():
        sys.exit(f"Arquivo não encontrado: {csv_path}\n"
                 "Coloque o CSV do Kaggle em data/IOT-temp.csv")

    print(f"Lendo {csv_path} ...")
    df, stats = load_and_clean(csv_path)
    print(f"  linhas lidas: {stats['lidas']}")
    print(f"  removidas (inválidas): {stats['invalidas']}")
    print(f"  removidas (duplicadas): {stats['duplicadas']}")

    engine = get_engine()
    with engine.begin() as conn:
        conn.exec_driver_sql(DDL)
        conn.exec_driver_sql(f"TRUNCATE TABLE {TABLE}")  # permite rodar o script mais de uma vez
        df.to_sql(TABLE, conn, if_exists="append", index=False,
                  chunksize=5000, method="multi")
        conn.exec_driver_sql(VIEWS_SQL.read_text(encoding="utf-8"))

    with engine.connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar()
    print(f"Carga concluída: {total} registros em '{TABLE}' e 3 views criadas.")


if __name__ == "__main__":
    main()
