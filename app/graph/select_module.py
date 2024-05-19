from .vertex import Vertex

def select1(vertex : Vertex):
    visited = []
    def visit():
        for edge in sorted(vertex.edges.values(), key=lambda x : str(x['next_vertex'])):
            target = edge['next_vertex']
            if target not in visited:
                visited.append(target)
                return(target)
        return visited[0]
    return visit

default = select1
selectors = {'select1' : select1}