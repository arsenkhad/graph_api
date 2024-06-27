from typing import Annotated
from fastapi import Depends, FastAPI, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import fileinput

from .auth import auth, get_current_user, AccessLevels, check_access
from .graph.graph import Graph
from .sql_app.db import get_db, Base, engine
from .sql_app import models, schemas, crud
from .graph_models import GraphModel, GraphModelReturn, GraphEdge, GraphEdgeDesc
from .config import SAVE_DIRECTORY

access_exception = HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Not enough access rights",
    )

wrong_project_exception = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Project identifier doesn`t match",
    )

save_fail_exception = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Project save failed",
    )

non_exist_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Object doesn`t exist"
)

illegal_input_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Request is illegal"
)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth)


def get_project_by_pid(db : Session, pid : int) -> Graph | None:
    project = crud.get_project_by_id(db, pid)
    if not project:
        return None

    graph = Graph(pid, label=project.project_label)
    for node in crud.get_project_nodes(db, pid):
        graph.add_vertex(node.node_id, node.node_label, metadata={
            'node_description' : node.node_description,
            'node_created' : node.node_created,
            'node_updated' : node.node_updated,
            })
    graph.import_aDOT(project.project_path, clear=False, check_errors=False)
    return graph


def save_project_by_pid(db : Session, pid : int, project_graph : Graph):
    project = crud.get_project_by_id(db, pid)
    if not project:
        raise wrong_project_exception
    updated = []
    new_nodes = []
    project_nodes = crud.get_project_nodes(db, pid)
    for v_id in project_graph.get_vertices_IDs():
        if v_id not in ['__BEGIN__', '__END__']:
            vert = project_graph.get_vertex(v_id)
            node_new = schemas.NodeCreate(node_label=str(vert.label), node_description=vert.metadata.get('node_description', ''))
            db_node_record = None
            if type(vert.id) == int:
                db_node_record = crud.get_node_by_id(db, vert.id)
                if db_node_record and db_node_record.project_id != pid:
                    raise wrong_project_exception
            
            if db_node_record:
                updated.append(crud.update_node(db, schemas.Node(node_id=vert.id, project_id=pid, **node_new.model_dump()), flush=False))
            else:
                new_node = crud.add_node(db, pid, node_new, flush=False)
                new_nodes.append((v_id, new_node))
    if project_graph.export_aDOT(project.project_path):
        raise save_fail_exception
    for node in project_nodes:
        if node not in updated:
            crud.del_node(db, node.node_id)
    db.commit()
    for obj in updated:
        db.refresh(obj)

    for _, node in new_nodes:
            db.refresh(node)

    with fileinput.FileInput(project.project_path, inplace=True) as file:
        for line in file:
            for id, node in new_nodes:
                line = line.replace(str(id), str(node.node_id))
            print(line, end='')


    crud.update_project(db, schemas.Project(project_id=pid))
    return None




@app.get("/project")
def get_available_projects_id(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    return {'projects': crud.get_user_projects(db, current_user.user_id)}

@app.get("/project/info")
def get_available_projects_info(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    return {'projects': crud.get_user_projects_data(db, current_user.user_id)}


@app.get("/project/{project_id}")
async def get_project_info(
    project_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.read_access):
        raise access_exception
    db_project = crud.get_project_by_id(db, project_id)
    if not db_project:
        raise non_exist_exception

    access = schemas.Access(user_id=current_user.user_id, project_id=project_id)
    user_access = crud.get_user_access(db, access)
    return {'project' : crud.strip_project_path(db_project), 'access' : user_access}

@app.get("/project/{project_id}/graph")
async def get_full_graph(
    project_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> GraphModelReturn:
    if not check_access(db, current_user, project_id, AccessLevels.read_access):
        raise access_exception
    graph : Graph = get_project_by_pid(db, project_id)
    return GraphModelReturn(**graph.export_dict())

@app.get("/project/{project_id}/users")
async def get_project_users(
    project_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.read_access):
        raise access_exception
    return {'users' : crud.get_project_users(db, project_id)}

@app.get("/project/{project_id}/chapters")
async def get_ordered_chapters(
    project_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.read_access):
        raise access_exception
    graph : Graph = get_project_by_pid(db, project_id)
    return {"chapters" : graph.get_priorities()}


@app.post("/project")
async def create_project(
    project : schemas.ProjectBase,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    project = schemas.ProjectCreate(project_author = current_user.user_id, **project.model_dump())
    db_project = crud.add_project(db, project, dir=SAVE_DIRECTORY)
    graph = get_project_by_pid(db, db_project.project_id)
    graph.get_vertex('__BEGIN__').add_edge(graph.get_vertex('__END__'))
    save_project_by_pid(db, db_project.project_id, graph)
    return {'Message' : 'Success', 'project' : db_project}


@app.post("/project/{project_id}/graph")
async def save_full_graph(
    project_id : int,
    project : GraphModel,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    graph = Graph(project_id, project.model_dump())
    save_project_by_pid(db, project_id, graph)
    return {'Message' : 'Success'}


@app.post("/project/{project_id}/node")
async def add_new_node(
    project_id : int,
    node : schemas.NodeCreate,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    new_node = crud.add_node(db, project_id, node)
    return {'Message' : 'Success', 'node' : new_node}


@app.post("/project/{project_id}/edge")
async def add_new_edge(
    project_id : int,
    edge : GraphEdge,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    graph : Graph = get_project_by_pid(db, project_id)

    edge_dump = {**edge.model_dump()}
    edge_dump['next_vertex'] = graph.get_vertex(edge.next_vertex)
    vert = graph.get_vertex(edge.cur_vertex)
    if not vert:
        raise non_exist_exception
    if edge.cur_vertex == '__END__' or edge.next_vertex == '__BEGIN__':
        raise illegal_input_exception
    vert.add_edge(**edge_dump)
    save_project_by_pid(db, project_id, graph)
    return {'Message' : 'Success'}


@app.post("/project/{project_id}/users/{user_id}")
async def add_new_access(
    project_id : int,
    user_id : int,
    access_level : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    if (access_level not in [AccessLevels.read_access, AccessLevels.edit_access]) or user_id == current_user.user_id:
        raise illegal_input_exception

    access = schemas.AccessCreate(user_id=user_id, project_id=project_id, access_level=access_level)
    if crud.get_user_access(db, access):
        crud.update_access(db, access)
    else:
        crud.add_access(db, access)
    return {'Message' : 'Success'}


@app.patch("/project/{project_id}")
async def update_project_info(
    project_id : int,
    project : schemas.Project,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    upd_project = crud.update_project(db, project)
    return {'Message' : 'Success', 'project' : upd_project}


@app.patch("/project/{project_id}/node/{node_id}")
async def update_node_info(
    project_id : int,
    node_id : int,
    node : schemas.NodeCreate,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    db_node = crud.get_node_by_id(db, node_id)
    if not db_node:
        raise non_exist_exception
    if db_node.project_id != project_id:
        raise wrong_project_exception

    upd_node = crud.update_node(db, node)
    return {'Message' : 'Success', 'node' : upd_node}



@app.delete("/project/{project_id}")
async def delete_full_project(
    project_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.full_access):
        raise access_exception
    if not crud.del_project(db, project_id):
        raise non_exist_exception
    return {'Message' : 'Success'}


@app.delete("/project/{project_id}/users/{user_id}")
async def delete_user_access(
    project_id : int,
    user_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    
    access = schemas.Access(user_id=user_id, project_id=project_id)
    if not crud.del_access(db, access):
        raise non_exist_exception
    return {'Message' : 'Success'}


@app.delete("/project/{project_id}/node/{node_id}")
async def delete_graph_node(
    project_id : int,
    node_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    graph : Graph = get_project_by_pid(db, project_id)
    if graph.get_vertex(node_id):
        graph.del_vertex(node_id)
        save_project_by_pid(db, project_id, graph)
    return {'Message' : 'Success'}


@app.delete("/project/{project_id}/edge")
async def delete_graph_edge(
    project_id : int,
    edge : GraphEdgeDesc,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    graph : Graph = get_project_by_pid(db, project_id)
    
    vert = graph.get_vertex(edge.cur_vertex)
    if not vert:
        raise non_exist_exception
    vert.del_edge(edge.next_vertex)
    save_project_by_pid(db, project_id, graph)
    return {'Message' : 'Success'}
