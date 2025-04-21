import grpc
import time
from concurrent import futures
import inventory_pb2
import inventory_pb2_grpc

# In-memory inventory data (for simplicity)
inventory_data = {}
next_item_id = 1


class InventoryServiceServicer(inventory_pb2_grpc.InventoryServiceServicer):
    def GetItem(self, request, context):
        item_id = request.item_id
        if item_id in inventory_data:
            item = inventory_data[item_id]
            return inventory_pb2.GetItemResponse(item=item)
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Item not found')

    def AddItem(self, request, context):
        global next_item_id
        new_item = inventory_pb2.Item(
            item_id=next_item_id, name=request.name, quantity=request.quantity)
        inventory_data[next_item_id] = new_item
        next_item_id += 1
        return inventory_pb2.AddItemResponse(item=new_item)

    def UpdateItem(self, request, context):
        item = request.item
        if item.item_id in inventory_data:
            inventory_data[item.item_id] = item
            return inventory_pb2.UpdateItemResponse(item=item)
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Item not found')

    def DeleteItem(self, request, context):
        item_id = request.item_id
        if item_id in inventory_data:
            del inventory_data[item_id]
            return inventory_pb2.DeleteItemResponse(success=True)
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Item not found')

    def ListItems(self, request, context):
        for item in inventory_data.values():
            yield inventory_pb2.ListItemResponse(item=item)

    def BulkUpdateItems(self, request_iterator, context):
        for request in request_iterator:
            item_id = request.item_id
            quantity_change = request.quantity_change
            if item_id in inventory_data:
                inventory_data[item_id].quantity += quantity_change
                print(
                    f"Updated item {item_id}: Quantity changed by {quantity_change}")
            else:
                print(f"Item {item_id} not found for bulk update.")
        return inventory_pb2.BulkUpdateResponse(message="Bulk update completed.")

    def MonitorInventory(self, request_iterator, context):
        monitored_items = set()
        for request in request_iterator:
            item_id = request.item_id
            monitored_items.add(item_id)
            print(f"Server: Monitoring item: {item_id}")

        while True:
            for item_id in monitored_items:
                if item_id in inventory_data:
                    yield inventory_pb2.MonitorInventoryResponse(item=inventory_data[item_id])
                    print(
                        f"Server: Sending update for item {item_id}: {inventory_data[item_id]}")
            time.sleep(1)

    def PingPong(self, request, context):
        try:
            start_time = time.time()
            time.sleep(0.169)  # Simulate some processing delay
            end_time = time.time()
            server_latency_ms = int((end_time - start_time) * 1000)  # Calculate 
            print(f"Received PingPong request: {request.message}")  # Debug log
            return inventory_pb2.PongResponse(
                message=f"Pong: {request.message}",
                count=request.count + 1,
                latency_ms=server_latency_ms
            )
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server started on port 50051.")
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
