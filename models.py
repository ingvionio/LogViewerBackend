from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy import create_engine
from datetime import datetime
import os
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

Base = declarative_base()
load_dotenv()

class PluginResult(Base):
    __tablename__ = "plugin_results"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, nullable=False)  # ID сегмента из ParseWithLogs
    filename = Column(String(255), nullable=False)  # Чтобы связать с файлом
    plugin_address = Column(String(100), nullable=False)  # Например: "localhost:50051"
    plugin_name = Column(String(100), nullable=True)      # Например: "example_plugin"
    success = Column(String(10), nullable=False)          # "true"/"false" или Boolean
    message = Column(String(500), nullable=True)
    metadata_json = Column(JSON, nullable=True)           # Результат response.metadata
    filtered_logs = Column(JSON, nullable=True)           # Результат response.logs
    created_at = Column(DateTime, default=datetime.utcnow)

class JsonFile(Base):
    __tablename__ = "json_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False)  # Название файла
    segments = Column(JSON, nullable=True)  # Результат ParseWithLogs.parse_file()
    chains = Column(JSON, nullable=True)  # Результат ParseWithLogs.parse_file_to_chain()
    upload_date = Column(DateTime, default=datetime.utcnow)


def get_database_engine():
    db_url = os.getenv('DATABASE_URL', 'sqlite:///./json_files.db')
    return create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})


def create_tables(engine):
    Base.metadata.create_all(bind=engine)