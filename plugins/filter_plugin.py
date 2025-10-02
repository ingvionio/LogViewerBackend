import grpc
from concurrent import futures
from proto.filter import filter_pb2_grpc, filter_pb2


class PluginService(filter_pb2_grpc.PluginServiceServicer):
    def ProcessSegment(self, request, context):
        # проверяем тип плагина
        if request.plugin_type != filter_pb2.FILTER:
            return filter_pb2.SegmentResponse(
                success=False,
                message="Unsupported plugin type"
            )

        filtered_logs = request.logs
        filter_field = "module"
        filter_value = "t1"

        for f in request.filters:
            filter_field = f.field
            filter_value = f.value
            if f.field == "module":
                if f.exact:
                    filtered_logs = [log for log in filtered_logs if log.module == f.value]
                else:
                    filtered_logs = [log for log in filtered_logs if f.value in log.module]

        return filter_pb2.SegmentResponse(
            success=True,
            message=f"Found {len(filtered_logs)} logs for filter {filter_field}={filter_value}",
            logs=filtered_logs,
            metadata={
                "matched": str(len(filtered_logs)),
                "filter_field": filter_field,
                "filter_value": filter_value
            }
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    filter_pb2_grpc.add_PluginServiceServicer_to_server(PluginService(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    print("Filter plugin started on port 50052")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
