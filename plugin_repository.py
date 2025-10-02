# plugin_repository.py
from sqlalchemy import desc, func
from sqlalchemy.orm import sessionmaker, aliased
from models import PluginResult, get_database_engine
from datetime import datetime

class PluginResultRepository:
    def __init__(self):
        self.engine = get_database_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def save_plugin_result(
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

        # plugin_repository.py
    def get_all_results(self):
        """Получить все результаты из базы данных."""
        db = self.SessionLocal()
        try:
            results = db.query(PluginResult).order_by(PluginResult.created_at.desc()).all()
            return [
                {
                    "id": r.id,
                    "filename": r.filename,
                    "segment_id": r.segment_id,
                    "plugin_address": r.plugin_address,
                    "plugin_name": r.plugin_name,
                    "success": r.success == "true",
                    "message": r.message,
                    "metadata": r.metadata_json,
                    "filtered_logs": r.filtered_logs,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        except Exception as e:
            print(f"❌ Ошибка в get_all_results: {e}")
            raise
        finally:
            db.close()

    def get_results_by_filename(self, filename: str):
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


    # plugin_repository.py
    def delete_results_by_filename(self, filename: str):
        """Удаляет все результаты плагинов для файла."""
        db = self.SessionLocal()
        try:
            db.query(PluginResult).filter(PluginResult.filename == filename).delete()
            db.commit()
        finally:
            db.close()

    def get_latest_results_by_filename(self, filename: str):
        """Получить последний результат для каждого плагина по файлу."""
        db = self.SessionLocal()
        try:
            # создаём подзапрос: для каждого plugin_address берём max(created_at)
            subq = (
                db.query(
                    PluginResult.plugin_address,
                    func.max(PluginResult.created_at).label("max_created")
                )
                .filter(PluginResult.filename == filename)
                .group_by(PluginResult.plugin_address)
                .subquery()
            )

            # алиас таблицы PluginResult
            pr_alias = aliased(PluginResult)

            # джоин с подзапросом, чтобы взять полный объект последнего результата
            latest_results = (
                db.query(pr_alias)
                .join(subq,
                      (pr_alias.plugin_address == subq.c.plugin_address) &
                      (pr_alias.created_at == subq.c.max_created))
                .all()
            )

            # преобразуем в словари
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
                for r in latest_results
            ]
        finally:
            db.close()
