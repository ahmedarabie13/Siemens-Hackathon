# app/__init__.py

from flask import Flask
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from .config import Config

# Initialize extensions
mongo = PyMongo()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app
    mongo.init_app(app)
    socketio.init_app(app)

    # Import and register blueprints
    from app.controllers.agent_controller import agent_bp
    from app.controllers.chat_controller import chat_bp

    # Blueprints are registered with URL prefixes
    app.register_blueprint(agent_bp, url_prefix='/agent')
    app.register_blueprint(chat_bp, url_prefix='/chat')

    return app
