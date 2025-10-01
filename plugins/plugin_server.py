from concurrent import futures
import grpc
from proto import logplugin_pb2
from proto import logplugin_pb2_grpc
from datetime import datetime


class PluginService(logplugin_pb2_grpc.PluginServiceServicer):
    def ProcessSegment(self, request, context):
        # Подсчёт метрик
        total_logs = len(request.logs)
        error_count = sum(1 for log in request.logs if log.level.lower() == "error")

        apply_subsegments = 0
        if request.segment_type.lower() == "apply":
            for log in request.logs:
                if "apply calling plan" in log.message.lower():
                    apply_subsegments = 1
                    break

        try:
            start = datetime.fromisoformat(request.start_time)
            end = datetime.fromisoformat(request.end_time)
            duration_sec = (end - start).total_seconds()
        except Exception:
            duration_sec = 0

        metadata = {
            "total_logs": str(total_logs),
            "error_count": str(error_count),
            "apply_subsegments": str(apply_subsegments),
            "duration_sec": str(duration_sec)
        }

        return logplugin_pb2.SegmentResponse(
            success=True,
            message="Metrics calculated successfully",
            metadata=metadata
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    # регистрация сервиса
    logplugin_pb2_grpc.add_PluginServiceServicer_to_server(PluginService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Plugin gRPC server started on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
