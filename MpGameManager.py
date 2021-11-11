from collections import Sequence

import GameComponents as Gc
from GameComponents.locals import *
import pygame
from pygame.locals import *
import os
import sys
import json
import threading as th
import random


def get_turn_and_accel_state(pressed) -> tuple[bool, bool]:
    angle_clwise = pressed[K_RIGHT] or pressed[K_d]
    angle_counter_clwise = pressed[K_LEFT] or pressed[K_a]
    t_ = None if not angle_clwise ^ angle_counter_clwise else angle_clwise
    a_ = pressed[K_w] or pressed[K_UP]
    return t_, a_


class Client:
    def __init__(self, screen, host_ip, name):
        self.screen: pygame.Surface = screen
        self.host_ip = host_ip
        self.name = name
        self.receive = Gc.Receive(DEFAULT_PORT, self.on_response)
        self.connection_state = ""
        self.game_started = False
        self.running = False
        self.other_players: dict[str, Gc.MpPlayer] = {}
        self.nametags: dict[str, Gc.TextUI] = {}
        self.font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 12)
        self.font_b = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 20)

        self.receive.start()


    def loop(self) -> str:
        self.try_join()

        connecting_txt = Gc.TextUI(self.font_b, DEFAULT_TEXT_COL, "Connecting...", Gc.Coordinate(100, 600))
        connecting_txt.blit(self.screen)
        pygame.display.update()
        while self.connection_state == "":
            pass
        self.screen.fill(BG_COLOR, connecting_txt.rect)
        if self.connection_state == COM_GAME_FULL:
            connecting_txt.set_text("Connection error: GAME FULL. ")
            return COM_GAME_FULL

        connecting_txt.set_text("Waiting for start...")
        connecting_txt.blit(self.screen)
        pygame.display.update()
        while not self.game_started:
            pass
        self.running = True

        host_send = Gc.Send(self.host_ip, DEFAULT_PORT)
        me = Gc.MpPlayer((random.randint(0, 600), random.randint(0, 600)), Gc.ml.dat[PLAYER], self.name)
        mynametag = Gc.TextUI(self.font, DEFAULT_TEXT_COL, self.name,
                                   Gc.Coordinate(me.cords.x + NAMETAG_OFFSET[0], me.cords.y + NAMETAG_OFFSET[1]))
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            pressed = pygame.key.get_pressed()
            turn, accel = get_turn_and_accel_state(pressed)
            me.update(accel, turn)
            self.screen.fill(BG_COLOR)

            tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_PLAYER_POS, f"{me.cords.x}x{me.cords.y}x{me.angle}x{Gc.get_local_ip()}", self.name)
            host_send.set_message(json.dumps(tmp_msg.d()))
            s: Gc.MpPlayer
            for ip, s in self.other_players.items():
                self.nametags[ip].set_pos(Gc.Coordinate(s.cords.x + NAMETAG_OFFSET[0], s.cords.y + NAMETAG_OFFSET[1]))
                s.blit(self.screen)
                self.nametags[ip].blit(self.screen)

            me.blit(self.screen)
            mynametag.set_pos(Gc.Coordinate(me.cords.x + NAMETAG_OFFSET[0], me.cords.y + NAMETAG_OFFSET[1]))
            mynametag.blit(self.screen)
            host_send.run()
            pygame.display.update()
            pygame.time.Clock().tick(UPD)

    def try_join(self):
        tmp_send = Gc.Send(self.host_ip, DEFAULT_PORT)
        tmp_msg = Gc.GameCom(COM_PREP, COM_REQUEST_JOIN, self.name, "")
        tmp_send.send_message(json.dumps(tmp_msg.d()))

    def on_response(self, msg, addr):
        received = Gc.GameCom("", "", "", "")
        received.__dict__ = json.loads(msg)
        if received.info_type == COM_PREP:
            if received.msg == COM_GAME_START:
                self.game_started = True
            else:
                self.connection_state = received.msg
        elif received.info_type == COM_GAMEDATINFO:
            name = received.other
            if received.msg == COM_PLAYER_POS:
                sp = received.value.split('x')
                x, y, a, ip = int(float(sp[0])), int(float(sp[1])), int(float(sp[2])), sp[3]
                if ip not in self.other_players.keys():
                    self.other_players.setdefault(ip, Gc.MpPlayer((x, y), Gc.ml.dat[PLAYER], name))
                    p = self.other_players[ip]
                    self.nametags.setdefault(ip, Gc.TextUI(self.font, DEFAULT_TEXT_COL, p.name,
                                                           Gc.Coordinate(p.cords.x + NAMETAG_OFFSET[0],
                                                                         p.cords.y + NAMETAG_OFFSET[1])))
                self.other_players[ip].set_pos((x, y), a)


class Host:
    def __init__(self, screen, num_players, name):
        self.screen: pygame.Surface = screen
        self.host_receive = Gc.Receive(DEFAULT_PORT, self.on_rec_from_client)
        self.num_players = num_players
        self.players_name = []
        self.players = []
        self.ips = []
        self.running = False
        self.players_sprites: dict[str, Gc.MpPlayer] = {}
        self.nametags: dict[str, Gc.TextUI] = {}
        self.send_objects: list[Gc.Send] = []
        self.name = name
        self.asteroids = Gc.AstGroup()
        self.small_asteroids = Gc.objects.AstGroup()
        self.bullets = Gc.BulletGroup()
        self.font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 12)

        self.players_name.append(name)
        self.host_receive.start()

    def on_rec_from_client(self, msg_, addr):
        received = Gc.GameCom("", "", "", "")
        received.__dict__ = json.loads(msg_)
        if received.info_type == COM_PREP:
            print("REQUEST!!!!")
            tmp_send = Gc.Send(addr[0], DEFAULT_PORT)
            if len(self.players) < self.num_players:
                self.players_name.append(received.value)
                self.players.append(received.value)
                self.ips.append(addr[0])
                tmp_msg = Gc.GameCom(COM_PREP, COM_CON_SUCCESS, "", "")
                tmp_send.send_message(json.dumps(tmp_msg.d()))
            else:
                tmp_send.set_message(json.dumps((COM_PREP, COM_GAME_FULL)))
        elif received.info_type == COM_GAMEDATINFO:
            name = received.other
            if received.msg == COM_PLAYER_POS:
                sp = received.value.split('x')
                x, y, a, ip = int(float(sp[0])), int(float(sp[1])), int(float(sp[2])), sp[3]
                if addr[0] in self.players_sprites.keys():
                    self.players_sprites[addr[0]].set_pos((x, y), a)

    def loop(self):
        # Wait for players
        font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 15)
        wait_txt = Gc.TextUI(font, DEFAULT_TEXT_COL, "Waiting for players...", Gc.Coordinate(SCREEN_DIMENSION[0] / 2,
                                                                                              SCREEN_DIMENSION[1] / 2))
        ip_txt = Gc.TextUI(font, DEFAULT_TEXT_COL, f"Give this ip to your friends: {Gc.get_local_ip()}",
                           Gc.Coordinate(50, 50))

        players_txt = []
        pl_txt_cord = Gc.Coordinate(100, 110)
        for i in range(self.num_players):
            players_txt.append(Gc.TextUI(font, DEFAULT_TEXT_COL, f"Player {i + 1}: ", Gc.Coordinate(pl_txt_cord.x,
                                                                                                    pl_txt_cord.y)))
            pl_txt_cord.update(0, 20, additive=True)

        while len(self.players_name) < self.num_players:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            self.screen.fill(BG_COLOR)
            for i, txt in enumerate(players_txt):  # update text
                if i + 1 > len(self.players_name):
                    break
                txt.set_text(f"Player {i + 1}: {self.players_name[i]}", pos=txt.pos)

            # >>>> UPDATE >>>>
            for txt in players_txt:
                txt.blit(self.screen)
            wait_txt.blit(self.screen)
            ip_txt.blit(self.screen)
            pygame.display.update()

        self.running = True
        for ip in self.ips:
            tmp_send = Gc.Send(ip, DEFAULT_PORT)
            tmp_msg = Gc.GameCom(COM_PREP, COM_GAME_START, "", "")
            tmp_send.send_message(json.dumps(tmp_msg.d()))

        me = Gc.Player((SCREEN_DIMENSION[0] / 2, SCREEN_DIMENSION[1] / 2), Gc.ml.dat[PLAYER])
        mynametag = Gc.TextUI(self.font, DEFAULT_TEXT_COL, self.name,
                              Gc.Coordinate(me.cords.x + NAMETAG_OFFSET[0], me.cords.y + NAMETAG_OFFSET[0]))
        for i, ip in enumerate(self.ips):
            self.players_sprites.setdefault(ip, Gc.MpPlayer((0, 0), Gc.ml.dat[PLAYER], self.name[i]))
            self.send_objects.append(Gc.Send(ip, DEFAULT_PORT))
            p = self.players_sprites[ip]
            self.nametags.setdefault(ip, Gc.TextUI(self.font, DEFAULT_TEXT_COL, p.name,
                                                   Gc.Coordinate(p.cords.x + NAMETAG_OFFSET[0],
                                                                 p.cords.y + NAMETAG_OFFSET[1])))

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            self.screen.fill(BG_COLOR)
            pressed = pygame.key.get_pressed()
            turn, accel = get_turn_and_accel_state(pressed)
            me.update(accel, turn)

            for ip, p in self.players_sprites.items():
                p.blit(self.screen)
                self.nametags[ip].set_pos(Gc.Coordinate(p.cords.x + NAMETAG_OFFSET[0],
                                                        p.cords.y + NAMETAG_OFFSET[1]))
                self.nametags[ip].blit(self.screen)

            s: Gc.Send
            for s in self.send_objects:
                for ip, sprite in self.players_sprites.items():
                    if ip == s.address:
                        continue
                    tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_PLAYER_POS,
                                         f"{sprite.cords.x}x{sprite.cords.y}x{sprite.angle}x{ip}", sprite.name)
                    s.set_message(json.dumps(tmp_msg.d()))
                    s.run()

                tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_PLAYER_POS,
                                     f"{me.cords.x}x{me.cords.y}x{me.angle}x{Gc.get_local_ip()}", self.name)
                s.set_message(json.dumps(tmp_msg.d()))
                s.run()

            me.blit(self.screen)
            mynametag.set_pos(Gc.Coordinate(me.cords.x + NAMETAG_OFFSET[0], me.cords.y + NAMETAG_OFFSET[0]))
            mynametag.blit(self.screen)

            pygame.display.update()
            pygame.time.Clock().tick(UPD)

