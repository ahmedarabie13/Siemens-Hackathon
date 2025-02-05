# app/repositories/agent_repository.py

from app import mongo
from bson import ObjectId

def transform_doc(doc):
    doc['_id'] = str(doc['_id'])
    return doc

def insert_agent(agent_doc):
    result = mongo.db.agents.insert_one(agent_doc)
    agent_doc['_id'] = str(result.inserted_id)
    return agent_doc

def find_agents():
    agents_cursor = mongo.db.agents.find()
    return [transform_doc(agent) for agent in agents_cursor]

def find_agent_by_id(agent_id):
    agent = mongo.db.agents.find_one({"_id": ObjectId(agent_id)})
    if agent:
        return transform_doc(agent)
    return None

def update_agent_by_id(agent_id, update_data):
    result = mongo.db.agents.update_one({"_id": ObjectId(agent_id)}, {"$set": update_data})
    if result.matched_count == 0:
        return None
    agent = mongo.db.agents.find_one({"_id": ObjectId(agent_id)})
    return transform_doc(agent)

def delete_agent_by_id(agent_id):
    result = mongo.db.agents.delete_one({"_id": ObjectId(agent_id)})
    return result.deleted_count > 0
