import src as mu

compiler = mu.Compiler('./tests/abcd.pym')

print(' ')
print(*compiler.compiled,sep='\n')