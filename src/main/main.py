from ..compiler import *
from ..utils.logging import LogLevel, log, reset_log
import re
from collections import deque
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
        self.surf = pg.Surface(size,pg.SRCALPHA)
        self.surf.fill((0,0,0,255))
        self.width = size[0]
        self.height = size[1]
        # In the compiler, also make something which organizes the elements into their respective frames
        # Both the total elements group and frames group will modify each other because they are just pointing
        # to the same object


        self.render_down_scope('global')



    def render_down_scope(self,id_:str):
        """Re-renders the object of the ID provided and all of it's children, 
        nothing else. Useful for only re-rendering a small scope"""
        initial_object = self.elements[id_]
        self.create_image_individual(initial_object)
        self.create_image_individual(self.getElementById('welcome'))
        # remove rendering in this function, this is meant to re-create images.
        # Will need to make a function that is dedicated to turning on and off frames
    

    ###############################################


    def create_image_individual(self, element:Element):
        """Re-renders the styles for an individual element"""

        # set defaults for computed styles
        computed_styles = {
            'width':0,
            'height':0,
            'rotation':0,
            'x':0,
            'y':0,
            'cx':0,
            'cy':0,
            'background':None,
            'corner-radius':0,
            'border':False,
            'border_color':None,
            'border_width':0,
        }
        element.computed_styles = {x:computed_styles[x] for x in computed_styles}
        if element.type == 'global':
            element.computed_styles['width'] = self.width
            element.computed_styles['height'] = self.height
            element.computed_styles['cx'] = self.width / 2
            element.computed_styles['cy'] = self.height / 2
            gbsurf = pg.Surface([self.width,self.height],pg.SRCALPHA)
            element.set_surface(gbsurf,gbsurf.get_rect())
            return
        buffer = {}
        for style in STYLES.keys():
            # This code is not meant to add to computed styles at all, rather to verify that all styles contain proper
            # types, structure, and attributes
            if style not in element.style: # grab default style instead of regular if not in element.style
                val = STYLES[style]['default']
                buffer[style] = val
                continue
            
            else:
                val:str = element.style[style].strip()
            
            acceptable_types = STYLES[style]['types']


            # Whether in or out continue with regular parsing
            not_chosen = 0
            if "number" in acceptable_types :
                try:
                    buffer[style] = float(val)
                except ValueError:
                    not_chosen += 1
            
            if "percentage" in acceptable_types:
                try:
                    maximum = STYLES[style]['max']
                    
                    if maximum in ['parentwidth','parentheight']: # If it depends on parent get that
                        
                        if buffer['position'] == 'relative':
                            parent = self.getElementById(element.parent_id) 
                        else:
                            parent = self.getElementById('global')

                        if maximum == 'parentwidth':
                            maximum = parent.computed_styles['width']

                        elif maximum == 'parentheight':
                            maximum = parent.computed_styles['height']
                    
                    buffer[style] = (float(val[:-1]) /100 ) * maximum
                except ValueError:
                    not_chosen += 1

            if "rgbvalue" in acceptable_types: # rgb val
                if len(re.findall("(\d+)",val)) != 3:
                    not_chosen += 1
                else:
                    colour = tuple(map(int,re.findall("(\d+)",val)))
                    buffer[style] = colour
                    

            
            if "text" in acceptable_types:
                if val not in STYLES[style]['accepted']:
                    not_chosen += 1
                else:
                    buffer[style] = val
                    

            if not_chosen == len(acceptable_types):
                log(f"{style} value {val} not valid",LogLevel.FATAL)
            


        if element.type in ['div', 'frame']:
            self.create_div_image(element, buffer)
        
        elif element.type in ['image']:
            ...

        elif element.type in ['text']:
            ...
        
        self.common_image_creation(element,buffer)

    ###############################################
    def common_image_creation(self,element:Element,buffer):
        # common - shared between all elements
        element.computed_styles['width'] = buffer['width']
        element.computed_styles['height'] = buffer['height']
        element.computed_styles['position'] = buffer['position']
        element.computed_styles['y'] = buffer['top']
        element.computed_styles['x'] = buffer['left']
        element.computed_styles['cx'] = buffer['left'] + buffer['width'] / 2
        element.computed_styles['cy'] = buffer['top'] + buffer['height'] / 2
        element.computed_styles['rotation'] = buffer['rotation']
        # end adding to  computed styles

        # get the surface
        surf = element.get_surface()['surf']
        if buffer['position'] == 'relative':
            parent = self.getElementById(element.parent_id) 
        else:
            parent = self.getElementById('global')
        surf = pg.transform.rotate(surf,parent.computed_styles['rotation']+buffer['rotation'])
        surf_rect = surf.get_rect(center = (
            element.computed_styles['cx'],
            element.computed_styles['cy']
        ))
        # set the surface to the rotated version
        element.set_surface(surf,surf_rect)
        self.blit_to_surf(surf,surf_rect)
        print(element.computed_styles)

    ##################################################

    def blit_to_surf(self,new_surf:pg.Surface,surf_rect:pg.Rect):
        self.surf.blit(new_surf,surf_rect)

    ###################################################

    def create_div_image(self, element:DivElement, buffer):
        print(buffer)

        # border
        border_space = 0
        border_color = (0,0,0,0)
        border = False
        if buffer['border-width'] != 0 and buffer['border-color'] is not None:
            border_space = buffer['border-width']
            border_color = [x for x in buffer['border-color']] + [buffer['opacity']]
            element.computed_styles['border'] = True
            border = True
        
        element.computed_styles['border-width'] = border_space
        element.computed_styles['border_color'] = border_color
        
        # background
        background_color = (0,0,0,0)
        if buffer['background'] is not None:
            background_color = [x for x in buffer['background']] + [buffer['opacity']]

        element.computed_styles['background'] = background_color
        # misc move misc to common function

        # surface images
        surf = pg.Surface([buffer['width'],buffer['height']],pg.SRCALPHA)
        if border:
            pg.draw.rect(surf,border_color,(0,0,buffer['width'],buffer['height']),border_radius=element.computed_styles['corner-radius'])
        
        pg.draw.rect(surf,background_color,
                     (border_space,border_space,
                      buffer['width']-(2*border_space),
                      buffer['height']-(2*border_space)
                      )
                     )
        surf_rect = surf.get_rect()
        element.set_surface(surf, surf_rect)
        

    


    ###############################################
    ###############################################

    def getElementById(self,id_:str) -> Element:
        element = self.elements.get(id_,None)
        if element is None:
            log(f"{id_} not found in getElementById function, returning None",LogLevel.WARNING)

        return element 

            








    







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


