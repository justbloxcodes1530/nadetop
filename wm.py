import pygame
import importlib
from ewmh import EWMH
from Xlib import X, display
from pygame._sdl2 import Window

disp = display.Display("Display")
ewmh = EWMH(disp)
root = disp.screen().root

sdl_window = Window.from_display_module()

root.change_attributes(event_mask=X.SubstructureNotifyMask)

pygame.init()

screen = pygame.display.set_mode((800, 600), pygame.NOFRAME)
pygame.display.set_caption("Frameless Window")
#pygame.display.set_window_position((0,0))
sdl_window.position = (0, 0)

screen = pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.NOFRAME)

screen.fill((0, 127, 255))

clock = pygame.time.Clock()
walking = True

while walking:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            walking = False

    pygame.display.flip()
    ev = disp.next_event()

    if ev.type == X.CreateNotify:
        print(f"New window created! ID: {hex(ev.window.id)}")
    elif ev.type == X.MapNotify:
        print(f"Window mapped (shown): {hex(ev.window.id)}")
    clock.tick(60)

pygame.quit()