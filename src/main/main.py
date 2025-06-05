from ..compiler import *
from ..utils.logging import LogLevel, log, reset_log
import re
import pygame as pg


class View:
    
    elements:dict[str,Element]
    states:dict[str,State]
    surf: pg.Surface
    size: list[int,int]
    frames:dict[str,list[State]]

    def __init__(self, elements:dict[str,Element], states:dict[str,State], size:list[int,int], frames:dict[str,list[State]]):
        
        self.elements = elements
        self.states = states
        self.frames = frames
        self.surf = pg.Surface(size)
        self.width = size[0]
        self.height = size[1]
        # In the compiler, also make something which organizes the elements into their respective frames
        # Both the total elements group and frames group will modify each other because they are just pointing
        # to the same object


        self.render_down_scope('global')



    def render_down_scope(self,id_:str):
        """Re-renders the object of the ID provided and all of it's children, 
        nothing else. Useful for only re-rendering a small scope"""
        initial_object = self.elements['abc']
        self.create_image_individual(initial_object)
    



    def create_image_individual(self, element:Element):
        """Re-renders the styles for an individual element"""
        print(element.style)
        computed_styles = {}

        for style in element.style: #This current method of computing styles will not work, as some styles are dependent on others
            # for example, top-left   and height/width percentages in conjunction with position: absolute or position: relative
            val:str = element.style[style]
            acceptable_types = STYLES[style]
            type_:str = None

            
            



    







####################################
# Pass Objects from compiler to View
####################################

def initialize(path:str, size:list[int,int]) -> View:
    # transfers finished objects from compiler to view
    compiler = Compiler(path)
    state_objects = compiler.states
    elements = compiler.compiled
    frames = compiler.frames
    return View(elements=elements,states=state_objects, size=size, frames=frames)


