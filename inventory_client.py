import grpc
import inventory_pb2
import inventory_pb2_grpc

class InventoryClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = inventory_pb2_grpc.InventoryServiceStub(self.channel)

    def get_item(self, item_id):
        request = inventory_pb2.GetItemRequest(item_id=item_id)
        try:
            response = self.stub.GetItem(request)
            return response.item
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise

    def add_item(self, name, quantity):
        request = inventory_pb2.AddItemRequest(name=name, quantity=quantity)
        response = self.stub.AddItem(request)
        return response.item

    def update_item(self, item_id, name, quantity):
        item = inventory_pb2.Item(item_id=item_id, name=name, quantity=quantity)
        request = inventory_pb2.UpdateItemRequest(item=item)
        try:
            response = self.stub.UpdateItem(request)
            return response.item
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise

    def delete_item(self, item_id):
        request = inventory_pb2.DeleteItemRequest(item_id=item_id)
        try:
            response = self.stub.DeleteItem(request)
            return response.success
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return False
            else:
                raise

    def list_items(self):
        request = inventory_pb2.ListItemsRequest()
        for response in self.stub.ListItems(request):
            yield response.item

    def bulk_update_items(self, updates):
        def request_iterator():
            for item_id, quantity_change in updates.items():
                yield inventory_pb2.BulkUpdateRequest(item_id=item_id, quantity_change=quantity_change)
        response = self.stub.BulkUpdateItems(request_iterator())
        return response.message

    def monitor_inventory(self, item_ids, callback):
        def request_iterator():
            for item_id in item_ids:
                yield inventory_pb2.MonitorInventoryRequest(item_id=item_id)
        for response in self.stub.MonitorInventory(request_iterator()):
            callback(response)