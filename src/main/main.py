from ..compiler import *
from ..utils.logging import LogLevel, log, reset_log
import pygame as pg


class View:
    
    elements:dict[str,Element]
    states:dict[str,State]
    surf: pg.Surface
    size: list[int,int]

    def __init__(self, elements:dict[str,Element], states:dict[str,State], size:list[int,int]):
        
        self.elements = elements
        self.states = states
        self.surf = pg.Surface(size)
        self.width = size[0]
        self.height = size[1]

    







####################################
# Pass Objects from compiler to View
####################################

def initialize(path:str, size:list[int,int]) -> View:
    # transfers finished objects from compiler to view
    compiler = Compiler(path)
    state_objects = compiler.states
    elements = compiler.compiled
    return View(elements=elements,states=state_objects, size=size)


