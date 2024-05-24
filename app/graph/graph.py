from multipledispatch import dispatch
from .vertex import Vertex

class Graph :
    @dispatch(int, label=str, select_module_funcs=dict, predicate_module_funcs=dict, processor_module_funcs=dict)
    def __init__(self, id : int, label : str = '', select_module_funcs = {}, predicate_module_funcs = {}, processor_module_funcs = {}) -> None:
        """Initialize empty Graph object.

        Args:
            id (int): Graph id.
            label (str, optional): Graph label. Defaults to ''.
        """

        self.__vertices : dict[str, Vertex] = {}
        self._id : int = id
        self.label : str = label
        self.__functions = {'select_module' : select_module_funcs, 'predicate_module' : predicate_module_funcs, 'processor_module' : processor_module_funcs}
        self.__func_descriptions = {}
        self.__transitions = {}
        self.add_vertex('__BEGIN__')
        self.add_vertex('__END__')

    @dispatch(str, label=str, select_module_funcs=dict, predicate_module_funcs=dict, processor_module_funcs=dict)
    def __init__(self, adot_template : str, label : str = '', select_module_funcs = {}, predicate_module_funcs = {}, processor_module_funcs = {}) -> None:
        """Initialize Graph object from template.

        Args:
            adot_template (str): Graph template file.
            label (str, optional): Graph label. Defaults to ''.
        Raises:
            ValueError: Error during graph import from file.
        """
        self.label = label
        self.__vertices : dict[str, Vertex] = {}
        self.__functions = {'select_module' : select_module_funcs, 'predicate_module' : predicate_module_funcs, 'processor_module' : processor_module_funcs}
        self.__func_descriptions = {}
        self.__transitions = {}
        import_error = self.import_aDOT(adot_template, False)
        if import_error:
            raise ValueError('adot_template must be a path to an aDOT file.')

    @dispatch(int, dict, select_module_funcs=dict, predicate_module_funcs=dict, processor_module_funcs=dict)
    def __init__(self, id : int, dict_template : dict, select_module_funcs = {}, predicate_module_funcs = {}, processor_module_funcs = {}) -> None:
        self._id : int = id
        self.label : str = dict_template.get('project_label')
        self.__functions = {'select_module' : select_module_funcs, 'predicate_module' : predicate_module_funcs, 'processor_module' : processor_module_funcs}
        self.__func_descriptions = {}
        self.__transitions = {}

        self.__vertices : dict[str, Vertex] = {}
        for vert in dict_template.get('vertices').values():
            self.add_vertex(**vert)

        for vert in self.__vertices.values():
            for edge in dict_template['vertices'][str(vert.id)].get('edges', {}).values():
                vertex = self.get_vertex(edge['next_vertex'])
                edge['next_vertex'] = vertex
                edge.pop('cur_vertex', None)
                vert.add_edge(**edge)


    def __str__(self) -> str:
        return self.label

    def print_all(self):
        print(f'Graph {self.label}')
        for vertex in self.__vertices.values():
            print(vertex, *('->', *vertex.edges.keys()) if vertex.edges else '')

    @property
    def id(self):
        return self._id

    def get_vertex(self, vertex_id : str | int) -> Vertex | None:
        return self.__vertices.get(vertex_id, None)

    def get_vertices_IDs(self) -> list[int | str]:
        return [vertex for vertex in self.__vertices]

    def vertex_exists(self, vertex : Vertex | str | int, verbose = True) -> Vertex | None:
        if type(vertex) == Vertex:
            vertex = vertex.id
        if vertex in self.__vertices:
            if verbose:
                print(f'Vertex with ID "{vertex}" already exists')
            return self.__vertices[vertex]
        return None
    
    def add_vertex(self, *args, verbose = False, **kwargs)  -> Vertex | Exception:
        if len(args) == 1 and type(args[0]) == Vertex:
            vertex = args[0]
        else:
            try:
                vertex = Vertex(*args, **kwargs)
            except Exception as error:
                print(error)
                return error
        existing_vertex = self.vertex_exists(vertex, verbose)
        if existing_vertex:
            return existing_vertex
        self.__vertices[vertex.id] = vertex
        return vertex
    
    def add_vertices(self, *vertices, verbose = False) :
        for v in vertices:
            if type(v) != Vertex:
                print(f'TypeError: "{v}" is not a vertex')
            else:
                if not self.vertex_exists(v, verbose): 
                    self.__vertices[v.id] = v

    def del_vertex(self, vertex : str | int | Vertex) -> Vertex:
        if type(vertex) == Vertex:
            vertex = vertex.id
        for v in self.__vertices.values():
            v.del_edge(vertex, False)
        return self.__vertices.pop(vertex)


    def add_func_desc(self, name, module, entry):
        try:
            self.__func_descriptions[name] = {'name' : name, 'module' : module, 'entry' : entry}
        except:
            print('Some error occured.')

    def __get_func(self, description):
        if type(description) == str:
            description = self.__func_descriptions.get(description)
        if type(description) == dict and description.get('module') and description.get('entry'):
            func = self.__functions.get(description['module']).get(description['entry'])
            if not func:
                print(f'Function "{description["entry"]}" does not exist in module "{description["module"]}"')
            return func
        print('Function description has wrong format.')
        return None


    def add_transition(self, name, processor, predicate=None):
        self.__transitions[name] = {}
        if predicate:
            func = self.__get_func(predicate)
            if type(predicate) == dict:
                predicate = predicate.get('name')
            if func:
                self.__transitions[name]['predicate'] = {'name' : predicate, 'func' : func}
        if processor:
            func = self.__get_func(processor)
            if type(processor) == dict:
                processor = processor.get('name')
            if func:
                self.__transitions[name]['function'] = {'name' : processor, 'func' : func}
        if self.__transitions[name]:
            self.__transitions[name]['name'] = name
        else:
            print(f'Transitions:\tNo corresponding funcions found for "{name}"')
            self.__transitions.pop(name)


    def set_selector(self, vertex : Vertex, selector : str | dict):
        func = self.__get_func(selector)
        if type(selector) == dict:
            selector = selector.get('name')
        if func and selector:
                if type(vertex) == Vertex:
                    vertex.selector = {'name' : selector, 'func' : func(vertex)}
                else:
                    print(f'{vertex} is not a Vertex')
        else:
            print(f'Selector function {selector} does not exist')


    # Функция импорта графа из формата aDOT
    def import_aDOT(self, file, clear = True, check_errors = True, from_data = False):
        try:
            file = open(file)
            data = file.read()
        except:
            if not from_data:
                return 1
            data = file

        if check_errors and (data.find('__BEGIN__') == -1 or data.find('__END__') == -1):
            print('Graph has no begin and/or end')
            return 1

        graph_id = data.find('digraph ')
        if check_errors and graph_id == -1:
            print('Imported graph has no ID. Import aborted.')
            return 1
        
        graph_id = data[graph_id + 8 : data.find('\n' or ' ', graph_id + 8)]
        try:
            graph_id = int(graph_id)
        except:
            print('Graph ID is a string')
        
        data = [line.strip() for line in data.split('\n')]

        select = [line for line in data if 'selector' in line]
        func = [line for line in data if 'module' in line and 'entry_func' in line]
        transition_func = [line for line in data if ('predicate' in line or 'function' in line) and line not in func]
        graph = [line for line in data if '->' in line or '=>' in line]

        if check_errors and not graph:
            print('aDOT import failed. Please, check file syntax.')
            return 1

        self._id = graph_id

        if clear:
            self.__vertices.clear()

        for line in func:
            parts = line.split(' ')
            func_name = parts[0]
            func_module = ''
            func_entry = ''
            for part in parts:
                if 'module=' in part:
                    func_module = part[part.find('=') + 1:-1]
                if 'entry_func=' in part:
                    func_entry = part[part.find('=') + 1:-1]
            self.add_func_desc(func_name, func_module, func_entry)

        for line in transition_func:
            parts = line.split(' ')
            func_name = parts[0]
            predicate = ''
            processor = ''
            for part in parts:
                if 'predicate=' in part:
                    predicate = part[part.find('=') + 1:-1]
                if 'function=' in part:
                    processor = part[part.find('=') + 1:-1]
            self.add_transition(func_name, processor, predicate)

        for line in graph:
            line = line.split(' ')
            start_vertex, threading, end_vertex, morphism = line if len(line) > 3 else [*line, '']
            morphism = morphism[morphism.find('=')+1:-1]
            try:
                if start_vertex != '__BEGIN__':
                    start_vertex = int(start_vertex)
                if end_vertex != '__END__':
                    end_vertex = int(end_vertex)
            except:
                print('One of vertex IDs was not an integer. Import interrupted.')
            start_vertex = self.add_vertex(id = start_vertex)
            end_vertex = self.add_vertex(id = end_vertex)
            start_vertex.add_edge(end_vertex, threading = threading == '=>', morph = self.__transitions[morphism] if morphism in self.__transitions else {})

        for line in select:
            label = int(line[:line.find(' ')])
            start = line.find('=', line.find('selector'))+1
            comma = line.find(',', start)
            bracket = line.find(']', start)
            selector = line[start: comma if comma < bracket else bracket]
            self.set_selector(self.__vertices[label], selector)

    # Функция экспорта графа в формат aDOT
    def export_aDOT(self, file) :
        # try:
            file = open(file, 'w')
            file.write(f'digraph {self.id}\n{"{"}\n')

            selectors = [func for func in self.__func_descriptions.values() if func['module'] == 'select_module']
            processors = [func for func in self.__func_descriptions.values() if func['module'] == 'processor_module']
            predicates = [func for func in self.__func_descriptions.values() if func['module'] == 'predicate_module']
            verts_with_selectors = [vertex for vertex in self.__vertices.values() if vertex.get_selector_name()]

            if selectors:
                file.write('// Определения функций-селекторов\n')
                for func in selectors:
                    file.write(f"\t{func['name']} [module={func.get('module')}, entry_func={func.get('entry')}]\n")

            if verts_with_selectors:
                file.write('\n// В узле указана функция-селектор\n')
                for vertex in verts_with_selectors:
                    file.write(f'\t{vertex.id} ["selector="{vertex.get_selector_name()}]\n')
            
            if processors:
                file.write('\n// Определения функций-обработчиков\n')
                for func in processors:
                    file.write(f"\t{func['name']} [module={func.get('module')}, entry_func={func.get('entry')}]\n")

            if predicates:
                file.write('\n// Определения функций-предикатов\n')
                for func in predicates:
                    file.write(f"\t{func['name']} [module={func.get('module')}, entry_func={func.get('entry')}]\n")

            edges = [{'src' : vertex.id, 'dest' : edge['next_vertex'].id, 'thread' : edge['threading'], 'morph' : edge['morph']} for vertex in self.__vertices.values() for edge in vertex.edges.values()]
            
            file.write('\n// Определения функций перехода\n')
            morphisms = []
            for edge in edges:
                morph = edge.get('morph')
                if morph and morph not in morphisms:
                    morphisms.append(morph)

            for morph in morphisms:
                pred = morph.get('predicate')
                func = morph.get('function')
                file.write(f"\t{morph['name']} [{'predicate='+pred['name'] if pred else ''}{', ' if pred and func else ''}{'function='+func['name'] if func else ''}]\n")

            file.write('\n// Описание графовой модели\n')
            for edge in edges:
                file.write(f"\t{edge['src']} {'=>' if edge['thread'] else '->'} {edge['dest']} {'[morphism='+edge['morph']['name']+']' if edge.get('morph') else ''}\n")
            file.write('}\n')
            file.close()
        # except:
        #     print("File creation failed. Check your permissions.")
        #     return 1


    def export_dict(self):
        vertices = {}
        for vert in self.__vertices.values():
            edges = {}
            for id, edge in vert.edges.items():
                edge_copy = edge.copy()
                edge_copy['cur_vertex'] = vert.id
                edge_copy['next_vertex'] = id
                edges[id] = edge_copy
            vertices[vert.id] = {"id" : vert.id, "label" : vert.label, "edges" : edges, "metadata" : vert.metadata}
        print(self.id)
        return {
            "id" : self.id,
            "label" : self.label,
            "vertices" : vertices
        }


    def __run_edge(self, vertex : Vertex, next_vertex : Vertex):
        edge = vertex.get_edge(next_vertex)
        if edge.get('morph'):
            pred = edge['morph'].get('predicate')
            proc = edge['morph'].get('function')
            if pred:
                args = pred['func'](self, vertex, next_vertex)
                if proc and args:
                    proc['func'](*args)

    def walk_graph(self):
        cur_vertex = self.__vertices['__BEGIN__']
        next_vertex = cur_vertex

        while cur_vertex != self.__vertices['__END__']:
            if cur_vertex.selector:
                next_vertex = cur_vertex.selector()
            else:
                next_vertex = list(cur_vertex.edges.values())[0]['next_vertex']
            self.__run_edge(cur_vertex, next_vertex)
            print(cur_vertex.id, '->', next_vertex.id)
            cur_vertex = next_vertex


    def get_priorities(self, start_vertex : Vertex = None, end_vertex : Vertex | str = '__END__'):
        visited = set()
        branch_endpoints = set()
        paths : list[list] = []
        if type(end_vertex) == Vertex:
            end_vertex = end_vertex.id
        visited.add(end_vertex)

        def run_edges(vertex : Vertex, path : list = []):
            path.append(vertex.id)
            if vertex.id in visited:
                branch_endpoints.add(vertex.id)
                paths.append(path)
            else:
                visited.add(vertex.id)
                for edge in vertex.edges:
                    run_edges(vertex.get_edge(edge).get('next_vertex'), path.copy())

        if not start_vertex or type(start_vertex) != Vertex:
            start_vertex = self.get_vertex('__BEGIN__')

        if start_vertex:
            run_edges(start_vertex)

        ordered_endpoints = [start_vertex.id, end_vertex]
        for path in paths:
            path_endpoints = [start_vertex.id]
            for vert in path:
                if vert in branch_endpoints and vert not in path_endpoints:
                    path_endpoints.append(vert)

            for i, vert in enumerate(path_endpoints):
                if vert not in ordered_endpoints:
                    ordered_endpoints.insert(ordered_endpoints.index(path_endpoints[i-1]) + 1, vert)

        priorities = []
        for endpoint in ordered_endpoints:
            branches = [path[:len(path) - path[::-1].index(endpoint) - 1] for path in paths if path.count(endpoint)]
            # print(*branches, '\n', sep='\n')
            for branch in sorted(branches, reverse=True, key=lambda branch : len([vert for vert in branch if vert in priorities])):
                for vertex in branch:
                    if vertex not in priorities:
                        priorities.append(vertex)
            if endpoint not in priorities:
                priorities.append(endpoint)

        return priorities