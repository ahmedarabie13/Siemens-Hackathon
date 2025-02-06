# app/services/chat_service.py
import json
import threading
from datetime import datetime


from Agents import run_orchestrator, run_flow_agent
from app.repositories.chat_repository import (
    insert_chat,
    find_chats,
    find_chat_by_id,
    update_chat_by_id,
    delete_chat_by_id, delete_all_chats,
)
from app.services.agent_service import get_agents


def create_chat(data):
    if not data or 'title' not in data:
        return {'error': 'Missing required field: title'}, 400
    chat_doc = {
        "title": data['title'],
        "messages": data.get('messages', [])
    }
    inserted_chat = insert_chat(chat_doc)
    return inserted_chat, 201

def get_chats():
    chats = find_chats()
    return chats, 200

def get_chat(chat_id):
    try:
        chat = find_chat_by_id(chat_id)
    except Exception:
        return {'error': 'Invalid chat ID'}, 400
    if not chat:
        return {'error': 'Chat not found'}, 404
    return chat, 200

def update_chat(chat_id, data):
    update_data = {}
    if 'title' in data:
        update_data['title'] = data['title']
    if 'messages' in data:
        update_data['messages'] = data['messages']
    try:
        updated = update_chat_by_id(chat_id, update_data)
    except Exception:
        return {'error': 'Invalid chat ID'}, 400
    if not updated:
        return {'error': 'Chat not found'}, 404
    return updated, 200

def send_message(chat_id, data):
    if not data or 'message' not in data:
        return {'error': 'Missing required field: message'}, 400
    try:
        chat = find_chat_by_id(chat_id)
    except Exception as e:
        print(e)
        return {'error': 'Invalid chat ID'}, 400
    if not chat:
        return {'error': 'Chat not found'}, 404

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chat['messages'].append({
        'message': data['message'],
        'owner': 'USER',
        'timestamp': timestamp
    })
    try:
        updated_data = {'messages': chat['messages']}
        updated = update_chat_by_id(chat_id, updated_data)
    except Exception as e:
        print(e)
        return {'error': 'Invalid chat ID'}, 400
    if not updated:
        return {'error': 'Chat not found'}, 404
    agents = get_agents()[0]
    threading.Thread(target=chat_and_publish, args=(chat, data, agents,)).start()

    return updated, 200

def chat_and_publish(chat, message, agents):
    result =run_orchestrator(message, agents)
    graph=run_flow_agent(message,result)
    print('Results from chat:', result,graph)
    result_message = {
        'message': result,
        'owner': 'SYSTEM',
        'graph':graph,
        'timestamp': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    }
    update_chat_by_id(chat['_id'], {'messages': chat['messages'] + [result_message]})

def delete_chat(chat_id):
    try:
        deleted = delete_chat_by_id(chat_id)
    except Exception:
        return {'error': 'Invalid chat ID'}, 400
    if not deleted:
        return {'error': 'Chat not found'}, 404
    return {'result': 'Chat deleted'}, 200


def delete_chats():
    try:
        deleted_count = delete_all_chats()
    except Exception:
        return {'error': 'Failed to delete chats'}, 500
    if deleted_count == 0:
        return {'error': 'No chats found to delete'}, 404
    return {'result': f'{deleted_count} chats deleted'}, 200

