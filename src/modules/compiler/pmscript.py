from typing import Self, Any
import json
from .logging import log, LogLevel, reset_log

# great youtube series: https://www.youtube.com/watch?v=3PW552YHwy0&list=PLZQftyCk7_SdoVexSmwy_tBgs7P0b97yD&index=5

##################
# Constants
##################

EXIT = False
CONTINUE = True

##################
# TOKENS
##################

ILLEGAL_DATA_NAMESPACES = [">",";","{","}","\'","\"","=","#","<"]
KEYWORDS = ['class','id','style']
RESERVED_NAMEVALUES = ['GLOBAL']

T_ADVANCE = 'T_ADVANCE'
T_SEMICOLON = 'T_SEMICOLON'
T_NAMEVALUE = 'T_NAMEVALUE'
T_DATAVALUE = 'T_DATAVALUE'
T_LBRCK = 'T_LBRCK'
T_RBRCK = 'T_RBRCK'
T_FSLASH = 'T_FSLASH'
T_EQ = 'T_EQ'
T_KW = 'T_KW'
T_BACK = 'T_BACK'

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

    def get_type(self):
        return self.type
    


##################
# Syntax Tree
##################


    # Structure of syntax elements. Token sep by $. Repeatable options keywords by ? then sep by /

    # Options can be filled with 'IGNORE', 'ANY', 'NONE' for keywords

    # For options, ASSIGN keyword can be used to take a datavalue and assign to a namevalue

SYNTAX_TREE = { 
    
    ##############################################################
    "OPEN_ELEMENT":"T_ADVANCE$T_NAMEVALUE?T_KW$T_EQ$T_DATAVALUE",
    "CLOSE_ELEMENT":"T_ADVANCE$T_FSLASH$T_NAMEVALUE?NONE",
    "COMMENT":"T_FSLASH$T_FSLASH?ANY",
    "IMPORT":"T_SEMICOLON$T_SEMICOLON$T_NAMEVALUE$T_BACK$T_DATAVALUE?NONE",
}
##################
# ELEMENTS
##################
_past_ids = []

class Element:
    type:str
    parent_id:str

    def __init__(self, type_:str, parent_id:str|None, style:dict[str,str]={}, id_:str=None, value:str='', scoped_styles:dict={}):
        self.type = type_
        self.id = id_
        self.parent_id:str = parent_id
        self.children = []
        self.style = style
        self.value = value
        self.scoped_styles = scoped_styles

        if not self.id:
            self.id = _create_id(self)
        else:
            _past_ids.append(self.id)

    def __repr__(self):
        # return f'ID: {self.id} ; TYPE: {self.type} ; Parent_ID: {str(self.parent_id)} ; STYLE_TAGS: {self.style}'
        return f'{self.type}'

    def __str__(self):
        return f'{self.id}'
def _create_id(object:Element):

    id_suffix = 0
    object_type = object.type

    while (id := object_type+str(id_suffix)) in _past_ids: 
        id_suffix += 1
    _past_ids.append(id)
    return id

##############################################################

class Error():
    def __init__(self,text:str='Error'):
        log(text,LogLevel.FATAL)
        super().__init__(f"{text}")

class IllegalCharError(Error):
    def __init__(self, line_number:int=None, line:str='', char:str=''):
        text = f"Illegal character `{char}`"
        text = f"\n\n\nLine {line_number}| \"    {line}    \"    >>  {text}"
        super().__init__(text)

class StringNotEnded(Error):
    def __init__(self, line_number:int=None, line:str=''):
        text = f"\n\n\nLine {line_number}| \"    {line}    \"    >>  String not Ended"
        super().__init__(text)

class SyntaxIncorrect(Error):
    def __init__(self, line_number:int=None, line:str='', message='Syntax Error'):
        text = f"\n\n\nLine {line_number}| \"    {line}    \"    >>  {message}"
        super().__init__(text)

class ImportFailed(Error):
    def __init__(self, line_number:int=None, line:str='', path:str=''):
        text = f"\n\n\nLine {line_number}| \"    {line}    \"    >>  Import Error: Import of `{path}` failed. Try using absolute imports from the CWD"
        super().__init__(text)

class NameSpaceError(Error):
    def __init__(self, line_number:int=None, line:str='', namevalue=''):
        text = f"\n\n\nLine {line_number}| \"    {line}    \"    >>  Namespace Error: {namevalue} reserved for system use"
        super().__init__(text)
##################
# LEXER
##################

# For parent/ Children, use a stack showing what the current parent is, so that switching back and forth is easy


class Lexer:
    text:str
    current_char:str
    current_build:str
    mode:list[Any]
    tokens:list[Token] = []
    parent:Element

    def __init__(self):
        ...
    
    def new_line(self,line:str, index:int, parent:Element = None):
        self.text = line.strip()
        self.parent = parent
        self.index = index
        self.current_build = ''
        self.mode = [self.default_search] # A stack for me to easily switch between different search patterns
        self.tokens = []
        if self.text: 
            self.make_tokens()
    
    def make_tokens(self):
        for i, char in enumerate(self.text):
            
            self.mode[-1](char) # The top of the stack is what is executed

        if self.mode[-1] == self.value_search: # This logic is to capture any components at the end of the string
            raise StringNotEnded(self.index, self.text)
        
        elif self.current_build != '':
            self.tokens.append(Token(T_NAMEVALUE,self.current_build))

    ##############################################################

    def flush_build(self):
        if self.current_build in KEYWORDS:
            self.tokens.append(Token(T_KW,self.current_build))
            self.current_build = ''
        elif self.current_build != '':
            self.tokens.append(Token(T_NAMEVALUE,self.current_build))
        self.current_build = ''

    def default_search(self,char:str):
        if char == ' ' or char == '\t':
            self.flush_build()

        
        elif char == '\'':
            self.current_build = ''
            self.mode.append(self.value_search)
        

        elif char == '>': # In The future I could probably make this way more concise but for now it works
            self.flush_build()
            self.tokens.append(Token(T_ADVANCE,char))
            
        
        elif char == ';':
            self.flush_build()
            self.tokens.append(Token(T_SEMICOLON,char))


        elif char == '[':
            self.flush_build()
            self.tokens.append(Token(T_LBRCK,char))


        elif char == ']':
            self.flush_build()
            self.tokens.append(Token(T_RBRCK,char))


        elif char == '=':
            self.flush_build()
            self.tokens.append(Token(T_EQ,char))


        elif char == '/':
            self.flush_build()
            self.tokens.append(Token(T_FSLASH,char))

        elif char == '<':
            self.flush_build()
            self.tokens.append(Token(T_BACK,char))


        else:
            self.current_build += char

    ##############################################################

    def value_search(self, char:str):
        if char == '\'':
            self.tokens.append(Token(T_DATAVALUE,self.current_build))
            self.current_build = ''
            self.mode.pop()
        elif char in ILLEGAL_DATA_NAMESPACES:
            raise IllegalCharError(self.index,self.text, char)
        else:
            self.current_build += char
            
##################
# Compiler
##################

# Uses lexer as subcategory
class Compiler:
    lexer:Lexer
    parent_stack:list[Element]
    compiled:list[Element]


    def __init__(self, path:str): # Use token patterns to figure out what type the line is
        self.lexer = Lexer()
        self.global_scope = Element(type_="GLOBAL",id_="GLOBAL", parent_id=None,style={})
        self.parent_stack = [self.global_scope]
        self.compiled = [self.global_scope]
        self.path = path
        self.uncompiled = []
        self.index = 0
        self.syntax_tree = dict()
        self.parse_syntax_tree()
        # print(self.syntax_tree)
        self.extract_path(path,0, '')
        self.compile()
        # print(*self.uncompiled,sep='\n')

    ##############################################################

    def parse_syntax_tree(self):

        syntax_keys = list(SYNTAX_TREE.keys())
        for key in syntax_keys:
            raw_syntax = SYNTAX_TREE[key]
            temp = raw_syntax.split('?')
            if len(temp) == 1:
                raw_identifier, raw_options = temp[0],''
            elif len(temp) > 2:
                raise Error('? Identifier found multiple times in syntax Tree')
            else:
                raw_identifier, raw_options = temp
            identifier_structure = raw_identifier.split('$')
            options_structure = raw_options.split('$')
            if len(options_structure) == 1 and options_structure[0] == '':
                options_structure = []
            self.syntax_tree[key] = {
                "identifier":identifier_structure,
                "options":options_structure
            }
            



    def extract_path(self,path:str, insert_index:0,line):
        try:
            with open(path,'r') as f:
                self.uncompiled = self.uncompiled[:insert_index+1] + f.read().split('\n') + self.uncompiled[insert_index+1:]
        except FileNotFoundError:
            raise ImportFailed(self.index, line)
            
    ##############################################################

    def compile(self):
        while self.index < len(self.uncompiled):
            line = self.uncompiled[self.index]


            self.lexer.new_line(line,self.index+1)
            if not self.lexer.tokens: 
                self.index += 1
                continue

            syntax_type = self.match_tokens(self.lexer.tokens,line)
            
            
            if syntax_type == "COMMENT":
                ...
            
            elif syntax_type == "IMPORT":
                self.handle_import(self.lexer.tokens,line)
            
            elif syntax_type == "OPEN_ELEMENT":
                self.handle_open_element(self.lexer.tokens,line,syntax_type)
            
            elif syntax_type == "CLOSE_ELEMENT":
                self.handle_close_element(self.lexer.tokens,line,syntax_type)
            
            else:
                raise SyntaxError()
            print(self.parent_stack, "\n",)

            self.index += 1
    
    ##############################################################

    def match_tokens(self, tokens:list[Token],line):

        syntax_type = ''
        for key in self.syntax_tree:

            for i,tok_type in enumerate(self.syntax_tree[key]['identifier']):
                
                if tokens[i].get_type() != tok_type:
                    
                    break

                if i == len(self.syntax_tree[key]['identifier'])-1:
                    syntax_type = key

        if not syntax_type:
            raise SyntaxIncorrect(self.index,line,"Syntax Error. Perhaps you forgot an identifier?")

        # print(syntax_type)
        return syntax_type
    
    ##############################################################

    def handle_import(self,tokens:list[Token],line):
        import_type = tokens[2]
        path = tokens[4]
        # import type and path are static always so I can assign them like that

        self.uncompiled[self.index] = ''
        if import_type.value == "markdown":
            self.extract_path(path.value,self.index,line)

        elif import_type.value == "styles":
            try:
                with open(path.value,'r') as f:
                    raw_styles = json.load(f)
            except FileNotFoundError:
                raise ImportFailed(self.index, line)

            # This is to scope classes to their specific zones, so that styles can be overwritten in certain scopes
            for key in raw_styles:
                self.parent_stack[-1].scoped_styles[key] = raw_styles[key]
                
    ##############################################################

    
    def handle_open_element(self,tokens:list[Token],line:str,syntax_type:str):
        tok_types = []
        for tok in tokens:
            tok_types.append(tok.get_type())
        
        # some basic reserved namespace stuff
        type_ = tokens[1].value
        
        if type_ in RESERVED_NAMEVALUES: # Check to make sure the user isn't overwriting global or something
            raise NameSpaceError(self.index,line,type_)
        
        options_structure = self.syntax_tree[syntax_type]['options']
        type_search_index = 0
        seen_keywords = []

        datapoints = {
            "class":'',
            "style":'',
            "id":''
        }
        cur_kw:str = ''
        cur_val:str = ''
        for i,tok in enumerate(tokens[2:]): # past the element declaration
            if tok.get_type() != options_structure[type_search_index]: # Raise error if structure is not followed
                raise SyntaxIncorrect(self.index, line, f"Syntax Error. {tok.get_type()} not in right place or not supported in OPTIONS structure {options_structure}.")
            
            # Keyword checking
            if tok.get_type() == T_KW:
                if tok.value in seen_keywords: 
                    raise SyntaxIncorrect(self.index, line, f"Syntax Error. {tok.get_type()} used twice.")
                cur_kw = tok.value
                seen_keywords.append(tok.value)

            # Datavalue checking
            if tok.get_type() == T_DATAVALUE:
                cur_val = tok.value

            # structure completion / increment
            type_search_index += 1 # increment structure
            type_search_index %= len(options_structure) # repeat structure on completion

            if type_search_index == 0:
                if not cur_kw or not cur_val:
                    raise SyntaxIncorrect(self.index,line,f"Syntax Error. Error with OPTION values")

                datapoints[cur_kw] = cur_val
                cur_kw,cur_val = '',''

        
        if type_search_index != 0: # Raise error if structure is unfinished
            raise SyntaxIncorrect(self.index, line, f"Syntax Error. OPTIONS structure {options_structure} not completed, missing elements {options_structure[type_search_index:]}.")
        # print(datapoints)


        style = {}
        if datapoints["class"]:
            for element in self.parent_stack[::-1]: # reverse iterate to find the most recently scope version of the class
                if datapoints["class"] in element.scoped_styles:
                    
                    scoped_class = element.scoped_styles[datapoints['class']]
                    for item in scoped_class:
                        style[item] = scoped_class[item]
                    break
        
        if datapoints["style"]: # split up the styles into keypairs
            for item in datapoints["style"].split('/'):
                raw = item.split(':')

                if len(raw) > 2 or len(raw) < 2:
                    raise SyntaxIncorrect(self.index,line,f"`:` Symbol must act as a divider between key:value pairs, and must exist.")

                key,value = raw
                style[key] = value
        
        if not datapoints['id']:
            datapoints['id'] = None

        current = Element(type_,self.parent_stack[-1].id,style,datapoints['id'],value='')
        self.parent_stack[-1].children.append(current)
        self.parent_stack.append(current)
        self.compiled.append(current)


    ##############################################################
        
        
    def handle_close_element(self,tokens:list[Token],line:str,syntax_type:str):
        if len(tokens) > 3:
            return SyntaxIncorrect(self.index,line,f"CLOSE_ELEMENT argument does not take options")
        
        type_ = tokens[2].value

        if type_ in RESERVED_NAMEVALUES: # Check to make sure the user isn't overwriting global or something
            raise NameSpaceError(self.index,line,type_)

        if self.parent_stack[-1].type != type_:
            raise SyntaxIncorrect(self.index, line, f"CLOSE ELEMENT argument in wrong scope. Try checking if another element is still open during this call.")
        
        self.parent_stack.pop()


# Todo. Add text piece support, button support, textbox support, reactive state support