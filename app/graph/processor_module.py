from .vertex import Vertex

def read_note(note):
    print(note['name'])

    pass

def process1(vertex : Vertex, prev_vertex : Vertex):
    notes = vertex.notes

    if not vertex.readstate:
        vertex.readstate = True
        for note in notes.values():
            print(note)
            read_note(note)
    print(prev_vertex, '->', vertex)

default = process1
processors = {'process1': process1}