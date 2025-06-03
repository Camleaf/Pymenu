from src.modules.compiler.pmscript import Compiler


compiler = Compiler('./tests/abcd.pym')

print(compiler.compiled)