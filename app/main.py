from typing import Annotated
from fastapi import Depends, FastAPI, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import auth, get_current_user, AccessLevels, check_access
from .graph.graph import Graph
from .sql_app.db import get_db
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
    for v_id in project_graph.get_vertices_IDs():
        if v_id not in ['__BEGIN__', '__END__']:
            vert = project_graph.get_vertex(v_id)
            node_new = schemas.NodeCreate(node_label=vert.label, node_description=vert.metadata['node_description'])
            db_node_record = None
            if type(vert.id) == int:
                db_node_record = crud.get_node_by_id(db, vert.id)
                if db_node_record and db_node_record.project_id != pid:
                    raise wrong_project_exception
            
            if db_node_record:
                updated.append(crud.update_node(db, schemas.Node(node_id=vert.id, project_id=pid, **node_new.model_dump()), flush=False))
            else:
                updated.append(crud.add_node(db, pid, node_new, flush=False))
    if project_graph.export_aDOT(project.project_path):
        raise save_fail_exception
    db.commit()
    for obj in updated:
        db.refresh(obj)
    crud.update_project(db, schemas.Project(project_id=pid))
    return None




@app.get("/project")
def get_available_projects(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    return {'projects': crud.get_user_projects(db, current_user.user_login)}


@app.get("/project/{project_id}")
async def get_full_graph(
    project_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> GraphModelReturn:
    if not check_access(db, current_user, project_id, AccessLevels.read_access):
        raise access_exception
    graph : Graph = get_project_by_pid(db, project_id)
    return GraphModelReturn(**graph.export_dict())


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
    project = schemas.ProjectCreate(project_author = current_user.user_login, **project.model_dump())
    db_project = crud.add_project(db, project, dir=SAVE_DIRECTORY)
    graph = get_project_by_pid(db, db_project.project_id)
    graph.get_vertex('__BEGIN__').add_edge(graph.get_vertex('__END__'))
    save_project_by_pid(db, db_project.project_id, graph)
    return {'Message' : 'Success', 'Project_Created' : db_project}


@app.post("/project/{project_id}")
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
    return {'Message' : 'Success', 'Node_Created' : new_node}


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
    if not vert or edge.cur_vertex == '__END__' or edge.next_vertex == '__BEGIN__':
        raise status.HTTP_400_BAD_REQUEST
    vert.add_edge(**edge_dump)
    save_project_by_pid(db, project_id, graph)
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
    return {'Message' : 'Success', 'Project_Updated' : upd_project}


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
    return {'Message' : 'Success', 'Node_Updated' : upd_node}



@app.delete("/project/{project_id}")
async def delete_full_graph(
    project_id : int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.full_access):
        raise access_exception
    if not crud.del_project(db, project_id):
        raise non_exist_exception
    for node in crud.get_project_nodes(db, project_id):
        crud.del_node(db, node.node_id)
    return {'Message' : 'Success'}


@app.delete("/project/{project_id}/node/{node_id}")
async def delete_graph_node(
    project_id : int,
    node_id : int | str,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not check_access(db, current_user, project_id, AccessLevels.edit_access):
        raise access_exception
    graph : Graph = get_project_by_pid(db, project_id)
    if graph.get_vertex(node_id):
        graph.del_vertex(node_id)
        save_project_by_pid(db, project_id, graph)
    if not crud.del_node(db, node_id):
        raise non_exist_exception
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
        raise status.HTTP_400_BAD_REQUEST
    vert.del_edge(edge.next_vertex)
    save_project_by_pid(db, project_id, graph)
    return {'Message' : 'Success'}
