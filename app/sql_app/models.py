from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
import datetime

from .db import Base


class Node(Base):
    __tablename__ = 'nodes'
    node_id = Column(Integer, primary_key=True)
    node_label = Column(String)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    node_description = Column(String)
    node_created = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    node_updated = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

class Project(Base):
    __tablename__ = 'projects'
    project_id = Column(Integer, primary_key=True)
    project_code = Column(String)
    project_label = Column(String)
    project_path = Column(String)
    project_author = Column(Integer, ForeignKey('users.user_id'))
    project_description = Column(String)
    project_created = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    project_updated = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

class UserAccess(Base):
    __tablename__ = 'user_access'
    access_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    access_level = Column(Integer)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    password = Column(String)
