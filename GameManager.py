import GameComponents as Gc
from GameComponents.UI import *
import MpGameManager as mpgm
import pygame
from pygame.locals import *
import sys
import os
import random


another_connected = False
opponent_send = None


def generate_gameover_window(score: int) -> MenuUI:
    """
    Fonction permettant de générer les UI quand le joueur meurt.

    :params: Le score final
    :return: Une instance de MenuUI qui contient les UI.
    """
    font_path = os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT)

    score_text = TextUI(pygame.font.Font(font_path, 13), DEFAULT_TEXT_COL, f"Score: {score}", Coordinate(0, 0))

    menu = MenuUI("Game Over", ("Return to the menu", "Quit game"), ml.dat[ARROW],
                     Coordinate(SCREEN_DIMENSION[0] / 2 - 110, SCREEN_DIMENSION[1] / 2 - 100),
                     pygame.font.Font(font_path, 25), pygame.font.Font(font_path, 15), Coordinate(50, 20),
                     Coordinate(-30, -5), Coordinate(45, 80), 30, align="left")
    menu.add_UI_object(score_text, Coordinate(50, 50), 1)

    return menu


def generate_score_UI(score: int) -> UIGroup:
    """
    Fonction permettant de générer le UI de score et de HP.

    :params: Le score final
    :return: Une instance de UIGroup qui contient les UI.
    """
    sc_font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), SCORE_SIZE)
    gui_sh = UIGroup(Coordinate(10, 10, clamp_coordinate=False))
    gui_sh.add_UI_object(TextUI(sc_font, (217, 211, 211), str(score)),
                         Coordinate(0, 0, clamp_coordinate=False), 0)
    for x in range(3):
        gui_sh.add_UI_object(ImageUI(ml.dat[HEART], Coordinate(0, 0)),
                            Coordinate(-10 + x * ml.dat[HEART].get_width() + 10, SCORE_SIZE + 10,
                            clamp_coordinate=False), x + 1)
    return gui_sh


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

        # ++++ INIT ++++
        title_offset = Gc.Coordinate(SCREEN_DIMENSION[0] / 2 - 130, 60)
        cursor_offset = Gc.Coordinate(-30, 0)

        # fonts
        title_font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), TITLE_SIZE)
        sc_font = pygame.font.Font(os.path.join(os.path.dirname(__file__), TYPEWRITER_FONT), SELECTABLE_SIZE)

        # textbox, timeout text label, etc..
        additional_ui = []

        # Le premier menu
        main_menu = Gc.MenuUI(TITLE_TXT, ("Single Player", "Multi Player", "Quit"), Gc.ml.dat[ARROW],
                              Gc.Coordinate(0, 0),
                              title_font, sc_font,
                              title_offset, cursor_offset,
                              Gc.Coordinate(400, 300), 50, align="center", name="main")

        # Le menu où on choisit si le joueur host ou join une game
        multi_mode_select = Gc.MenuUI("Multiplayer", ("Host game", "Join an existing game", "Back"), Gc.ml.dat[ARROW],
                                      Gc.Coordinate(0, 0), title_font, sc_font, title_offset, cursor_offset,
                                      Gc.Coordinate(500, 300), 75, align="right", name="mms")

        # Le menu où on met l'ip du host et le nom du joueur pour join un game
        join_multi_select = Gc.MenuUI("Join asteroid game", ("Enter IP: ", "Your name:", "Join", "Back"),
                                      Gc.ml.dat[ARROW],
                                      Gc.Coordinate(0, 0), title_font,
                                      sc_font, title_offset, cursor_offset,
                                      Gc.Coordinate(400, 375), 75, align="right", name="jms")

        # Le menu où on host une game
        host_multi = Gc.MenuUI("Host new game", ("Your name:", "Players count:", "Go", "Back"), Gc.ml.dat[ARROW],
                               Gc.Coordinate(0, 0), title_font,
                               sc_font, title_offset, cursor_offset,
                               Gc.Coordinate(400, 460), 75, align="right", name="host")

        # Les textbox pour mettre l'addresse IP, le nom du joueur et le nombre de joueur, respectivement
        ip_textbox = Gc.TextBoxUI(Gc.Coordinate(400, 400), 200, sc_font,
                                  allowed_chars="0123456789.")
        name_textbox = Gc.TextBoxUI(Gc.Coordinate(400, 475), 200, sc_font)
        players_num_textbox = Gc.TextBoxUI(Gc.Coordinate(400, 550), 200, sc_font, allowed_chars="0123456789")

        draw_ui = main_menu  # Le UI où on va dessiner sur l'écran

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                # Menu behaviours
                if event.type == pygame.KEYDOWN:
                    """Quand le joueur appuie sur un bouton."""
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
            # ++++ UPDATE 
            screen.fill(BG_COLOR)
            draw_ui.blit(screen)
            for ui in additional_ui:
                ui.blit(screen)
            pygame.display.update()

    # SINGLE PLAYER GAME LOOP
    def game():
        """Fonction appelé pour démarrer le mode singleplayer."""

        # >>>>>> Initialize >>>>>>>
        running = True
        player = Gc.Player((SCREEN_DIMENSION[0] / 2, SCREEN_DIMENSION[1] / 2), Gc.ml.dat[PLAYER])  # Instance du player
        score = 0

        asteroids = Gc.AstGroup()  # Variable qui va contnenir les (grands) asteroids
        small_asteroids = Gc.objects.AstGroup()  # Variable qui va contenir les (petits) asteroids

        bullets = Gc.BulletGroup()  # Variable qui va contenir les balles
        t_bullets = 0  # Timer pour le cooldown de tir

        game_over_window = None 
        lock_space = False  # Un bool pour bloquer la touch espace afin de ne pas aller directement au main menu apres que le player meurt

        particles = Gc.ParticlesGroup()  # Variable qui va contenir les particules qui apparaissent lors un asteroid se casse
        gui_sh = generate_score_UI(score)

        tick = 0  # Nombre de ticks(frame) écoulés après le start du jeu
        # <<<<<<<<<

        # >>>>>> Main loop >>>>>>
        while running:
            # ++++ Input events ++++
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            pressed = pygame.key.get_pressed()
            turn, accel = Gc.objects.get_turn_and_accel_state(pressed)
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
                    player.play_death_sound()

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

    # MAIN LOOP
    while True:
        menu()
        game()

