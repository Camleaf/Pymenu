"""
The pygame menu library that I made just for a school tanks game

Dependencies: 
- Python >= 3.11.9
- Pygame-ce >= 2.5.3

Built-in classes: 
    Window
    Grid
    __Object
    Label
    Button
    TextBox
    CheckBox
    Image
    Background
Use .__doc__ to learn more about each class

Check Readme.md for basic usage.
"""
import pygame as pg
from typing import NewType
from typing import Any
from copy import deepcopy
import os

# default color declarations just since it is a library
BLACK = (0,0,0)
WHITE = (255,255,255)
GRAY = (100,100,100)
BLUE = (0,0,255)
objectID = NewType('objectID', str)
objectRect = NewType('objectRect', list[float])

class Empty:
    ...

class Window:
    """
    Window(width, height) -> Window()
    Creates the window class, basis of the pymenu library\n
    Arguments:
        width: The 0 <= width integer of the menu window
        height: The 0 <= height integer of the menu window
    
    Returns:
        Window()

    Methods:
        create_link
        pack
        set_font_file
        set_placeholder_file
        __gridhandler
        mouseInteraction
        keyboardInteraction
        update_surf
        update_stat
        return_state
        save_frame
        load_frame
        flush
        surface
    Use .__doc__ for more info on methods
    """
    def __init__(self, width:int, height:int):
        

        self._default_font_file = os.path.join(f"{os.getcwd()}","gameFont.ttf")
        self._placeholder_file = os.path.join(f"{os.getcwd()}","Placeholder.png")
        self.sysfont = False
        self.__width = width
        self.__height = height
        self.__surf = pg.Surface([self.__width, self.__height],pg.SRCALPHA)
        self.__surf.fill((0,0,0,0))

        self.__collidables: dict[objectID, pg.Rect] = {}
        self._objects: dict[objectID, __Object] = {}
        self.__frames: dict[objectID, Any] = {}
        
        self.__links: dict[objectID, dict[str, list[objectID]]] = {}
        # objects are held in _objects for recalculations based on hover and data status
        # object rects are held in __collidables for mouse collision purposes

    def create_link(self, ID:str, linked_id:str=None, backward=True):
        """
        self.create_link(ID, linked_id, backward) -> None
        Creates a render link between multiple objects; Useful for re-rendering multiple dependent surfaces without refreshing entire frame\n
        Arguments:
            ID: Unique identifier of current object in current frame
            linked_id: Unique identifier of target object in current frame
            backward: Boolean value where True represents the target updating before the current, and False the other way around
        Returns:
            None
        """
        if linked_id == None: return

        if backward:
            self.__links[ID]["backward"].append(linked_id)
        else:
            self.__links[ID]["forward"].append(linked_id) # backward linked ID updates its images before the current surface, forward vice versa
        return None
    
    def pack(self, object, position: tuple[float]=(0,0), dimensions: tuple[int]=(0,0),ID = None) -> None:
        """
        self.pack(object, row, column, columnspan, ID) -> None
        Assign the object to the current frame; If object is Grid, sends subobjects to self.__gridhandler for processing\n
        Arguments:
            object: __Object derived class
            position: tuple[int] designating the (left,top) of the object
            dimensions: LEGACY FUNCTION; Generates dimensions based off image_rectl tuple[int] designating the (width,length) of the object
            ID: unique identifier of object; if none passed one is generated
        Returns:
            None
        """
        
        if object == "grid":
            self.__gridhandler(object, position)
        else:
            if ID is None: # add a identity creation func
                ID = _create_id(object)
            object: __Object = object

            self._objects[ID] = object
            if dimensions != (0,0): # if dimensions are given use them
                self.__collidables[ID] = pg.Rect(
                    position[0], 
                    position[1],
                    dimensions[0],
                    dimensions[1]
                )
            else: # otherwise use the rect of the image
                self.__collidables[ID] = object._image.get_rect()
                self.__collidables[ID].topleft = position
            self.__links[ID] = {"forward":[], "backward":[]}
            self.update_surf(ID)
    
    
    def set_font_file(self, file_path, sysfont=False):
        """
        self.set_font_file(file_path, sysfont) -> None
        Sets the current file for fonts, a font path or a system font\n
        Arguments:
            file_path: absolute file path to an image of types 'ttf'; if sysfont then can be any system font
            sysfont: boolean value determining whether to use a system font (True) or absolute file path (False)
        Returns:
            None
        """
        self._default_font_file = file_path
        if sysfont:
            self.sysfont = True
        else:
            self.sysfont = False
    
    def set_placeholder_file(self, file_path:str):
        """
        self.set_placeholder_file(file_path) -> None
        Sets the placeholder file for images without an image_path to an absolute path\n
        Arguments:
            file_path: absolute file path to an image of types 'jpg, png, jpeg'
        Returns:
            None
        """
        self._placeholder_file = file_path

    def __gridhandler(self, grid, position):
        """
        self.__gridhandler(grid, position) -> None
        Private method whichs handles self.pack operations for all subitems of a grid at a specific position\n
        Arguments:
            grid: Grid() object
            position: tuple[int] designating the (left,top) of the grid
        Returns:
            None

        """
        grid:Grid = grid
        
        for identity in grid._objects:
            identity:objectID

            # create positions based off the grid position and the row and column position
            object, (column_position, row_position, column_span) = grid._objects[identity]
            x = position[0] + column_position * grid._column_width
            y = position[1] + row_position * grid._row_height
            self.pack(object,(x,y), ID=identity)

    def mouseInteraction(self, position):
        """
        self.mouseInteraction(position) -> None
        Handles all interactions with objects which require interaction with the mouse\n
        Arguments:
            position: tuple[int] representing x and y position of cursor
        
        Collision effect based on object type: 
            label: continue
            textbox: activate or deactivate keyboard interactions depending on previous state
            func: call the method contained in the _func attribute
            val: change the activation to True or False depending on previous state
        
        Returns:
            None
        """
        for ID in self.__collidables:
            object = self._objects[ID]
            collidable = self.__collidables[ID]
            
            if object.type == "label": continue

            if not collidable.collidepoint(position[0],position[1]):

                if object.type == "textbox": 
                    object.activated = False
                    self.update_surf(ID)

                continue
            
            if object.type == "func":
                ret = self._objects[ID]._func(*self._objects[ID]._args)
                if not ret and ret is not None: # if the function returns false, it means it should not update the surface, however if it is none it should by default update
                    return
            elif object.type == "val":
                self._objects[ID].activated = True if not self._objects[ID].activated else False
            elif object.type == "textbox":
                self._objects[ID].activated = True
                self._objects[ID].cursor_pos = len(object.text)-1
            self.update_surf(ID)

            

    def keyboardInteraction(self, key):
        """
        self.keyboardInteraction(key) -> None
        Handles all interactions with activated keyboard-capable textbox objects
        Arguments:
            key: unicode input from pygame event.dict["unicode"] except in cases outlined below

        Character handling:
            '\ x08' represents Backspace
            '\ r' represents Return
            'lspr' represents Leftt Arrow
            'rspr' represents Right Arrow
            Any other keys use default unicode appearance
        Returns:
            None
        """

        for ID in self._objects:
            object = self._objects[ID]
            if object.type != "textbox": continue
            if not object.activated: continue

            new_text = object.text[:object.cursor_pos+1] + key + object.text[object.cursor_pos+1:]
            if key == "\x08":
                if len(object.text) != 0:
                    self._objects[ID].text = object.text[:object.cursor_pos] + object.text[object.cursor_pos+1:]
                    self._objects[ID].cursor_pos -= 1
            elif key == "\r":
                self._objects[ID].activated = False
            elif key == "lspr":
                self._objects[ID].cursor_pos -= 1
                if self._objects[ID].cursor_pos != 0:
                    self._objects[ID].cursor_pos %= len(object.text)
            elif key == "rspr":
                self._objects[ID].cursor_pos += 1
                if self._objects[ID].cursor_pos != 0:
                    self._objects[ID].cursor_pos %= len(object.text)
            elif object.input_type == "num" and key in "1234567890":
                
                self._objects[ID].text = new_text
                self._objects[ID].cursor_pos += len(key)
            elif object.input_type == "all":

                self._objects[ID].text = new_text
                self._objects[ID].cursor_pos += len(key)
            self.update_surf(ID)

    def update_surf(self, ID,bg_color:int=(0,0,0,0), update_bg:bool=True):
        """
        self.update_surf(ID, bg_color, update_bg) -> None
        updates the current render of the object inherited from __Object with unique identifier ID and any objects with a render link\n
        Arguments:
            ID: Unique string identifier of an Object on the current Frame
            bg_color: what to erase the object with before re-render
            update_bg: boolean to enable/disable erasing the background; In some cases can prevent overwriting images and stop artifacts on items with rounded corners
        Returns:
            None
        """
        collidable = self.__collidables[ID]
        orig_coords = collidable.topleft
        if update_bg:
            pg.draw.rect(self.__surf, bg_color, collidable)
        self._objects[ID].render()
        self.__collidables[ID] = self._objects[ID]._image.get_rect()
        self.__collidables[ID].topleft = orig_coords

        for linked_ID in self.__links[ID]["backward"]: #update backward linked ids
            self.update_surf(linked_ID, update_bg=False)

        self.__surf.blit(self._objects[ID]._image,collidable)

        for linked_ID in self.__links[ID]["forward"]: #update forward linked ids
            self.update_surf(linked_ID, update_bg=False)
    

    def update_stat(self,ID,activated:bool=None,text:str=None, command=None, args:tuple[Any]=None, image_path:str=None):
        """
        self.update_stat(ID,activated,text,command,args,image_path) -> None:
        Updates the state of an object inherited from __Object with unique string identifier ID\n
        Arguments:
            ID: Unique string identifier of an Object on the current Frame
            activated: Keyword argument representing activation state of the object
            text: Keyword argument representing the text value of the object
            command: Keyword argument representing the object method
            args: Keyword argument representing the args passed to the object method on activation
            image_path: Keyword argument representing image_path of the object
        Returns:
            None
        """
        if activated is not None:
            self._objects[ID].activated = activated
        if text is not None:
            self._objects[ID].text = text
        if command is not None:
            if not callable(command):
                raise Exception(f"Value {command} is not a callable method. Try removing the brackets from the passed function")
            self._objects[ID]._func = command
        if args is not None:
            self._objects[ID]._args = args
        
        if image_path is not None:
            self._objects[ID].image_path = image_path

    def return_state(self, ID:str):
        """
        self.return_state(ID) -> Empty__attr__{activated:bool, text:str, command:method, args:tuple[int], image_path=''}
        Returns the default state vars of the object with a given ID\n
        Arguments:
            ID: Unique string identifier of an Object on the current Frame
        Returns:
            class { activated:bool, text:str, command:method, args:tuple[int], image_path='' 
        """
        state_export = Empty()
        object = self._objects[ID]
        state_export.activated = object.activated
        state_export.text = object.text
        state_export.command = object._func
        state_export.args = object._args
        state_export.image_path = object.image_path
        return state_export

    def save_frame(self,ID:str,flush:bool = True):
        """
        self.save_frame(ID, flush) -> None
        Saves the current frame by ID and can be accessed by future loads
        Arguments:
            ID: New unique string identifier assigned to current Window Frame
            flush: boolean value determining if the current frame should be flushed after saving
        Returns:
            None
        """

        self.__frames[ID] = { # if inheritance issues show up just put copies on everything
            "collidables" : self.__collidables, #{x:self.__collidables[x] for x in self.__collidables}, 
            "objects" : self._objects, #{x:self._objects[x] for x in self._objects},
            "surface": self.__surf,
            "links": self.__links
        }
        if flush:
            self.flush()
            

    def delete_frame(self, ID:str):
        """
        self.delete_frame(ID) -> None
        Deletes frame ID\n
        Arguments:
            ID: Unique string identifier of a Window Frame
        Returns:
            None
        """
        del self.__frames[ID]

    def load_frame(self,ID:str):
        """
        self.load_frame(ID) -> False
        Loads frame ID as the current Window Frame\n
        Arguments:
            ID: Unique string identifier of a Window Frame
        Returns:
            False
        """
        if ID not in self.__frames:
            raise Exception(f"No frame ID {ID} exists")
        frame = self.__frames[ID]
        self.__collidables = frame['collidables']
        self._objects = frame['objects']
        self.__surf = frame['surface']
        self.__links = frame['links']
        return False


    def flush(self):
        """
        self.flush() -> None
        Flushes the current frame, removing all data from it. Data in stored frames are unaffected.\n
        Returns:
            None
        """
        self.__surf = pg.Surface([self.__width, self.__height],pg.SRCALPHA)
        self.__surf.fill((0,0,0,0))

        self.__links = {}
        self.__collidables = {}
        self._objects = {}


    def surface(self):
        """
        self.surface() -> pygame.Surface()
        Return the surface object representing the Window object\n
        Returns:
            pygame.Surface()
        """
        return self.__surf
    
class Grid:
    """
    Grid(columns, rows, columnwidth, rowheight) -> Grid()
    Initialize a grid object with a static number of rows, columns, with static and uniform height\n
    Arguments:
        columns: int > 0
        rows: int > 0
        columnwidth: int > 0
        rowheight: int > 0

    Returns:
        Grid()

    Methods:
        pack: add object inherited from __Object to Grid
    """
    def __init__(self, columns:int=1, rows:int=1, columnwidth:float = 10, rowheight:float = 10):
        # if an object doesn't fit in its defined grid space crop it

        self._column_count = columns
        self._row_count = rows
        self._column_width = columnwidth
        self._row_height = rowheight
        # work on everything else next then come back to this

        self._objects:dict[objectID, list] = {}
        # list is defined as [object, (col_pos, row_pos, span)]

    def pack(self, object, row:int = 0, column:int = 0, columnspan:int = 1, ID:str=None) -> None:
        """
        self.pack(object, row, column, columnspan, ID) -> None
        Adds an object to a slot in the grid\n
        Arguments:
            object: __Object derived class
            row: int from 0 to number of rows - 1
            column: int from 0 to number of columns - 1
            columnspan: int from 1 to number of columns
            ID: unique identifier of object; if none passed one is generated
        Returns:
            None
        """
        object:__Object = object
        if object == "grid":
            raise Exception("Grid object attempted to pack other Grid object")

        if row < 0 or row > self._row_count-1 or column < 0 or column > self._column_count-1:
            raise Exception("Row or column greater than defined limit of Grid object")
        
        if columnspan > self._column_count or columnspan < 1:
            raise Exception("Columnspan either greater than number of columns, is zero, or is negative")
        if ID is None:
            ID = _create_id(object)
        self._objects[ID] = [object, (column, row, columnspan)]
        



    def __eq__(self,other):
        """
        self.__eq__(other) -> "object"
        Arguments:
            other: any string
        Returns:
            other == "grid"
        """
        return other == "grid"

    def __str__(self):
        """
        self.__str__() -> "grid"
        Returns:
            "grid"
        """
        return "grid"

class __Object:
    """
    __Object(window, value=None, text='', command=None, args=None, image_path='') -> __Object()
    Default object class which all sub-objects inherit from\n
    Arguments:
        window: Window() object
        value: starting activation setting
        text: string text value
        command: method to execute; Incompatible with value
        args: arguments passed to the command
        image_path: string image path
    
    Returns:
        __Object
    
    Methods:
        render
        __str__
    """

    def __init__(self, window, value:bool=None, text:str = '', command=None, args:tuple[Any]=None, image_path:str = ''):
        self._image = pg.Surface([0,0],pg.SRCALPHA)
        self.activated = value
        self._func = command
        self._args = args
        self.text = text
        self.window:Window = window
        self.image_path = image_path

        if value is not None and command is not None:
            raise Exception("Objects can not be defined with both a value and a command")
        elif value is not None:
            self.type = "val"
        elif command is not None:
            self.type = "func"
        else:
            self.type = "label"

    def render(self) -> None:
        """Empty function to fill in in each individual object"""
        ...
        # add the color purple when this finishes, as all indiv functions will need their own render func


    def __str__(self):
        """
        self.__str__() -> "object"
        Returns:
            "object"
        """
        return "object"    
        
    
def _create_multiline_text(window:Window, text:str, padding=10, size=20, width=100, color: tuple[int]=BLACK, font_file:str=None, sysfont:bool=False) -> pg.Surface:
    """
    _create_multiline_text(window, text, padding=10, width=100, color=(0,0,0), font_file=None, sysfont=False) -> pygame.Surface
    Creates a pygame.Surface object containing the text.\n
    Arguments:
        window: Window() object
        font_file: absolute path of a .ttf file; defaults to window._default_font_file; if sysfont the name of the font
        sysfont: a boolean value determining the usage of a .ttf or a system font
        size: font size of the text   width: maximum width of the text before a newline is created; -1 scales the width to the text
        padding: padding in pixels afforded to each edge of the text
        color: the RGB color value of the text
    Returns:
        pygame.surface() object
    """

    # this won't run very much so the overhead can be greater
    if font_file is None:
        font_file = window._default_font_file
    if sysfont:
        font = pg.font.SysFont(font_file,size)
    else:
        font = pg.font.Font(font_file,size=size)
    if width == -1:
        width = padding//2
    surf = font.render(text,True, color, wraplength=width- padding//2)
    surf.convert_alpha()
    return surf

__past_ids = []
def _create_id(object:__Object) -> objectID:
    """
    _create_id(object) -> objectID:str
    Creates a unique object identifier\n
    Arguments:
        object: object inherited from __Object class
    Returns:
        objectID:str
    """
    id_suffix = 0
    object_type = str(object)

    while (id := object_type+str(id_suffix)) in __past_ids: 
        id_suffix += 1
    __past_ids.append(id)
    return id
        

# define custom types
grid = NewType('grid', Grid)
