import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chat2graph.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True