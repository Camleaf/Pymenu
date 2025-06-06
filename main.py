import src as pm
import sys,pygame as pg
from pygame.locals import *
View = pm.initialize('./tests/abcd.pym', [400,400])
pg.init()
clock = pg.Clock()
display= pg.display.set_mode((400,400),pg.SRCALPHA)



while True:
    display.fill((0,0,0))
    for event in pg.event.get():
        if event.type == QUIT:
            pg.quit()
            sys.exit()

    display.blit(View.surf,(0,0))
    pg.display.flip()
    clock.tick(24)
    