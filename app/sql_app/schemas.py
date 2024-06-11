from pydantic import BaseModel
from datetime import datetime


class UserCredAuth(BaseModel):
    user_login : str
    user_password : str

class UserCreate(UserCredAuth):
    user_email : str


class AccessBase(BaseModel):
    user_id : int
    project_id : int

class AccessCreate(AccessBase):
    access_level : int

class Access(AccessBase):
    class Config:
        from_attributes = True

class NodeBase(BaseModel):
    node_label : str = ''
    node_description : str = ''

class NodeCreate(NodeBase):
    pass

class Node(NodeBase):
    project_id : int
    node_id : int
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    project_label : int | str = ''
    project_code : str = ''
    project_description : str = ''

class ProjectCreate(ProjectBase):
    project_author : int

class Project(ProjectBase):
    project_id : int
    class Config:
        from_attributes = True

class ProjectData(ProjectCreate, Project):
    project_created : datetime
    project_updated : datetime
