import grpc
from abc import ABC, abstractmethod
from proto.Logplugin import logplugin_pb2, logplugin_pb2_grpc
from proto.filter import filter_pb2_grpc, filter_pb2


class PluginClient(ABC):
    @abstractmethod
    def process_segment(self, segment):
        pass


class LogPluginClient(PluginClient):
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = logplugin_pb2_grpc.PluginServiceStub(self.channel)

    def process_segment(self, segment):
        request = logplugin_pb2.SegmentRequest(
            segment_id=segment["Id"],
            segment_type=segment["Type"],
            start_time=segment["StartTime"] or "",
            end_time=segment["EndTime"] or "",
            logs=[
                logplugin_pb2.LogEntry(
                    level=str(log.get("level") or ""),
                    message=str(log.get("message") or ""),
                    timestamp=str(log.get("timestamp") or ""),
                    module=str(log.get("module") or "")
                )
                for log in segment["Logs"]
            ]
        )
        return self.stub.ProcessSegment(request)


class FilterPluginClient(PluginClient):
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = filter_pb2_grpc.PluginServiceStub(self.channel)

    def process_segment(self, segment):
        # Добавляем логику для фильтров если нужно
        filters = []
        if "filters" in segment:
            for filter_criteria in segment["filters"]:
                filters.append(filter_pb2.FilterCriteria(
                    field=filter_criteria.get("field", ""),
                    value=filter_criteria.get("value", ""),
                    exact=filter_criteria.get("exact", False)
                ))

        request = filter_pb2.SegmentRequest(
            segment_id=segment["Id"],
            segment_type=segment["Type"],
            start_time=segment["StartTime"] or "",
            end_time=segment["EndTime"] or "",
            logs=[
                filter_pb2.LogEntry(
                    level=str(log.get("level") or ""),
                    message=str(log.get("message") or ""),
                    timestamp=str(log.get("timestamp") or ""),
                    module=str(log.get("module") or "")
                )
                for log in segment["Logs"]
            ],
            filters=filters
        )
        return self.stub.ProcessSegment(request)


def create_plugin_client(plugin_type, host, port):
    """Фабрика для создания клиентов плагинов"""
    if plugin_type == "log_processor":
        return LogPluginClient(host, port)
    elif plugin_type == "filter":
        return FilterPluginClient(host, port)
    else:
        raise ValueError(f"Unknown plugin type: {plugin_type}")


def send_segment_to_plugin(segment, host, port, plugin_type="log_processor"):
    """
    Отправляет сегмент на плагин указанного типа.

    Args:
        segment: словарь с сегментом
        host: адрес хоста плагина
        port: порт плагина
        plugin_type: "log_processor" или "filter"

    Returns:
        SegmentResponse от плагина
    """
    channel = grpc.insecure_channel(f"{host}:{port}")

    if plugin_type == "log_processor":
        stub = logplugin_pb2_grpc.PluginServiceStub(channel)
        request = logplugin_pb2.SegmentRequest(
            segment_id=segment["Id"],
            segment_type=segment["Type"],
            start_time=segment["StartTime"] or "",
            end_time=segment["EndTime"] or "",
            logs=[
                logplugin_pb2.LogEntry(
                    level=str(log.get("level") or ""),
                    message=str(log.get("message") or ""),
                    timestamp=str(log.get("timestamp") or ""),
                    module=str(log.get("module") or "")
                )
                for log in segment["Logs"]
            ]
        )

    elif plugin_type == "filter":
        stub = filter_pb2_grpc.PluginServiceStub(channel)

        # Обработка фильтров (если есть)
        filters = []
        if "filters" in segment:
            for filter_criteria in segment["filters"]:
                filters.append(filter_pb2.FilterCriteria(
                    field=filter_criteria.get("field", ""),
                    value=filter_criteria.get("value", ""),
                    exact=filter_criteria.get("exact", False)
                ))

        request = filter_pb2.SegmentRequest(
            segment_id=segment["Id"],
            segment_type=segment["Type"],
            start_time=segment["StartTime"] or "",
            end_time=segment["EndTime"] or "",
            logs=[
                filter_pb2.LogEntry(
                    level=str(log.get("level") or ""),
                    message=str(log.get("message") or ""),
                    timestamp=str(log.get("timestamp") or ""),
                    module=str(log.get("module") or "")
                )
                for log in segment["Logs"]
            ],
            filters=filters
        )
        return stub.ProcessSegment(request)

    else:
        raise ValueError(f"Unknown plugin type: {plugin_type}")
class FilterPluginClient(PluginClient):
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = filter_pb2_grpc.PluginServiceStub(self.channel)

    def process_segment(self, segment):
        filters = []
        if "filters" in segment:
            for f in segment["filters"]:
                filters.append(filter_pb2.FilterCriteria(
                    field=f.get("field", ""),
                    value=f.get("value", ""),
                    exact=f.get("exact", False)
                ))

        request = filter_pb2.SegmentRequest(
            segment_id=segment["Id"],
            segment_type=segment["Type"],
            start_time=segment["StartTime"] or "",
            end_time=segment["EndTime"] or "",
            logs=[
                filter_pb2.LogEntry(
                    level=str(log.get("level", "")),
                    message=str(log.get("message", "")),
                    timestamp=str(log.get("timestamp", "")),
                    module=str(log.get("module", ""))
                )
                for log in segment["Logs"]
            ],
            plugin_type=filter_pb2.FILTER,   # ← ОБЯЗАТЕЛЬНО!
            filters=filters
        )
        return self.stub.ProcessSegment(request)


