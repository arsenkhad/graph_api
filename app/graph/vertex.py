from __future__ import annotations

def _check_type(obj, obj_name, types):
    def get_types(types_iterable):
        print(types_iterable)
        return ' | '.join(list(map(lambda type : str(type)[7:-1], types_iterable)))
    try:
        iter(types)
    except:
        types = [types]
    if type(obj) not in types:
        print(f'"{obj_name}" type must be {get_types(types)}. {get_types([type(obj)])} provided instead.')
        return False
    return True


class Vertex :
    '''Represents single vertex of oriented graph'''
    def __init__(self, id : int | str, label : str = None, selector = {}, metadata = {}, **kwargs) -> None:
        """_summary_

        Args:
            id (int | str): id of a vertex. Defaults to None.
            label (str, optional): label of a vertex. Defaults to None.
            pos (list[2], optional): position of a vertex. Defaults to None.
            selector (dict, optional): selector function associated with vertex. Defaults to {}.
            metadata (dict, optional): field for description, date of creation, etc. Defaults to {}.
        """
        self._id = id
        self._label = str(label) if label else str(self._id)
        self._was_read = False
        self._edges : dict[str, dict] = {}
        self._selector = selector

        self.metadata = metadata
        self._notes = {}

    def __eq__(self, vertex : Vertex) -> bool:
        return self._id == vertex._id

    def __str__(self) -> str:
        return self._label if self._label else f'ID: {self._id}'

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label
    
    @label.setter
    def label(self, label : str):
        if _check_type(label, 'label', str):
            self._label = label

    @property
    def edges(self):
        return self._edges

    def add_edge(self, next_vertex : Vertex, morph : dict = {}, threading : bool = False, **kwargs):
        if _check_type(next_vertex, 'next_vertex', Vertex):
            self._edges[next_vertex.id] = {'next_vertex' : next_vertex, 'threading': threading}
            self.set_morph(next_vertex, morph)

    def get_edge(self, next_vertex : Vertex | str | int, verbose = True) -> dict | None:
        if _check_type(next_vertex, 'next_vertex', [Vertex, str, int]):
            if type(next_vertex) == Vertex:
                next_vertex = next_vertex.id
            edge = self._edges.get(next_vertex)
            if not edge:
                if verbose:
                    print(f'Edge {next_vertex} does not exist.')
                return None
            return edge
        return None

    def del_edge(self, edge_vertex : Vertex | str | int, verbose = True) -> dict | None:
        if _check_type(edge_vertex, 'edge_vertex', [Vertex, str, int]):
            if type(edge_vertex) == Vertex:
                edge_vertex = edge_vertex.id

            removed_edge = self._edges.pop(edge_vertex, None)
            if not removed_edge and verbose:
                print('You tried deleting non-existant edge')
            return removed_edge
        return None

    def set_morph(self, edge_vertex : Vertex | str | int, morph : dict):
        if _check_type(edge_vertex, 'edge_vertex', [Vertex, str, int]):
            if type(edge_vertex) == Vertex:
                edge_vertex = edge_vertex.id
            edge = self.get_edge(edge_vertex, False)
            if not edge:
                raise ValueError(f'Edge {edge_vertex} does not exist.')

            if _check_type(morph, 'morph', dict):
                edge['morph'] = morph

    @property
    def selector(self):
        if self._selector:
            return self._selector['func']
        return None

    @selector.setter
    def selector(self, selector_info : dict):
        if _check_type(selector_info, 'selctor', dict):
            name = selector_info.get('name')
            func = selector_info.get('func')
            if name and func:
                self._selector = {'name' : name, 'func' : func}
            else:
                print('Error: Must provide selector name and func.')

    def get_selector_name(self):
        if self._selector:
            return self._selector['name']
        return None

    @property
    def notes(self):
        return self._notes

    def add_note(self, note_path : str, note_name : str):
        if _check_type(note_path, 'note_path', str) and _check_type(note_name, 'note_name', str):
            self._notes[note_name] = {'name' : note_name, 'path' : note_path}

    def del_note(self, note_name : str):
        if _check_type(note_name, 'note_name', str):
            removed_note = self._notes.pop(note_name, None)
            if not removed_note:
                print('You tried deleting non-existant note')
            return removed_note
        return None

    @property
    def readstate(self):
        return self._was_read
    
    @readstate.setter
    def readstate(self, readstate = False):
        self._was_read = bool(readstate)
    
    def get_all(self):
        return self.id, self.label, self.metadata