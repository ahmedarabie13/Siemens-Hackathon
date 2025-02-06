# app/repositories/chat_repository.py

from app import mongo
from bson import ObjectId

def transform_doc(doc):
    doc['_id'] = str(doc['_id'])
    return doc

def insert_chat(chat_doc):
    result = mongo.db.chats.insert_one(chat_doc)
    chat_doc['_id'] = str(result.inserted_id)
    return chat_doc

def find_chats():
    chats_cursor = mongo.db.chats.find()
    return [transform_doc(chat) for chat in chats_cursor]

def find_chat_by_id(chat_id):
    chat = mongo.db.chats.find_one({"_id": ObjectId(chat_id)})
    if chat:
        return transform_doc(chat)
    return None

def update_chat_by_id(chat_id, update_data):
    result = mongo.db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": update_data})
    if result.matched_count == 0:
        return None
    chat = mongo.db.chats.find_one({"_id": ObjectId(chat_id)})
    return transform_doc(chat)

def delete_chat_by_id(chat_id):
    result = mongo.db.chats.delete_one({"_id": ObjectId(chat_id)})
    return result.deleted_count > 0

def delete_all_chats():
    result = mongo.db.chats.delete_many({})
    return result.deleted_count
