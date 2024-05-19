from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
import datetime

from .db import Base, engine


from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

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
    project_author = Column(String, ForeignKey('users.user_login'))
    project_description = Column(String)
    project_created = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    project_updated = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

class UserAccess(Base):
    __tablename__ = 'user_access'
    access_id = Column(Integer, primary_key=True)
    user_login = Column(String, ForeignKey('users.user_login'))
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    access_level = Column(Integer)

class User(Base):
    __tablename__ = 'users'
    user_login = Column(String, primary_key=True)
    user_email = Column(String)
    user_password = Column(String)
    user_surname = Column(String)
    user_firstname = Column(String)
    user_patronymic = Column(String)
    user_qualification = Column(String)
    user_department = Column(String)
    user_avatar = Column(String)
