import threading
from collections import Sequence
import GameComponents as Gc
from GameComponents.locals import *
import MpGameManager as mpgm
import pygame
from pygame.locals import *
import sys
import os
import random
import json


another_connected = False
opponent_send = None

def generate_gameover_window(score: int) -> Gc.MenuUI:
    """
    Fonction permettant de générer les UI quand le joueur meurt.

    :params: Le score final
    :return: Une instance de MenuUI qui contient les UI.
    """
    font_path = os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT)

    score_text = Gc.UI.TextUI(pygame.font.Font(font_path, 13), DEFAULT_TEXT_COL, f"Score: {score}", Gc.Coordinate(0, 0))

    menu = Gc.MenuUI("Game Over", ("Return to the menu", "Quit game"), Gc.ml.dat[ARROW],
                     Gc.objects.Coordinate(SCREEN_DIMENSION[0] / 2 - 110, SCREEN_DIMENSION[1] / 2 - 100),
                     pygame.font.Font(font_path, 25), pygame.font.Font(font_path, 15), Gc.Coordinate(50, 20),
                     Gc.Coordinate(-30, -5), Gc.Coordinate(45, 80), 30, align="left")
    menu.add_UI_object(score_text, Gc.objects.Coordinate(50, 50), 1)

    return menu


def generate_score_UI(score: int) -> Gc.UIGroup:
    """
    Fonction permettant de générer le UI de score et de HP.

    :params: Le score final
    :return: Une instance de UIGroup qui contient les UI.
    """
    sc_font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), SCORE_SIZE)
    gui_sh = Gc.UIGroup(Gc.Coordinate(10, 10, clamp_coordinate=False))
    gui_sh.add_UI_object(Gc.TextUI(sc_font, (217, 211, 211), str(score)),
                         Gc.Coordinate(0, 0, clamp_coordinate=False), 0)
    for x in range(3):
        gui_sh.add_UI_object(Gc.ImageUI(Gc.ml.dat[HEART], Gc.Coordinate(0, 0)),
                             Gc.Coordinate(-10 + x * Gc.ml.dat[HEART].get_width() + 10, SCORE_SIZE + 10,
                                           clamp_coordinate=False), x + 1)
    return gui_sh


def get_turn_and_accel_state(pressed: Sequence[bool]) -> tuple[bool, bool]:
    """Fonction permettant de savoir si le joueur est en train de accélérer(ou pas) et si il est en train de tourner(ou pas).

    :param pressed: Un sequence de bool renvoyé par la fonction pygame
    :return: Une tuple de bool où
            = Le premier représente comment le joueur tourne(None si il tourne pas, True si il tourne dans
            le sens de l'aiguille de montre et False à l'envers. )

            = Le deuxième représente si le joueur accélère( True si oui False si non)
    """
    angle_clwise = pressed[K_RIGHT] or pressed[K_d]
    angle_counter_clwise = pressed[K_LEFT] or pressed[K_a]
    t_ = None if not angle_clwise ^ angle_counter_clwise else angle_clwise
    a_ = pressed[K_w] or pressed[K_UP]
    return t_, a_


def run():
    """Fonction appelé par main.py pour démarrer le jeu."""
    # Init fenêtre
    screen = pygame.display.set_mode(SCREEN_DIMENSION)
    pygame.display.set_caption(WINDOW_TITLE)

    def menu(skip_menu=False):
        """Fonction appelé après run() ou game() pour afficher le menu du jeu.
        :param skip_menu: Si on passe directement à game() ou pas.
        """
        if skip_menu:
            return

        title_offset = Gc.Coordinate(SCREEN_DIMENSION[0] / 2 - 130, 60)
        cursor_offset = Gc.Coordinate(-30, 0)

        title_font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), TITLE_SIZE)

        sc_font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), SELECTABLE_SIZE)

        additional_ui = []

        main_menu = Gc.MenuUI(TITLE_TXT, ("Single Player", "Multi Player", "Quit"), Gc.ml.dat[ARROW],
                              Gc.Coordinate(0, 0),
                              title_font, sc_font,
                              title_offset, cursor_offset,
                              Gc.Coordinate(400, 300), 50, align="center", name="main")

        multi_mode_select = Gc.MenuUI("Multiplayer", ("Host game", "Join an existing game", "Back"), Gc.ml.dat[ARROW],
                                      Gc.Coordinate(0, 0), title_font, sc_font, title_offset, cursor_offset,
                                      Gc.Coordinate(500, 300), 75, align="right", name="mms")

        join_multi_select = Gc.MenuUI("Join asteroid game", ("Enter IP: ", "Your name:", "Join", "Back"),
                                      Gc.ml.dat[ARROW],
                                      Gc.Coordinate(0, 0), title_font,
                                      sc_font, title_offset, cursor_offset,
                                      Gc.Coordinate(400, 375), 75, align="right", name="jms")

        host_multi = Gc.MenuUI("Host new game", ("Your name:", "Players count:", "Go", "Back"), Gc.ml.dat[ARROW],
                               Gc.Coordinate(0, 0), title_font,
                               sc_font, title_offset, cursor_offset,
                               Gc.Coordinate(400, 460), 75, align="right", name="host")

        ip_textbox = Gc.TextBoxUI(Gc.Coordinate(400, 400), 200, sc_font,
                                  allowed_chars="0123456789.")
        name_textbox = Gc.TextBoxUI(Gc.Coordinate(400, 475), 200, sc_font)

        players_num_textbox = Gc.TextBoxUI(Gc.Coordinate(400, 550), 200, sc_font, allowed_chars="0123456789")

        draw_ui = main_menu

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                # Menu behaviours
                if event.type == pygame.KEYDOWN:
                    if draw_ui.name == "main":  # MAIN MENU
                        if event.key == K_DOWN or event.key == K_s:
                            draw_ui.move_cursor(1)
                        if event.key == K_UP or event.key == K_w:
                            draw_ui.move_cursor(-1)
                        if event.key == K_SPACE:
                            selected = draw_ui.selected
                            if selected == 0:
                                host = False
                                multi = False
                                return host, multi
                            elif selected == 1:
                                draw_ui = multi_mode_select
                            elif selected == 2:
                                sys.exit()
                    elif draw_ui.name == "mms":  # MULTIPLAYER MODE SELECT SCREEN
                        if event.key == K_DOWN or event.key == K_s:
                            draw_ui.move_cursor(1)
                        if event.key == K_UP or event.key == K_w:
                            draw_ui.move_cursor(-1)
                        if event.key == K_SPACE:
                            selected = draw_ui.selected
                            if selected == 0:
                                draw_ui = host_multi
                                additional_ui.append(name_textbox)
                                additional_ui.append(players_num_textbox)
                            elif selected == 1:
                                draw_ui = join_multi_select
                                additional_ui.append(ip_textbox)
                                additional_ui.append(name_textbox)

                            elif selected == 2:
                                draw_ui = main_menu
                    elif draw_ui.name == "jms":  # JOIN MULTIPLAYER GAME
                        selected = draw_ui.selected
                        if event.key == K_DOWN or event.key == K_s:
                            draw_ui.move_cursor(1)
                        if event.key == K_UP or event.key == K_w:
                            draw_ui.move_cursor(-1)
                        if event.key == K_SPACE:
                            if selected == 3:
                                draw_ui = multi_mode_select
                                additional_ui.clear()
                            elif selected == 2:
                                join = mpgm.Client(screen, ip_textbox.cont, name_textbox.cont)
                                ret = join.loop()
                                if ret is not None:
                                    additional_ui.append(ret)
                        elif event.key == K_BACKSPACE or event.key == K_DELETE:
                            try:
                                additional_ui[selected].delete_char()
                            except IndexError:
                                pass
                            except AttributeError:
                                pass
                        else:
                            try:
                                additional_ui[selected].add_char(event.key)
                            except IndexError:
                                pass
                            except AttributeError:
                                pass
                    elif draw_ui.name == "host":  # HOST MULTIPLAYER GAME
                        selected = draw_ui.selected
                        if event.key == K_DOWN or event.key == K_s:
                            draw_ui.move_cursor(1)
                        if event.key == K_UP or event.key == K_w:
                            draw_ui.move_cursor(-1)
                        if event.key == K_SPACE:
                            if selected == 3:
                                draw_ui = multi_mode_select
                                additional_ui.clear()
                            elif selected == 2:  # START MULTIPLAYER
                                try:
                                    num = int(players_num_textbox.cont)
                                except ValueError:
                                    num = 2
                                hst = mpgm.Host(screen, num, name_textbox.cont)
                                hst.loop()
                        elif event.key == K_BACKSPACE or event.key == K_DELETE:
                            try:
                                additional_ui[selected].delete_char()
                            except IndexError:
                                pass
                        else:
                            try:
                                additional_ui[selected].add_char(event.key)
                            except IndexError:
                                pass

            screen.fill(BG_COLOR)
            draw_ui.blit(screen)
            for ui in additional_ui:
                ui.blit(screen)
            pygame.display.update()

    # SINGLE PLAYER GAME LOOP
    def game():
        """Fonction appelé pour démarrer le mode multiplayer.
        """

        # >>>>>> Initialize >>>>>>>
        running = True
        player = Gc.Player((SCREEN_DIMENSION[0] / 2, SCREEN_DIMENSION[1] / 2), Gc.ml.dat[PLAYER])
        score = 0

        asteroids = Gc.AstGroup()
        small_asteroids = Gc.objects.AstGroup()

        bullets = Gc.BulletGroup()
        t_bullets = 0

        game_over_window = None
        lock_space = False

        particles = Gc.ParticlesGroup()
        gui_sh = generate_score_UI(score)

        tick = 0
        # <<<<<<<<<

        # >>>>>> Main loop >>>>>>
        while running:
            # ++++ Input events ++++
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            pressed = pygame.key.get_pressed()
            turn, accel = get_turn_and_accel_state(pressed)
            # +++++++

            screen.fill(BG_COLOR)  # Background
            
            # ++++ Generate asteroids ++++
            if tick % (UPD * AST_FREQUECY) == 0:  
                if random.randint(0, 1) == 1:
                    x = random.randint(0, SCREEN_DIMENSION[0] - 1)
                    y = 0
                else:
                    y = random.randint(0, SCREEN_DIMENSION[1] - 1)
                    x = 0
                asteroids.add(Gc.Asteroid((x, y), random.randint(0, 359)))
            # +++++

            destroyed = asteroids.is_colliding_destroy_bullet(bullets, particles)
            score += len(destroyed) * POINTS_P_AST
            if len(destroyed) > 0:  # Small asteroids
                for d_cords in destroyed:
                    for _ in range(random.randint(SMALL_ASTS_PDA[0], SMALL_ASTS_PDA[1])):
                        small_asteroids.add(Gc.Asteroid(d_cords.t, random.randint(0, 359), small=True))

            score += round(len(small_asteroids.is_colliding_destroy_bullet(bullets, particles)) * POINTS_P_AST / 2)

            if pressed[K_SPACE] and t_bullets <= 0:  # Generate bullets
                bullets.add(Gc.Bullet(player.cords.t, player.shoot_vector * BULLET_SPEED))
                t_bullets = round(UPD / 3)

            if asteroids.is_colliding_player(player) or small_asteroids.is_colliding_player(player):
                if gui_sh.length() > 1:
                    gui_sh.remove(-1)
                    player.set_pos((SCREEN_DIMENSION[0] / 2, SCREEN_DIMENSION[1] / 2), 0)

                if gui_sh.length() == 1:  # Game over
                    game_over_window = generate_gameover_window(score)
                    lock_space = True

            if game_over_window is None:
                player.update(accel, turn)
                bullets.update()
                asteroids.update()
                small_asteroids.update()
            else:
                if pressed[K_DOWN] or pressed[K_s]:
                    game_over_window.move_cursor(1)

                if pressed[K_UP] or pressed[K_w]:
                    game_over_window.move_cursor(-1)
                if pressed[K_SPACE] and not lock_space:
                    select_index = game_over_window.selected
                    if select_index == 0:
                        return
                    elif select_index == 1:
                        sys.exit()
                game_over_window.blit(screen)

            if not pressed[K_SPACE]:
                lock_space = False

            # ++++Updates++++
            tick += 1
            t_bullets -= 1
            gui_sh.set_text(str(score), 0)
            gui_sh.blit(screen)
            particles.update()
            particles.blit(screen)
            player.blit(screen)
            bullets.draw(screen)
            asteroids.draw(screen)
            small_asteroids.draw(screen)
            pygame.display.update()
            pygame.time.Clock().tick(UPD)
            # ++++++
        # <<<<<<<<<<

    while True:
        menu()
        game()

