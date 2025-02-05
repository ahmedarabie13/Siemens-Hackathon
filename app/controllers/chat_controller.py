# app/controllers/chat_controller.py

from flask import Blueprint, request, jsonify
from app.services.chat_service import create_chat, get_chats, get_chat, update_chat, send_message, delete_chat

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('', methods=['POST'])
def create_chat_route():
    data = request.get_json()
    result, status = create_chat(data)
    return jsonify(result), status

@chat_bp.route('', methods=['GET'])
def get_chats_route():
    result, status = get_chats()
    return jsonify(result), status

@chat_bp.route('/<chat_id>', methods=['GET'])
def get_chat_route(chat_id):
    result, status = get_chat(chat_id)
    return jsonify(result), status

@chat_bp.route('/<chat_id>', methods=['PUT'])
def update_chat_route(chat_id):
    data = request.get_json()
    result, status = update_chat(chat_id, data)
    return jsonify(result), status

@chat_bp.route('/<chat_id>/message', methods=['POST'])
def send_message_route(chat_id):
    data = request.get_json()
    result, status = send_message(chat_id, data)
    return jsonify(result), status

@chat_bp.route('/<chat_id>', methods=['DELETE'])
def delete_chat_route(chat_id):
    result, status = delete_chat(chat_id)
    return jsonify(result), status
