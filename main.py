from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from Parse_with_segments import ParseWithLogs
from database import json_repo
from plugin_repository import PluginResultRepository
import os
from fastapi import Depends, HTTPException, Header

app = FastAPI(title="Terraform Logs Parser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все источники (не для продакшена!)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все HTTP методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешает все заголовки
)
@app.post("/api/parsejson")
async def parse_json(file: UploadFile):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате .json")

    content = await file.read()
    text = content.decode("utf-8-sig")
    logs = [json.loads(line) for line in text.splitlines() if line.strip()]

    # main.py
    segments = ParseWithLogs.parse_file(logs)
    await json_repo.save_json_file(file.filename, segments=segments)
    await ParseWithLogs.process_segments_with_plugins(segments, file.filename)  # ← только здесь
    # Запускаем плагины (асинхронно)
    await ParseWithLogs.process_segments_with_plugins(segments, file.filename)
    return {"segments": segments}

@app.post("/api/parsechainsjson")
async def parse_chains_json(file: UploadFile):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате .json")

    content = await file.read()
    text = content.decode("utf-8-sig")
    logs = [json.loads(line) for line in text.splitlines() if line.strip()]


    chains = ParseWithLogs.parse_file_to_chain(logs)
    await json_repo.save_json_file(file.filename, chains=chains)
    return {"chains": chains}

@app.get("/api/jsonfiles/{filename}/plugin-results")
async def get_plugin_results(filename: str):
    plugin_repo = PluginResultRepository()
    results = await plugin_repo.get_results_by_filename(filename)
    return {"filename": filename, "plugin_results": results}

@app.get("/api/jsonfiles/{filename}/segments/{segment_id}/plugin-results")
async def get_plugin_results_for_segment(filename: str, segment_id: int):
    plugin_repo = PluginResultRepository()
    results = await plugin_repo.get_results_by_segment(filename, segment_id)
    return {"filename": filename, "segment_id": segment_id, "plugin_results": results}

@app.get("/api/jsonfiles")
async def get_all_json_filenames():
    """
    Получить список всех названий JSON файлов
    """
    filenames = await json_repo.get_all_filenames()
    return {"filenames": filenames}


@app.get("/api/jsonfiles/{filename}/segments")
async def get_file_segments(filename: str):
    """
    Получить segments по названию файла
    """
    segments = await json_repo.get_segments_by_filename(filename)
    if segments is None:
        raise HTTPException(status_code=404, detail=f"Файл с названием '{filename}' не найден")

    return {"filename": filename, "segments": segments}


@app.get("/api/jsonfiles/{filename}/chains")
async def get_file_chains(filename: str):
    """
    Получить chains по названию файла
    """
    chains = await json_repo.get_chains_by_filename(filename)
    if chains is None:
        raise HTTPException(status_code=404, detail=f"Файл с названием '{filename}' не найден")

    return {"filename": filename, "chains": chains}

# --- API для внешних систем (мониторинг, CI/CD, дашборды) ---


# Зависимость для проверки API-ключа
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    expected_key = os.getenv("API_SECRET_KEY")
    if not expected_key:
        # В dev-режиме ключ не обязателен
        return True
    if x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

@app.get("/api/v1/plugin-results",
         summary="Get all plugin results",
         description="⚠️ Может вернуть большой объём данных. Используйте с осторожностью.")
async def get_all_plugin_results(api_key: bool = Depends(verify_api_key)):
    plugin_repo = PluginResultRepository()
    results = await plugin_repo.get_all_results()
    return {"plugin_results": results}


@app.get("/api/v1/files/{filename}/plugin-results",
         summary="Get plugin results by filename",
         description="Get all plugin results for a specific parsed file")
async def get_plugin_results_by_file(
    filename: str,
    api_key: bool = Depends(verify_api_key)
):
    plugin_repo = PluginResultRepository()
    results = await plugin_repo.get_results_by_filename(filename)
    if not results:
        raise HTTPException(status_code=404, detail=f"No plugin results found for file '{filename}'")
    return {"filename": filename, "plugin_results": results}


@app.get("/api/v1/files/{filename}/segments/{segment_id}/plugin-results",
         summary="Get plugin results by segment",
         description="Get plugin results for a specific segment within a file")
async def get_plugin_results_by_segment(
    filename: str,
    segment_id: int,
    api_key: bool = Depends(verify_api_key)
):
    plugin_repo = PluginResultRepository()
    results = await plugin_repo.get_results_by_segment(filename, segment_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"No results for segment {segment_id} in file '{filename}'")
    return {
        "filename": filename,
        "segment_id": segment_id,
        "plugin_results": results
    }


@app.get("/api/v1/plugins/{plugin_address}/results",
         summary="Get results by plugin address",
         description="Get all results from a specific plugin (e.g., 'localhost:50051')")
async def get_results_by_plugin(
    plugin_address: str,
    api_key: bool = Depends(verify_api_key)
):
    plugin_repo = PluginResultRepository()
    results = await plugin_repo.get_results_by_plugin(plugin_address)
    return {"plugin_address": plugin_address, "plugin_results": results}