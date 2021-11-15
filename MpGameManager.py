import GameComponents as Gc
from GameComponents.locals import *
import pygame
from pygame.locals import *
from distutils.util import strtobool
import os
import sys
import json
import random
import time
import threading


def get_turn_and_accel_state(pressed) -> tuple[bool, bool]:
    angle_clwise = pressed[K_RIGHT] or pressed[K_d]
    angle_counter_clwise = pressed[K_LEFT] or pressed[K_a]
    t_ = None if not angle_clwise ^ angle_counter_clwise else angle_clwise
    a_ = pressed[K_w] or pressed[K_UP]
    return t_, a_


def generate_score_UI(score: int) -> Gc.UIGroup:
    sc_font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), SCORE_SIZE)
    gui_sh = Gc.UIGroup(Gc.Coordinate(10, 10, clamp_coordinate=False))
    gui_sh.add_UI_object(Gc.TextUI(sc_font, (217, 211, 211), str(score)),
                         Gc.Coordinate(0, 0, clamp_coordinate=False), 0)
    for x in range(HP):
        gui_sh.add_UI_object(Gc.ImageUI(Gc.ml.dat[HEART], Gc.Coordinate(0, 0)),
                             Gc.Coordinate(-10 + x * Gc.ml.dat[HEART].get_width() + 10, SCORE_SIZE + 10,
                                           clamp_coordinate=False), x + 1)
    return gui_sh


class Client:
    def __init__(self, screen, host_ip, name):
        self.screen: pygame.Surface = screen
        self.host_ip = host_ip
        self.my_ip = Gc.get_local_ip()
        self.name = name
        self.receive = Gc.Receive(DEFAULT_PORT, self._on_response)
        self.connection_state = ""
        self.game_started = False
        self.running = False
        self.other_players: dict[str, Gc.MpPlayer] = {}
        self.nametags: dict[str, Gc.TextUI] = {}
        self.font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 12)
        self.font_b = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 20)
        self.last_host_response = time.time()
        self.timed_out = False
        self.timeout_detector = threading.Thread(target=self._timeout_detection)
        self.detect_timeout = True
        self.asteroids: dict[int, Gc.Asteroid] = {}
        self.small_asteroids: dict[int, Gc.Asteroid] = {}
        self.bullets: dict[int, Gc.Bullet] = {}
        self.t_bullets = 0
        self.dead = False
        self.spawned = False
        self.me: Gc.MpPlayer = None
        self.score = 0
        self.score_gui = generate_score_UI(self.score)

        self.receive.start()
        self.timeout_detector.start()

    # MAIN GAME LOOP
    def loop(self):
        # >>>>>> CONNECT TO HOST >>>>>>
        self._try_join()

        connecting_txt = Gc.TextUI(self.font_b, DEFAULT_TEXT_COL, "Connecting...", Gc.Coordinate(100, 650))
        connecting_txt.blit(self.screen)
        pygame.display.update()
        while self.connection_state == "":
            if self.timed_out:
                self.stop_client()
                return Gc.TextUI(self.font_b, DEFAULT_TEXT_COL, "Connection timed out(join).", Gc.Coordinate(100, 650))
        self.screen.fill(BG_COLOR, connecting_txt.rect)
        if self.connection_state == COM_GAME_FULL:
            connecting_txt.set_text("Connection error: GAME FULL. ")
            return COM_GAME_FULL
        # <<<<<<

        # >>>>>> WAIT FOR START >>>>>
        connecting_txt.set_text("Waiting for the start...")
        connecting_txt.blit(self.screen)
        pygame.display.update()
        while not self.game_started:
            if self.timed_out:
                self.stop_client()
                return Gc.TextUI(self.font_b, DEFAULT_TEXT_COL, "Connection timed out(lobby).", Gc.Coordinate(100, 700))
        self.running = True
        # <<<<<<<<<

        # >>>>> INITIALIZE >>>>>
        host_send = Gc.Send(self.host_ip, DEFAULT_PORT)
        self.me = Gc.MpPlayer((random.randint(0, 600), random.randint(0, 600)), Gc.ml.dat[PLAYER], self.name, HP)
        mynametag = Gc.TextUI(self.font, DEFAULT_TEXT_COL, self.name,
                              Gc.Coordinate(self.me.cords.x + NAMETAG_OFFSET[0], self.me.cords.y + NAMETAG_OFFSET[1]))
        # <<<<<<<<

        # >>>>> MAIN LOOP >>>>>
        while self.running:
            # +++CHECK TIMEOUT+++
            if self.timed_out:
                self.stop_client()
                return Gc.TextUI(self.font_b, DEFAULT_TEXT_COL, "Connection timed out(game).", Gc.Coordinate(100, 700))
            # ++++++

            # +++INPUT EVENTS+++
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop_client()
                    sys.exit()
            pressed = pygame.key.get_pressed()
            # ++++++
            self.screen.fill(BG_COLOR)

            # +++SHOOT+++
            if not self.dead:
                if pressed[K_SPACE] and self.t_bullets <= 0:  # Generate bullets
                    tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_SHOOT, f"{self.me.cords.x}{DELIMITER}{self.me.cords.y}{DELIMITER}"
                                                                     f"{self.me.shoot_vector.x}{DELIMITER}{self.me.shoot_vector.y}",
                                         "")
                    host_send.send_message(json.dumps(tmp_msg.d()))
                    self.t_bullets = round(UPD / 3)
            # ++++++

            # +++SEND CLIENT's POS DATA TO HOST+++
            if not self.dead:
                tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_PLAYER_POS,
                                     f"{self.me.cords.x}{DELIMITER}{self.me.cords.y}{DELIMITER}"
                                     f"{self.me.angle}{DELIMITER}{Gc.get_local_ip()}", self.name)
                host_send.send_message(json.dumps(tmp_msg.d()))
            # ++++++

            # +++DRAW PLAYERS+++
            s: Gc.MpPlayer
            for ip, s in self.other_players.items():
                self.nametags[ip].set_pos(Gc.Coordinate(s.cords.x + NAMETAG_OFFSET[0], s.cords.y + NAMETAG_OFFSET[1]))
                s.blit(self.screen)
                self.nametags[ip].blit(self.screen)
            # ++++++

            # +++DRAW ASTEROIDS+++
            a: Gc.Asteroid
            for a in list(self.asteroids.values()).copy():
                a.blit(self.screen)
            for a in list(self.small_asteroids.values()).copy():
                print("yes")
                a.blit(self.screen)
            # ++++++

            # +++GUI UPDATE+++
            if self.score_gui.length() - 1 > self.me.health:
                self.score_gui.remove(-1)
            self.score_gui.set_text(str(self.score), 0)
            # ++++++

            # +++DRAW BULLETS+++
            b: Gc.Bullet
            for b in self.bullets.values():
                b.blit(self.screen)
            # ++++++

            # +++UPDATES+++
            if not self.dead:
                turn, accel = get_turn_and_accel_state(pressed)
                self.me.update(accel, turn)
                self.me.blit(self.screen)
                mynametag.set_pos(Gc.Coordinate(self.me.cords.x + NAMETAG_OFFSET[0], self.me.cords.y + NAMETAG_OFFSET[1]))
                mynametag.blit(self.screen)
            self.t_bullets -= 1
            self.score_gui.blit(self.screen)
            pygame.display.update()
            pygame.time.Clock().tick(UPD)
            # ++++++
        # <<<<<<<<

    def _try_join(self):
        tmp_send = Gc.Send(self.host_ip, DEFAULT_PORT)
        tmp_msg = Gc.GameCom(COM_PREP, COM_REQUEST_JOIN, self.name, "")
        tmp_send.send_message(json.dumps(tmp_msg.d()))

    def _on_response(self, msg, addr):
        self.last_host_response = time.time()
        received = Gc.GameCom("", "", "", "")
        received.__dict__ = json.loads(msg)
        if received.info_type == COM_PREP:
            if received.msg == COM_GAME_START:
                self.game_started = True
            else:
                self.connection_state = received.msg
        elif received.info_type == COM_GAMEDATINFO:
            ast_remove_flag: list[int] = list(self.asteroids.keys())
            small_ast_remove_flag: list[int] = list(self.small_asteroids.keys())
            bullets_remove_flag: list[int] = list(self.bullets.keys())
            players_remove_flag: list[str] = list(self.other_players.keys())
            players_remove_flag.append(self.my_ip)
            info: list[Gc.GameCom] = []
            d: dict
            for d in json.loads(received.msg):
                g_ = Gc.GameCom("", "", "", "")
                g_.__dict__ = d
                info.append(g_)

            for i in info:
                if i.msg == COM_ASTEROID:
                    tmp = i.value.split(DELIMITER)
                    x, y, angle, aid = int(float(tmp[0])), int(float(tmp[1])), int(float(tmp[2])), int(float(tmp[3]))
                    tmp = i.other.split(DELIMITER)
                    small, image_index = bool(strtobool(tmp[0])), tmp[1]
                    if not small:
                        if aid in self.asteroids.keys():
                            self.asteroids[aid].set_pos((x, y), angle)
                            self.asteroids[aid].angle = angle
                        else:
                            a = Gc.Asteroid((x, y), angle, small=False, ast_id=aid, img=image_index)
                            self.asteroids.setdefault(aid, a)
                        if aid in ast_remove_flag:
                            ast_remove_flag.remove(aid)
                    else:
                        if aid in self.small_asteroids.keys():
                            self.small_asteroids[aid].set_pos((x, y), angle)
                            self.small_asteroids[aid].angle = angle
                        else:
                            a = Gc.Asteroid((x, y), angle, small=True, ast_id=aid, img=image_index)
                            self.small_asteroids.setdefault(aid, a)
                        if aid in small_ast_remove_flag:
                            small_ast_remove_flag.remove(aid)
                elif i.msg == COM_BULLET:
                    tmp = i.value.split(DELIMITER)
                    x, y, bid = int(float(tmp[0])), int(float(tmp[1])), int(float(tmp[2]))
                    if bid in self.bullets.keys():
                        self.bullets[bid].set_pos((x, y))
                    else:
                        b = Gc.Bullet((x, y), pygame.Vector2(0, 0), bul_id=bid)
                        self.bullets.setdefault(bid, b)
                    if bid in bullets_remove_flag:
                        bullets_remove_flag.remove(bid)
                elif i.msg == COM_PLAYER_POS:
                    sp = i.value.split(DELIMITER)
                    osp = i.other.split(DELIMITER)
                    x, y, a, ip = int(float(sp[0])), int(float(sp[1])), int(float(sp[2])), sp[3]
                    name, health, self.score = osp[0], int(float(osp[1])), int(float(osp(2)))

                    if ip in players_remove_flag:
                        players_remove_flag.remove(ip)
                    if ip == self.my_ip:
                        self.spawned = True
                        self.dead = False
                        self.me.health = health
                        if x == int(SCREEN_DIMENSION[0] / 2) and y == int(SCREEN_DIMENSION[1] / 2):
                            self.me.set_pos((SCREEN_DIMENSION[0] / 2, SCREEN_DIMENSION[1] / 2), self.me.angle)
                        continue
                    if ip not in self.other_players.keys():
                        self.other_players.setdefault(ip, Gc.MpPlayer((x, y), Gc.ml.dat[PLAYER], name, HP))
                        p = self.other_players[ip]
                        self.nametags.setdefault(ip, Gc.TextUI(self.font, DEFAULT_TEXT_COL, p.name,
                                                               Gc.Coordinate(p.cords.x + NAMETAG_OFFSET[0],
                                                                             p.cords.y + NAMETAG_OFFSET[1])))
                    self.other_players[ip].set_pos((x, y), a)

            # Remove unnecessary objects
            for aid in ast_remove_flag:
                if aid in self.asteroids.keys():
                    self.asteroids.pop(aid)
            for aid in small_ast_remove_flag:
                if aid in self.small_asteroids.keys():
                    self.small_asteroids.pop(aid)
            for bid in bullets_remove_flag:
                if bid in self.bullets.keys():
                    self.bullets.pop(bid)
            for ip_ in players_remove_flag:
                if ip_ == self.my_ip and self.spawned:
                    self.dead = True
                    print("Dead")
                if ip_ in self.other_players.keys():
                    self.other_players.pop(ip_)

    def stop_client(self):
        self.receive.kill()
        self.detect_timeout = False
        self.timeout_detector.join()
        print("waiting for other threads to finish..")
        for th in threading.enumerate():
            if th is threading.currentThread():
                continue
            th.join()

    def _timeout_detection(self):
        while self.detect_timeout:
            print(time.time() - self.last_host_response)
            if time.time() - self.last_host_response > TIMEOUT:
                self.timed_out = True
                break
            time.sleep(TIMEOUT_CHECK_RATE)


class Host:
    def __init__(self, screen, num_players, name):
        self.screen: pygame.Surface = screen
        self.host_receive = Gc.Receive(DEFAULT_PORT, self._on_rec_from_client)
        self.num_players = num_players
        self.players_name_lobby = []
        self.players_name_game = []
        self.ips = []
        self.running = False
        self.do_ping = False
        self.players_sprites: dict[str, Gc.MpPlayer] = {}
        self.nametags: dict[str, Gc.TextUI] = {}
        self.send_objects: list[Gc.Send] = []
        self.name = name
        self.asteroids = Gc.AstGroup()
        self.small_asteroids = Gc.objects.AstGroup()
        self.bullets = Gc.BulletGroup()
        self.font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 12)
        self.ping_th: threading.Thread = None
        self.me: Gc.MpPlayer = None
        self.t_bullets = 0
        self.tick = 0
        self.asteroids_count = 0
        self.small_asteroids_count = 0
        self.bullets_count = 0
        self.score = 0
        self.my_ip = Gc.get_local_ip()
        self.dead = False
        self.score_gui = generate_score_UI(self.score)

        self.players_name_lobby.append(name)
        self.host_receive.start()

    # MAIN LOOP
    def loop(self):
        # >>>>>>>> INITIALIZE WINDOW UIs>>>>>>>
        font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), 15)
        wait_txt = Gc.TextUI(font, DEFAULT_TEXT_COL, "Waiting for players...", Gc.Coordinate(SCREEN_DIMENSION[0] / 2,
                                                                                             SCREEN_DIMENSION[1] / 2))
        ip_txt = Gc.TextUI(font, DEFAULT_TEXT_COL, f"Share this ip to your friends: {Gc.get_local_ip()}",
                           Gc.Coordinate(50, 50))

        players_txt = []
        pl_txt_cord = Gc.Coordinate(100, 110)
        for i in range(self.num_players):
            players_txt.append(Gc.TextUI(font, DEFAULT_TEXT_COL, f"Player {i + 1}: ", Gc.Coordinate(pl_txt_cord.x,
                                                                                                    pl_txt_cord.y)))
            pl_txt_cord.update(0, 20, additive=True)
        # <<<<<<<<<<<<<<<<<<<<<

        # >>>>>>> WAIT FOR PLAYERS >>>>>>>
        self.do_ping = True
        self.ping_th = threading.Thread(target=self._ping_connected_players)
        self.ping_th.start()
        while len(self.players_name_lobby) < self.num_players:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.kill_host()
                    sys.exit()

            self.screen.fill(BG_COLOR)
            for i, txt in enumerate(players_txt):  # update text
                if i + 1 > len(self.players_name_lobby):
                    break
                txt.set_text(f"Player {i + 1}: {self.players_name_lobby[i]}", pos=txt.pos)

            for txt in players_txt:
                txt.blit(self.screen)
            wait_txt.blit(self.screen)
            ip_txt.blit(self.screen)
            pygame.display.update()
        self.do_ping = False
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        # >>>>>>>> SEND GAME START SIGNAL TO CLIENTS AND INITIALIZE OBJECTS >>>>>>>>
        self.running = True
        for ip in self.ips:
            tmp_send = Gc.Send(ip, DEFAULT_PORT)
            tmp_msg = Gc.GameCom(COM_PREP, COM_GAME_START, "", "")
            tmp_send.send_message(json.dumps(tmp_msg.d()))

        self.me = Gc.MpPlayer((SCREEN_DIMENSION[0] / 2, SCREEN_DIMENSION[1] / 2), Gc.ml.dat[PLAYER], self.name, HP)
        mynametag = Gc.TextUI(self.font, DEFAULT_TEXT_COL, self.name,
                              Gc.Coordinate(self.me.cords.x + NAMETAG_OFFSET[0], self.me.cords.y + NAMETAG_OFFSET[0]))
        for i, ip in enumerate(self.ips):
            self.players_sprites.setdefault(ip, Gc.MpPlayer((0, 0), Gc.ml.dat[PLAYER], self.players_name_game[i], HP))
            self.send_objects.append(Gc.Send(ip, DEFAULT_PORT))
            p = self.players_sprites[ip]
            self.nametags.setdefault(ip, Gc.TextUI(self.font, DEFAULT_TEXT_COL, p.name,
                                                   Gc.Coordinate(p.cords.x + NAMETAG_OFFSET[0],
                                                                 p.cords.y + NAMETAG_OFFSET[1])))
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        # >>>>>>>>> GAME LOOP >>>>>>>>>>
        while self.running:
            # +++EVENTS+++
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.kill_host()
                    sys.exit()
            self.screen.fill(BG_COLOR)
            pressed = pygame.key.get_pressed()
            turn, accel = get_turn_and_accel_state(pressed)
            # ++++++

            # +++SHOOT+++
            if not self.dead:
                if pressed[K_SPACE] and self.t_bullets <= 0:  # Generate bullets
                    self.bullets.add(Gc.Bullet(self.me.cords.t, self.me.shoot_vector * BULLET_SPEED,
                                               bul_id=self.bullets_count))
                    self.bullets_count += 1
                    self.t_bullets = round(UPD / 3)
            # ++++++

            # +++ASTEROIDS GENERATION+++
            if self.tick % (UPD * AST_FREQUECY) == 0:  # Generate asteroids
                if random.randint(0, 1) == 1:
                    x = random.randint(0, SCREEN_DIMENSION[0] - 1)
                    y = 0
                else:
                    y = random.randint(0, SCREEN_DIMENSION[1] - 1)
                    x = 0
                self.asteroids.add(Gc.Asteroid((x, y), random.randint(0, 359), ast_id=self.asteroids_count))
                self.asteroids_count += 1
            # ++++++

            # +++DRAW PLAYERS+++
            for ip, p in self.players_sprites.items():
                p.blit(self.screen)
                self.nametags[ip].set_pos(Gc.Coordinate(p.cords.x + NAMETAG_OFFSET[0],
                                                        p.cords.y + NAMETAG_OFFSET[1]))
                self.nametags[ip].blit(self.screen)
            # +++++++

            # +++DETECT COLLISIONS+++
            destroyed = self.asteroids.is_colliding_destroy_bullet(self.bullets, None, render_particles=False)
            self.score += len(destroyed) * POINTS_P_AST
            if len(destroyed) > 0:  # Small asteroids
                for d_cords in destroyed:
                    for _ in range(random.randint(SMALL_ASTS_PDA[0], SMALL_ASTS_PDA[1])):
                        self.small_asteroids.add(Gc.Asteroid(d_cords.t, random.randint(0, 359),
                                                             small=True, ast_id=self.small_asteroids_count))
                        self.small_asteroids_count += 1
            self.score += round(len(self.small_asteroids.is_colliding_destroy_bullet(self.bullets, None, render_particles=False))
                                * POINTS_P_AST / 2)

            pop_list: list[str] = []
            pl: Gc.MpPlayer
            for k, pl in self.players_sprites.items():
                if self.asteroids.is_colliding_player(pl) or self.small_asteroids.is_colliding_player(pl):
                    # if gui_sh.length() > 1:
                    #     gui_sh.remove(-1)
                    pl.health -= 1
                    if pl.health <= 0:
                        pop_list.append(k)
                        # self.players_sprites.pop(k)
                        continue
                    pl.set_pos((int(SCREEN_DIMENSION[0] / 2), int(SCREEN_DIMENSION[1] / 2)), 0)
            for p in pop_list:
                self.players_sprites.pop(p)

            if not self.dead:
                if self.asteroids.is_colliding_player(self.me) or self.small_asteroids.is_colliding_player(self.me):
                    self.me.health -= 1
                    if self.me.health <= 0:
                        self.dead = True
                    else:
                        self.me.set_pos((SCREEN_DIMENSION[0] / 2, SCREEN_DIMENSION[1] / 2), 0)
            # +++

            # +++GUI UPDATE+++
            if self.score_gui.length() - 1 > self.me.health:
                self.score_gui.remove(-1)
            self.score_gui.set_text(str(self.score), 0)
            # ++++++

            # +++DRAW OBJECTS+++
            self.bullets.draw(self.screen)
            self.asteroids.draw(self.screen)
            self.small_asteroids.draw(self.screen)
            # ++++++

            # +++UPDATE+++
            if not self.dead:
                self.me.update(accel, turn)
                self.me.blit(self.screen)
                mynametag.set_pos(Gc.Coordinate(self.me.cords.x + NAMETAG_OFFSET[0], self.me.cords.y + NAMETAG_OFFSET[0]))
                mynametag.blit(self.screen)

            threading.Thread(target=self._send_objects_data2client).start()
            self.tick += 1
            self.t_bullets -= 1
            self.bullets.update()
            self.asteroids.update()
            self.small_asteroids.update()
            self.score_gui.blit(self.screen)
            pygame.display.update()
            pygame.time.Clock().tick(UPD)
            # ++++++
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<

    def _on_rec_from_client(self, msg_, addr):
        received = Gc.GameCom("", "", "", "")
        received.__dict__ = json.loads(msg_)
        if received.info_type == COM_PREP:
            print("REQUEST!!!!")
            tmp_send = Gc.Send(addr[0], DEFAULT_PORT)
            if len(self.players_name_game) < self.num_players:
                self.players_name_lobby.append(received.value)
                self.players_name_game.append(received.value)
                self.ips.append(addr[0])
                tmp_msg = Gc.GameCom(COM_PREP, COM_CON_SUCCESS, "", "")
                tmp_send.send_message(json.dumps(tmp_msg.d()))
            else:
                tmp_send.set_message(json.dumps((COM_PREP, COM_GAME_FULL)))
        elif received.info_type == COM_GAMEDATINFO:
            name = received.other
            if received.msg == COM_PLAYER_POS:
                sp = received.value.split(DELIMITER)
                x, y, a, ip = int(float(sp[0])), int(float(sp[1])), int(float(sp[2])), sp[3]
                if addr[0] in self.players_sprites.keys():
                    self.players_sprites[addr[0]].set_pos((x, y), a)
            elif received.msg == COM_SHOOT:
                sp = received.value.split(DELIMITER)
                x, y, dx, dy = int(float(sp[0])), int(float(sp[1])), float(sp[2]), float(sp[3])
                b = Gc.Bullet((x, y), pygame.Vector2(dx, dy) * BULLET_SPEED, bul_id=self.bullets_count)
                self.bullets_count += 1
                self.bullets.add(b)

    def _ping_connected_players(self):
        while self.do_ping:
            for ip in self.ips:
                print(ip)
                tmp_send = Gc.Send(ip, DEFAULT_PORT)
                tmp_send.send_message(json.dumps(Gc.GameCom(COM_PREP, COM_PING, "", "").d()))
            time.sleep(4)

    def kill_host(self):
        self.do_ping = False
        self.ping_th.join()
        self.host_receive.kill()
        print("waiting for other threads to finish..")
        for th in threading.enumerate():
            if th is threading.currentThread():
                continue
            th.join()

    def _send_objects_data2client(self):
        s: Gc.Send
        common_info: list[dict] = []

        # HOST itself
        if not self.dead:
            tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_PLAYER_POS,
                                 f"{self.me.cords.x}{DELIMITER}{self.me.cords.y}{DELIMITER}{self.me.angle}"
                                 f"{DELIMITER}{self.my_ip}", self.name)
            common_info.append(tmp_msg.d())
        # +++ASTEROIDS+++
        ast: Gc.Asteroid
        for ast in self.asteroids.sprites():
            tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_ASTEROID, f"{ast.cords.x}{DELIMITER}{ast.cords.y}{DELIMITER}"
                                                                f"{ast.angle}{DELIMITER}{ast.id}",
                                 f"{False}{DELIMITER}{ast.img_index}")
            common_info.append(tmp_msg.d())
        for ast in self.small_asteroids.sprites():
            tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_ASTEROID, f"{ast.cords.x}{DELIMITER}{ast.cords.y}{DELIMITER}"
                                                                f"{ast.angle}{DELIMITER}{ast.id}",
                                 f"{True}{DELIMITER}{ast.img_index}")
            common_info.append(tmp_msg.d())
        # +++
        # +++BULLETS+++
        bul: Gc.Bullet
        for bul in self.bullets.sprites():
            tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_BULLET, f"{bul.cords.x}{DELIMITER}{bul.cords.y}"
                                                              f"{DELIMITER}{bul.id}", "")
            common_info.append(tmp_msg.d())
        # +++
        # +++OTHER PLAYER's INFORMATION+++
        for ip, sprite in self.players_sprites.items():
            tmp_msg = Gc.GameCom(COM_GAMEDATINFO, COM_PLAYER_POS,
                                 f"{sprite.cords.x}{DELIMITER}{sprite.cords.y}{DELIMITER}"
                                 f"{sprite.angle}{DELIMITER}{ip}", DELIMITER.join([sprite.name, str(sprite.health), str(self.score)]))
            common_info.append(tmp_msg.d())
        # +++

        for s_ in self.send_objects:
            s = s_.copy()

            final = Gc.GameCom(COM_GAMEDATINFO, json.dumps(common_info), "", "")
            s.set_message(json.dumps(final.d()))
            s.run()
