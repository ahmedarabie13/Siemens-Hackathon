# app/services/agent_service.py

from app.repositories.agent_repository import (
    insert_agent,
    find_agents,
    find_agent_by_id,
    update_agent_by_id,
    delete_agent_by_id,
)

def create_agent(data):
    required_fields = ['title', 'role', 'goals', 'backstory']
    if not data or not all(field in data for field in required_fields):
        return {'error': 'Missing required fields: title, role, goals, backstory'}, 400

    agent_doc = {
        "title": data['title'],
        "role": data['role'],
        "goals": data['goals'],
        "backstory": data['backstory'],
        "docs": data.get('docs', '')
    }
    inserted_agent = insert_agent(agent_doc)
    return inserted_agent, 201


def create_agents(data_list):
    required_fields = ['title', 'role', 'goals', 'backstory']

    if not isinstance(data_list, list):
        return {'error': 'Expected a list of agents'}, 400

    agents = []
    errors = []

    for index, data in enumerate(data_list):
        if not all(field in data for field in required_fields):
            errors.append({'index': index, 'error': 'Missing required fields: title, role, goals, backstory'})
            continue

        agent_doc = {
            "title": data['title'],
            "role": data['role'],
            "goals": data['goals'],
            "backstory": data['backstory'],
            "docs": data.get('docs', '')
        }
        inserted_agent = insert_agent(agent_doc)
        agents.append(inserted_agent)

    response = {"agents": agents}
    if errors:
        response["errors"] = errors

    return response, 201 if agents else 400


def get_agents():
    agents = find_agents()
    return agents, 200

def get_agent(agent_id):
    try:
        agent = find_agent_by_id(agent_id)
    except Exception:
        return {'error': 'Invalid agent ID'}, 400
    if not agent:
        return {'error': 'Agent not found'}, 404
    return agent, 200

def update_agent(agent_id, data):
    update_data = {}
    for field in ['title', 'role', 'goals', 'backstory', 'docs']:
        if field in data:
            update_data[field] = data[field]
    try:
        updated = update_agent_by_id(agent_id, update_data)
    except Exception:
        return {'error': 'Invalid agent ID'}, 400
    if not updated:
        return {'error': 'Agent not found'}, 404
    return updated, 200

def delete_agent(agent_id):
    try:
        deleted = delete_agent_by_id(agent_id)
    except Exception:
        return {'error': 'Invalid agent ID'}, 400
    if not deleted:
        return {'error': 'Agent not found'}, 404
    return {'result': 'Agent deleted'}, 200
