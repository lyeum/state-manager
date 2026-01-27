# src/gm/state_db/configs/setting.py
# State Manager 설정값 관리

import os

from dotenv import load_dotenv

load_dotenv()
# ====================================================================
# PostgreSQL 데이터베이스 설정
# ====================================================================
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))

# Apache AGE 그래프 설정
AGE_GRAPH_NAME = os.getenv("AGE_GRAPH_NAME", "state_db")

# ====================================================================
# 서버 설정
# ====================================================================
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8030))
APP_ENV = os.getenv("APP_ENV", "local")

# ====================================================================
# 데이터베이스 포트
# ====================================================================
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# ====================================================================
# PostgreSQL 연결 설정 딕셔너리
# ====================================================================
DB_CONFIG = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "host": DB_HOST,
    "port": DB_PORT,
}
