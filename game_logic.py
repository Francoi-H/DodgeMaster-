import pygame

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 30)

    def move(self, dx):
        self.rect.x += dx
        self.rect.x = max(0, min(self.rect.x, 800 - self.rect.width))

    def draw(self, surface):
        pygame.draw.rect(surface, (0, 255, 0), self.rect)

class Block:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 50)
        self.y = y

    def move(self):
        self.rect.y += 5
        self.y = self.rect.y

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), self.rect)

def check_collision(player, block):
    return player.rect.colliderect(block.rect)
