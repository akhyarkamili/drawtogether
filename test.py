import pygame
import sys

pygame.init()

WHITE = (255, 255, 255)
width = 700
height = 400
screen = pygame.display.set_mode([width, height])
clock = pygame.time.Clock()

while True:
    clock.tick(2)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    screen.fill(WHITE)
    pygame.display.flip()
