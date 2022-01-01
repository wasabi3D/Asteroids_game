import pygame
import os
from GameComponents.objects import Coordinate
from GameComponents.locals import *
from GameComponents.objects import ml


class BaseUIObject(pygame.sprite.Sprite):
    """Le class que tous les autres objets UI vont succéder(inherit)
    """
    def __init__(self, pos: Coordinate):
        """:param pos: la position de l'objet
        """
        pygame.sprite.Sprite.__init__(self)
        self.pos = pos

    def set_pos(self, pos: Coordinate):
        """:param pos: la nouvelle position de l'objet
        """
        self.pos = pos
        self.rect = self.image.get_rect(topleft=pos.t)
    
    def blit(self, screen):
        """Permet de dessiner le UI sur l'écran sur un screen donné
        :param screen: Un screen(instance de pygame.Surface) 
        """
        screen.blit(self.image, self.rect)


class ImageUI(BaseUIObject):
    """Permet d'afficher une image (utilisé pour la petite flèche au menu)
    """
    def __init__(self, image: pygame.surface.Surface, pos: Coordinate = Coordinate(0, 0)):
        """:param image: Image qui va être affiché
        :param pos: La position de l'image(topleft)
        """
        super().__init__(pos)
        self.image = image
        self.rect = image.get_rect()
        self.set_pos(pos)


class TextUI(BaseUIObject):
    """Permet d'afficher un texte (et modifier!) facilement"""
    def __init__(self, font: pygame.font.Font, color: tuple[int, int, int], text="",
                 pos: Coordinate = Coordinate(0, 0)):
        """:param font: La police utilisé(la taille incluse)  
        :param color: La couleur du texte
        :param text: Le contenu du texte
        :param pos: La position de l'objet
        """
        super().__init__(pos)
        self.font_object = font
        self.text = text
        self.color = color
        self.image = self.font_object.render(self.text, True, color)
        self.set_pos(pos)

    def set_text(self, text: str, pos: Coordinate = None, color: tuple[int, int, int] = None):
        """Permet de changer le contenu(, la position et la couleur éventuellement)
        :param color: La couleur du texte
        :param text: Le contenu du texte
        :param pos: La position de l'objet
        """
        self.text = text
        ps = self.pos if pos is None else pos
        cl = self.color if color is None else color
        self.image = self.font_object.render(self.text, True, cl)
        self.set_pos(ps)


class UIGroup:
    """Class qui permet de regrouper plusieurs UI objects et de les controller. Ce class contient une liste 
    qui va contenir les UI objects."""
    def __init__(self, pos: Coordinate):
        """:param pos: La position de l'objet. Tous les coordonées des objets ajoutés ici deviennent une position
                        relative par rapport au position de ce instance."""
        self.components = []
        self.relative_pos = []
        self.pos = pos

    def add_UI_object(self, ui: BaseUIObject, rel_pos: Coordinate, index: int):
        """Permet de ajouter un UI object
        :param ui: Le UI object qu'on veut ajouter.
        :param rel_pos: La position relative par rapport à la position de ce objet.
        :param index: Le index du list où on veut insérer l'object;
        """
        tmp = ui
        tmppos = Coordinate(self.pos.x + rel_pos.x, self.pos.y + rel_pos.y)
        tmp.set_pos(tmppos)

        self.components.insert(index, ui)
        self.relative_pos.insert(index, rel_pos)

    def set_pos(self, pos: Coordinate):
        """:param pos: la nouvelle position de l'objet
        """
        self.pos = pos
        for i, ui in enumerate(self.components):
            ui.set_pos(self.relative_pos[i] + self.pos)

    def set_text(self, new_text: str, index: int):
        """Permet de modifier le texte d'un TextUI object qui se situe à un index donné.
        :param new_text: Nouvelle texte qu'on veut mettre.
        :param index: La position de TextUI object dans la liste.
        """
        if type(self.components[index]) is TextUI:
            self.components[index].set_text(new_text)
        else:
            raise TypeError(' : this method only allows TextUI type')

    def remove(self, index: int):
        """Permet de supprimer un objet qui se situe à un index donné.
        :param index: L'index de l'objet qu'on veut supprimer."""
        self.components.pop(index)
        self.relative_pos.pop(index)

    def move_UI_element(self, x, y, index):
        """Permet de modifier la position d'un UI
        :param x: Le nouveau abcisse de l'objet.
        :param y: Le nouveau ordonée de l'objet.
        :param index: L'index de l'objet qu'on veut déplacer.
        """
        self.relative_pos[index].x = x
        self.relative_pos[index].y = y
        tmppos = Coordinate(self.pos.x + self.relative_pos[index].x, self.pos.y + self.relative_pos[index].y)
        self.components[index].set_pos(tmppos)

    def blit(self, screen):
        """Permet de afficher tout les UI objects.
        :param screen: Un instance de pygame.Surface où on veut afficher les objets.
        """
        for ui in self.components:
            screen.blit(ui.image, ui.rect)

    def length(self):
        """
        :return: Renvoie le nombre d'objets."""
        return len(self.components)


class MenuUI(UIGroup):
    """Class qui permet de créer un menu facilement."""
    def __init__(self, title: str, choices: tuple, cursor: pygame.Surface, pos: Coordinate,
                 title_font: pygame.font.Font, choices_font: pygame.font.Font, title_offset: Coordinate,
                 cursor_offset: Coordinate, choices_offset: Coordinate, choices_space: int, default_index=0,
                 align="left", name=""):
        """:param title: Le titre du menu. (Ex. 'Asteroids game', 'Host multiplayer game')
           :param choices: Les choix que le joueur peut faire. Le joueur sélectionne avec la flèche.
           :param cursor: L'image de la flèche.
           :param pos: La position du menu.
           :param title_font: La police (taille inclue) du titre.
           :param choices_font: La police (taille inclue) des choix affichés.
           :param title_offset: Précise la position du titre par rapport à la postition de ce objet(pos).
           :param cursor_offset: Précise comment on positionne la flèche.
           :param choices_offset: Précise comment on positionne les choix par rapport à 
                            la position de ce objet(pos).
           :param choices_space: L'espace entre chaque choix
           :param default_index: Le choix sélecté par défaut.
           :param align: Comment on aligne les choix: gauche si 'left', le centre si 'center',
                            droite si 'right'. Tous les 3 sont utilisés dans le jeu.
           :param name: Le nom de ce menu."""
        super().__init__(pos)
        self.name = name
        self.add_UI_object(TextUI(title_font, DEFAULT_TEXT_COL, title), title_offset, 0)
        if len(choices) > 0:
            self.cursor_cords = []
            self.selected = default_index
            x, y = choices_offset.t
            for choice in choices:
                text = TextUI(choices_font, DEFAULT_TEXT_COL, choice)
                if align.lower() == "left":
                    self.add_UI_object(text, Coordinate(x, y), 0)
                    self.cursor_cords.append(Coordinate(x + cursor_offset.x, y + cursor_offset.y))
                elif align.lower() == "center":
                    self.add_UI_object(text, Coordinate(x - text.image.get_width() / 2, y), 0)
                    self.cursor_cords.append(Coordinate(x + cursor_offset.x - text.image.get_width() / 2,
                                                        y + cursor_offset.y))
                elif align.lower() == "right":
                    self.add_UI_object(text, Coordinate(x - text.image.get_width(), y), 0)
                    self.cursor_cords.append(Coordinate(x + cursor_offset.x - text.image.get_width(),
                                                        y + cursor_offset.y))
                y += choices_space

            self.add_UI_object(ImageUI(cursor), self.cursor_cords[self.selected], 0)

    def move_cursor(self, index: int):
        """Fonction qui permet de bouger la flèche du menu.
        """
        tmp_index = self.selected + index
        if len(self.cursor_cords) > tmp_index >= 0:
            self.selected += index
            new_cord = self.cursor_cords[self.selected]
            # print(new_cord.x, new_cord.y, new_cord.t)  これの謎を解明する
            self.move_UI_element(new_cord.t[0], new_cord.t[1], 0)


class TextBoxUI(UIGroup):
    """Class qui permet de créer des textboxes."""
    def __init__(self, pos: Coordinate, width: int, font: pygame.font.Font, line_offset=Coordinate(0, 0),
                 text_offset=Coordinate(0, -20), allowed_chars="ALL", line_height=5, default_text=""):
        """:param pos: Position du pixel en haut à gauche du textbox.
        :param width: La largeur du textbox en pixels.
        :param font: La font pour afficher le input du joueur.
        :param line_offset: Comment on décale la ligne blanche qui est en dessous du texte par rapport à la
        position du textbox
        du texte affichée
        :param text_offset: Comment on décale la position du texte par rapport à la position du textbox
        :param allowed_chars: Spécifie les lettres qu'on peut mettre dans le textbox. Par exemple on donne 
        '1234567890.' si c'est pour une addresse IP.
        :param line_height: La hauteur de la ligne blanche
        :default_text: Texte dans le text box par défaut 
        """
        super().__init__(pos)
        self.add_UI_object(ImageUI(pygame.transform.scale(ml.dat[LINE], (width, line_height))), line_offset, 0)
        self.width = width
        self.font = font
        self.cont = default_text
        self.allowed = allowed_chars
        self.text_offset = text_offset
        self.line_offset = line_offset
        self.add_UI_object(TextUI(font, DEFAULT_TEXT_COL, default_text), Coordinate(text_offset.x + line_offset.x,
                                                                                    text_offset.y + line_offset.y), 0)

    def add_char(self, key):
        """Fonction qui permet de ajouter une lettre dans le textbox
        :param key: Le nombre en décimal qui correspond au lettre dans le tableau ASCII."""
        try:
            if chr(key) in self.allowed or self.allowed == "ALL":
                self.cont += chr(key)
                self.redraw()
        except ValueError:
            return

    def delete_char(self):
        """Fonction qui permet de supprimer une lettre.
        """
        if len(self.cont) > 0:
            self.cont = self.cont[:-1]
            self.redraw()

    def redraw(self):
        """Fonction qui permet de regénérer l'image du textbox"""
        self.remove(0)
        tmp_txt = TextUI(self.font, DEFAULT_TEXT_COL, self.cont)
        if tmp_txt.image.get_width() > self.width:
            tmp_txt.image = pygame.transform.scale(tmp_txt.image, (self.width, tmp_txt.image.get_height()))
        self.add_UI_object(tmp_txt, Coordinate(self.text_offset.x + self.line_offset.x,
                                               self.text_offset.y + self.line_offset.y), 0)


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
        gui_sh.add_UI_object(ImageUI.ml.dat[HEART], Coordinate(0, 0),\
                            Coordinate(-10 + x * ml.dat[HEART].get_width() + 10, SCORE_SIZE + 10,\
                            clamp_coordinate=False), x + 1)
    return gui_sh
