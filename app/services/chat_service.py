# app/services/chat_service.py

from datetime import datetime
from app.repositories.chat_repository import (
    insert_chat,
    find_chats,
    find_chat_by_id,
    update_chat_by_id,
    delete_chat_by_id,
)

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
    return updated, 200

def delete_chat(chat_id):
    try:
        deleted = delete_chat_by_id(chat_id)
    except Exception:
        return {'error': 'Invalid chat ID'}, 400
    if not deleted:
        return {'error': 'Chat not found'}, 404
    return {'result': 'Chat deleted'}, 200
