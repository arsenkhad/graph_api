from sqlalchemy.orm import Session
import datetime

from . import models, schemas

def strip_project_path(db_project: models.Project):
    return schemas.ProjectData(**db_project.__dict__)

def get_user(db: Session, login: str):
    return db.get(models.User, login)

def get_user_access(db: Session, access: schemas.Access):
    all_user_access = db.query(models.UserAccess).filter(models.UserAccess.user_login == access.user_login)
    project_access = all_user_access.filter(models.UserAccess.project_id == access.project_id).first()
    full_access = all_user_access.filter(models.UserAccess.project_id == None).first()

    if full_access and ((not project_access) or (full_access.access_level > project_access.access_level)):
        return full_access.access_level
    if project_access:
        return project_access.access_level
    return None

def get_user_projects(db: Session, login: str):
    all_user_access = db.query(models.UserAccess).filter(models.UserAccess.user_login == login)
    if all_user_access.filter(models.UserAccess.project_id == None).first():
        return [project.project_id for project in db.query(models.Project)]
    return [item.project_id for item in all_user_access if item.access_level]

def get_user_projects_data(db: Session, login: str):
    db_project_ids = get_user_projects(db, login)
    return [strip_project_path(get_project_by_id(db, project_id)) for project_id in  db_project_ids]

def get_project_by_id(db: Session, project_id: int):
    return db.get(models.Project, project_id)

def get_project_nodes(db: Session, project_id: int):
    return db.query(models.Node).filter(models.Node.project_id == project_id).all()

def get_node_by_id(db: Session, node_id: int):
    return db.get(models.Node, node_id)


def apply_change(db: Session, object: models.Base):
    db.commit()
    db.refresh(object)
    return object


def add_access(db: Session, access: schemas.AccessCreate, flush=True):
    db_access = models.UserAccess(**access.model_dump())
    db.add(db_access)
    if flush:
        apply_change(db, db_access)
    return db_access

def add_user(db: Session, user: schemas.UserCreate, flush=True):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    if flush:
        apply_change(db, db_user)
    return db_user

def add_node(db: Session, project_id: int, node: schemas.NodeCreate, flush=True):
    db_node = models.Node(project_id=project_id, **node.model_dump())
    db.add(db_node)
    update_project(db, schemas.Project(project_id=project_id), flush=flush)
    if flush:
        apply_change(db, db_node)
    return db_node

def add_project(db: Session, project: schemas.ProjectCreate, dir: str):
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    apply_change(db, db_project)
    db_project.project_path = dir + str(db_project.project_id) + '.gv'
    apply_change(db, db_project)

    access_setting = schemas.AccessCreate(user_login=db_project.project_author, project_id=db_project.project_id, access_level=3)
    add_access(db, access_setting)

    return db_project


def update_access(db: Session, access: schemas.AccessCreate, flush=True):
    db_access = db.query(models.UserAccess).filter(models.UserAccess.user_login == access.user_login, models.UserAccess.project_id == access.project_id).first()
    db_access.access_level = access.access_level
    if flush:
        apply_change(db, db_access)
    return db_access

def update_node(db: Session, node: schemas.Node, flush=True):
    db_node = get_node_by_id(db, node.node_id)
    for attr, value in node.model_dump().items():
        if value:
            setattr(db_node, attr, value)
    db_node.node_updated = datetime.datetime.now(datetime.UTC)

    update_project(db, schemas.Project(project_id=node.project_id), flush=flush)
    if flush:
        apply_change(db, db_node)
    return db_node

def update_project(db: Session, project: schemas.Project, flush=True):
    db_project = get_project_by_id(db, project.project_id)
    for attr, value in project.model_dump().items():
        if value:
            setattr(db_project, attr, value)
    db_project.project_updated = datetime.datetime.now(datetime.UTC)
    if flush:
        apply_change(db, db_project)
    return db_project


def del_user(db: Session, user_login: str, flush=True):
    db_user = db.get(models.User, user_login)
    if db_user:
        db.delete(db_user)
        if flush:
            apply_change(db, db_user)
            return True
    return db_user

def del_node(db: Session, node_id: int, flush=True):
    db_node = get_node_by_id(db, node_id)
    if db_node:
        db.delete(db_node)
        update_project(db, schemas.Project(project_id=db_node.project_id), flush=flush)
        if flush:
            db.commit()
            return True
    return db_node

def del_project(db: Session, project_id: int, flush=True):
    db_project = get_project_by_id(db, project_id)
    if db_project:
        db.delete(db_project)
        if flush:
            db.commit()
            return True
    return db_project
