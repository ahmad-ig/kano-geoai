from sqlalchemy import create_engine
from config.secrets import DB_CONFIG#, DB_PASS, DB_HOST, DB_PORT, DB_NAME

# SQLAlchemy Connection Engine
DATABASE_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

def get_engine():
    return create_engine(DATABASE_URI)