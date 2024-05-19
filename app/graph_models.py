from pydantic import BaseModel

class GraphEdgeBase(BaseModel):
    cur_vertex : int | str
    next_vertex : int | str

class GraphEdge(GraphEdgeBase):
    threading : bool = False
    morph : dict = {}

class GraphEdgeDesc(GraphEdgeBase):
    pass


class GraphNode(BaseModel):
    id : int | str
    label : int | str = ''
    metadata : dict = {}
    edges : dict[int | str, GraphEdge] = {}


class GraphModel(BaseModel):
    label : int | str = ''
    vertices : dict[int | str, GraphNode] = {}

class GraphModelReturn(GraphModel):
    id : int