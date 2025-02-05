# app/controllers/agent_controller.py

from flask import Blueprint, request, jsonify
from app.services.agent_service import create_agent, get_agents, get_agent, update_agent, delete_agent

agent_bp = Blueprint('agent', __name__)

@agent_bp.route('', methods=['POST'])
def create_agent_route():
    data = request.get_json()
    result, status = create_agent(data)
    return jsonify(result), status

@agent_bp.route('', methods=['GET'])
def get_agents_route():
    result, status = get_agents()
    return jsonify(result), status

@agent_bp.route('/<agent_id>', methods=['GET'])
def get_agent_route(agent_id):
    result, status = get_agent(agent_id)
    return jsonify(result), status

@agent_bp.route('/<agent_id>', methods=['PUT'])
def update_agent_route(agent_id):
    data = request.get_json()
    result, status = update_agent(agent_id, data)
    return jsonify(result), status

@agent_bp.route('/<agent_id>', methods=['DELETE'])
def delete_agent_route(agent_id):
    result, status = delete_agent(agent_id)
    return jsonify(result), status
