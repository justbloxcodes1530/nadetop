import pygame

frame = pygame.display.set_mode((800, 600), pygame.NOFRAME)
pygame.display.set_caption("Frameless Window")
pygame.display.set_window_position((100,100))

clock = pygame.time.Clock()
walking = True

while walking:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            walking = False

    mouse_pos = mouse_pos if pygame.mouse.get_pressed()[0] else pygame.mouse.get_pos()

    if pygame.draw.rect(frame, (0, 127, 255), pygame.Rect(0, 0, frame.get_width(), 32)).collidepoint(mouse_pos):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        if pygame.mouse.get_pressed()[0]:
            pygame.display.set_window_position((pygame.mouse.get_pos(True)[0] - mouse_pos[0], pygame.mouse.get_pos(True)[1] - mouse_pos[1]))
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()