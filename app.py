from datetime import datetime

from bson import ObjectId
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_socketio import SocketIO

from Agents import run_orchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

# MongoDB configuration (make sure this URI matches your MongoDB setup)
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"  # using service name "mongodb" from docker-compose
# app.config["MONGO_URI"] = "mongodb+srv://engarabie13:1420Ahmed@cluster0.bequp.mongodb.net/myDB?retryWrites=true&w=majority&appName=Cluster0"

# Initialize PyMongo
mongo = PyMongo(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # allow all origins for testing


# ------------------------------------------------------------------------------
# Helper function to transform MongoDB documents into JSON-serializable dicts.
# ------------------------------------------------------------------------------
def transform_doc(doc):
    doc['_id'] = str(doc['_id'])
    return doc

def get_siemens_agents():
    """Retrieve all agents and return them as a Python list."""

    agents_cursor = mongo.db.agents.find()
    agents = [transform_doc(agent) for agent in agents_cursor]
    return agents

# ------------------------------------------------------------------------------
# CRUD Endpoints for "agent"
# Each agent has: title, role, goals, backstory, and optionally docs
# ------------------------------------------------------------------------------
@app.route('/agent', methods=['POST'])
def create_agent():
    """Create a new agent."""
    data = request.get_json()
    # Ensure required fields are provided (here title is now required as well)
    if not data or not all(k in data for k in ('role', 'goals', 'backstory', 'title')):
        return jsonify({'error': 'Missing required fields: title, role, goals, backstory'}), 400

    agent_doc = {
        "title": data['title'],
        "role": data['role'],
        "goals": data['goals'],
        "backstory": data['backstory'],
        "docs": data.get('docs', '')
    }
    result = mongo.db.agents.insert_one(agent_doc)
    agent_doc['_id'] = str(result.inserted_id)
    return jsonify(agent_doc), 201


@app.route('/agent', methods=['GET'])
def get_agents():
    """Retrieve all agents."""
    agents_cursor = mongo.db.agents.find()
    agents = [transform_doc(agent) for agent in agents_cursor]
    return jsonify(agents), 200


@app.route('/agent/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Retrieve a specific agent by ID."""
    try:
        agent = mongo.db.agents.find_one({"_id": ObjectId(agent_id)})
    except Exception:
        return jsonify({'error': 'Invalid agent ID'}), 400
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    return jsonify(transform_doc(agent)), 200


@app.route('/agent/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """Update an existing agent."""
    data = request.get_json()
    update_data = {}
    for field in ['title', 'role', 'goals', 'backstory', 'docs']:
        if field in data:
            update_data[field] = data[field]

    try:
        result = mongo.db.agents.update_one({"_id": ObjectId(agent_id)}, {"$set": update_data})
    except Exception:
        return jsonify({'error': 'Invalid agent ID'}), 400

    if result.matched_count == 0:
        return jsonify({'error': 'Agent not found'}), 404
    agent = mongo.db.agents.find_one({"_id": ObjectId(agent_id)})
    return jsonify(transform_doc(agent)), 200


@app.route('/agent/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent."""
    try:
        result = mongo.db.agents.delete_one({"_id": ObjectId(agent_id)})
    except Exception:
        return jsonify({'error': 'Invalid agent ID'}), 400

    if result.deleted_count == 0:
        return jsonify({'error': 'Agent not found'}), 404
    return jsonify({'result': 'Agent deleted'}), 200


# ------------------------------------------------------------------------------
# CRUD Endpoints for "chat"
# For demonstration, each chat contains a title and a list of messages.
# ------------------------------------------------------------------------------
@app.route('/chat', methods=['POST'])
def create_chat():
    """Create a new chat session."""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Missing required field: title'}), 400

    chat_doc = {
        "title": data['title'],
        "messages": data.get('messages', [])
    }
    result = mongo.db.chats.insert_one(chat_doc)
    chat_doc['_id'] = str(result.inserted_id)
    return jsonify(chat_doc), 201


@app.route('/chat', methods=['GET'])
def get_chats():
    """Retrieve all chat sessions."""
    chats_cursor = mongo.db.chats.find()
    chats = [transform_doc(chat) for chat in chats_cursor]
    return jsonify(chats), 200


@app.route('/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Retrieve a specific chat session."""
    try:
        chat = mongo.db.chats.find_one({"_id": ObjectId(chat_id)})
    except Exception:
        return jsonify({'error': 'Invalid chat ID'}), 400
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    return jsonify(transform_doc(chat)), 200


@app.route('/chat/<chat_id>', methods=['PUT'])
def update_chat(chat_id):
    """Update a chat session."""
    data = request.get_json()
    update_data = {}
    if 'title' in data:
        update_data['title'] = data['title']
    if 'messages' in data:
        update_data['messages'] = data['messages']

    try:
        result = mongo.db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": update_data})
    except Exception:
        return jsonify({'error': 'Invalid chat ID'}), 400

    if result.matched_count == 0:
        return jsonify({'error': 'Chat not found'}), 404
    chat = mongo.db.chats.find_one({"_id": ObjectId(chat_id)})
    return jsonify(transform_doc(chat)), 200


@app.route('/chat/<chat_id>/message', methods=['POST'])
def send_message(chat_id):
    """Send message from user to the chat."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing required field: title'}), 400

    chat = mongo.db.chats.find_one({"_id": ObjectId(chat_id)})
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chat['messages'].append({'message': data['message'],
                             'owner': 'USER',
                             'timestamp': str(timestamp)})

    try:
        result = mongo.db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": chat})
    except Exception:
        return jsonify({'error': 'Invalid chat ID'}), 400
    if result.matched_count == 0:
        return jsonify({'error': 'Chat not found'}), 404

    # TODO: call the crew and wait for the results then update the chat with it
    agent_result=run_orchestrator(data, get_siemens_agents())
    return jsonify(transform_doc(chat)), 200


@app.route('/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat session."""
    try:
        result = mongo.db.chats.delete_one({"_id": ObjectId(chat_id)})
    except Exception:
        return jsonify({'error': 'Invalid chat ID'}), 400

    if result.deleted_count == 0:
        return jsonify({'error': 'Chat not found'}), 404
    return jsonify({'result': 'Chat deleted'}), 200


# ------------------------------------------------------------------------------
# Run the App
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run with SocketIO to support WebSocket endpoints.
    socketio.run(app, host='0.0.0.0', port=7070, debug=True ,allow_unsafe_werkzeug=True)
