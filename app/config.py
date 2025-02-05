# app/config.py

class Config:
    SECRET_KEY = 'supersecretkey'
    MONGO_URI = "mongodb://localhost:27017/mydatabase"
    # For production or remote deployments, update the URI accordingly.
