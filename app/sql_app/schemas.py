from pydantic import BaseModel
from datetime import datetime


class UserCred(BaseModel):
    user_login : str


class UserCredAuth(UserCred):
    user_password : str


class UserBase(UserCred):
    user_email : str
    user_surname : str
    user_firstname : str
    user_patronymic : str
    user_qualification : str
    user_department : str
    user_avatar : str
    user_password : str

    class Config:
        examples =[{"user_email" : "example@mail.ru",
                    "user_surname" : "Иванов",
                    "user_firstname" : "Иван",
                    "user_patronymic" : "Иванович",
                    "user_qualification" : "Сотрудник",
                    "user_department" : "РК6",
                    "user_avatar" : "beautiful_photo.jpg",
                    "user_password" : "P@ssw0rd", # Password is stored hashed
                }]


class UserCreate(UserBase):
    pass

class User(UserBase):
    class Config:
        from_attributes = True


class AccessBase(BaseModel):
    user_login : str
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
    project_author : str

class Project(ProjectBase):
    project_id : int
    class Config:
        from_attributes = True

class ProjectData(ProjectCreate, Project):
    project_created : datetime
    project_updated : datetime
