from flask import Flask, jsonify, render_template, request, redirect, url_for
from inventory_client import InventoryClient
import threading
import time

app = Flask(__name__)
client = InventoryClient()

CSS = """
body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; }
.container { background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
h1, h2 { color: #333; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f0f0f0; }
tr:nth-child(even) { background-color: #f9f9f9; }
form { margin-top: 20px; }
label { display: block; margin-bottom: 5px; font-weight: bold; }
input[type="text"], input[type="number"], button { padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 3px; box-sizing: border-box; }
button { background-color: #5cb85c; color: white; cursor: pointer; }
.error { color: red; }
.success { color: green; }
"""


@app.route('/')
def index():
    items = list(client.list_items())
    return render_template('index.html', items=items)


@app.route('/item/<int:item_id>')
def view_item(item_id):
    item = client.get_item(item_id)
    if item:
        return render_template('view_item.html', item=item)
    else:
        return render_template('error.html', message=f"Item with ID {item_id} not found.")


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        new_item = client.add_item(name, quantity)
        return redirect(url_for('index'))
    return render_template('add_item.html')


@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
def update_item(item_id):
    item = client.get_item(item_id)
    if not item:
        return render_template('error.html', message=f"Item with ID {item_id} not found.")

    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        updated_item = client.update_item(item_id, name, quantity)
        if updated_item:
            return redirect(url_for('index'))
        else:
            return render_template('error.html', message=f"Failed to update item with ID {item_id}.")
    return render_template('update_item.html', item=item)


@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    success = client.delete_item(item_id)
    if success:
        return redirect(url_for('index'))
    else:
        return render_template('error.html', message=f"Could not delete item with ID {item_id}.")


@app.route('/bulk_update', methods=['GET', 'POST'])
def bulk_update():
    if request.method == 'POST':
        updates = {}
        for key, value in request.form.items():
            if key.startswith('item_id_') and value:
                item_id = int(value)
                quantity_change_key = f'quantity_change_{key.split("_")[-1]}'
                quantity_change = int(request.form.get(quantity_change_key, 0))
                if quantity_change != 0:
                    updates[item_id] = quantity_change
        if updates:
            message = client.bulk_update_items(updates)
            return render_template('bulk_update_result.html', message=message)
        else:
            return render_template('bulk_update_result.html', message="No updates provided.")
    items = list(client.list_items())
    return render_template('bulk_update.html', items=items)

# Bi-Directional Streaming (Monitor Inventory)


@app.route('/monitor')
def monitor_inventory_page():
    items = list(client.list_items())
    return render_template('monitor.html', items=items)


@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    item_ids_to_monitor = [int(item_id)
                           for item_id in request.form.getlist('item_ids')]
    app.monitored_items_data = {}

    def update_inventory(response):
        print(f"Received update: {response}")
        app.monitored_items_data[response.item.item_id] = response.item

    threading.Thread(target=client.monitor_inventory, args=(
        item_ids_to_monitor, update_inventory), daemon=True).start()
    time.sleep(1)
    return redirect(url_for('view_monitored'))


@app.route('/monitored_items')
def view_monitored():
    return render_template('monitored_items.html', monitored_items=app.monitored_items_data)
# Add to app.py after the CSS variable


@app.route('/ping')
def ping():
    try:
        result = client.ping_pong()
        return jsonify({
            "status": "healthy",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.route('/ping/<message>')
def ping_with_message(message):
    response = client.ping_pong(message=message)
    # Use dictionary access
    return f"Pong! Message: {response['message']}, Count: {response['count']}"


@app.route('/ping/<message>/<int:count>')
def ping_with_message_and_count(message, count):
    response = client.ping_pong(message=message, count=count)
    return f"Pong! Message: {response['message']}, Count: {response['count']}"


@app.route('/health')
def health_check():
    try:
        response = client.ping_pong("healthcheck")
        return {
            "status": "healthy",
            "grpc_response": response['message'],
            "count": response['count']
        }, 200
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 500


@app.route('/grpc-ping/<message>/<int:count>')
def grpc_ping(message, count):
    try:
        result = client.ping_pong(message=message, count=count)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/ping-pong')
def ping_pong():
    return render_template('ping_pong.html')


if __name__ == '__main__':
    app.run(debug=True)
