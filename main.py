import GameManager
import pygame
from GameComponents.p2p import *


if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    GameManager.run()
    # def pr(msg):
    #     print("\n", msg)

    # rec = Receive(8890, pr)
    # rec.start()

    # send = Send("10.64.161.31", 8890)
    # while True:
    #     send.set_message(input())
    #     send.run()
