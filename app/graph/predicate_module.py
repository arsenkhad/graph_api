from .vertex import Vertex

def predicate1(graph, vertex : Vertex | str, next_vertex : Vertex | str):
    if type(vertex) == str:
        vertex = graph.get_vertex(vertex)
    if type(next_vertex) == str:
        next_vertex = graph.get_vertex(next_vertex)

    if type(vertex) == Vertex and type(next_vertex) == Vertex:
        return next_vertex, vertex
    print(f'Error in data types. {vertex} or {next_vertex} are not Vertex object or label.')
    return None

default = predicate1
predicates = {'predicate1' : predicate1}