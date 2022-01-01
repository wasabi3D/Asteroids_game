import GameManager
import pygame


VERSION = "0.0.1 alpha"


if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    GameManager.run()
