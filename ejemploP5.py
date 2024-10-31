# instalar con 'pip install p5'
from p5 import *

def setup():
    size(400, 400)

def draw():
    background(255)
    ellipse(mouse_x, mouse_y, 50, 50)

run()
