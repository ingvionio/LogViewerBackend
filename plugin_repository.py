# plugin_repository.py
from sqlalchemy.orm import sessionmaker
from models import PluginResult, get_database_engine
from datetime import datetime

class PluginResultRepository:
    def __init__(self):
        self.engine = get_database_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    async def save_plugin_result(
        self,
        filename: str,
        segment_id: int,
        plugin_address: str,
        plugin_name: str,
        success: bool,
        message: str,
        metadata_json: dict,
        filtered_logs: list
    ):
        db = self.SessionLocal()
        try:
            result = PluginResult(
                filename=filename,
                segment_id=segment_id,
                plugin_address=plugin_address,
                plugin_name=plugin_name,
                success="true" if success else "false",
                message=message[:500] if message else None,  # обрезаем до 500 символов
                metadata_json=metadata_json or {},
                filtered_logs=filtered_logs or [],
                created_at=datetime.utcnow()
            )
            db.add(result)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    async def get_results_by_filename(self, filename: str):
        """Получить все результаты плагинов по имени файла"""
        db = self.SessionLocal()
        try:
            results = db.query(PluginResult).filter(PluginResult.filename == filename).all()
            return [
                {
                    "segment_id": r.segment_id,
                    "plugin_address": r.plugin_address,
                    "plugin_name": r.plugin_name,
                    "success": r.success == "true",
                    "message": r.message,
                    "metadata": r.metadata_json,
                    "filtered_logs": r.filtered_logs,
                    "created_at": r.created_at.isoformat()
                }
                for r in results
            ]
        finally:
            db.close()

    async def get_results_by_segment(self, filename: str, segment_id: int):
        """Получить результаты плагинов для конкретного сегмента"""
        db = self.SessionLocal()
        try:
            results = db.query(PluginResult).filter(
                PluginResult.filename == filename,
                PluginResult.segment_id == segment_id
            ).all()
            return [ ... ]  # аналогично выше
        finally:
            db.close()