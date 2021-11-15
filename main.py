import GameManager
import pygame
from GameComponents.p2p import *

VERSION = "0.0.1 alpha"


if __name__ == "__main__":
    print("===========")
    print(f"ASTEROIDS GAME verison {VERSION}")
    print("===========")
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
