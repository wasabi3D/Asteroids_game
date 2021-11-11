import pygame
from GameComponents.objects import Coordinate
from GameComponents.locals import *
from GameComponents.objects import ml
from typing import Union


class BaseUIObject(pygame.sprite.Sprite):
    def __init__(self, pos: Coordinate):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pos

    def set_pos(self, pos: Coordinate):
        self.pos = pos
        self.rect = self.image.get_rect(topleft=pos.t)


class ImageUI(BaseUIObject):
    def __init__(self, image: pygame.surface.Surface, pos: Coordinate = Coordinate(0, 0)):
        super().__init__(pos)
        self.image = image
        self.rect = image.get_rect()
        self.set_pos(pos)


class TextUI(BaseUIObject):
    def __init__(self, font: pygame.font.Font, color: tuple[int, int, int], text="",
                 pos: Coordinate = Coordinate(0, 0)):
        super().__init__(pos)
        self.font_object = font
        self.text = text
        self.color = color
        self.image = self.font_object.render(self.text, True, color)
        self.set_pos(pos)

    def set_text(self, text: str, pos: Coordinate = None, color: tuple[int, int, int] = None):
        self.text = text
        ps = self.pos if pos is None else pos
        cl = self.color if color is None else color
        self.image = self.font_object.render(self.text, True, cl)
        self.set_pos(ps)

    def blit(self, screen):
        screen.blit(self.image, self.rect)


class UIGroup:
    def __init__(self, pos: Coordinate):
        self.components = []
        self.relative_pos = []
        self.pos = pos

    def add_UI_object(self, ui: BaseUIObject, rel_pos: Coordinate, index: int):
        tmp = ui
        tmppos = Coordinate(self.pos.x + rel_pos.x, self.pos.y + rel_pos.y)
        tmp.set_pos(tmppos)

        self.components.insert(index, ui)
        self.relative_pos.insert(index, rel_pos)

    def set_pos(self, pos: Coordinate):
        self.pos = pos
        for i, ui in enumerate(self.components):
            ui.set_pos(self.relative_pos[i] + self.pos)

    def set_text(self, new_text: str, index: int):
        if type(self.components[index]) is TextUI:
            self.components[index].set_text(new_text)
        else:
            raise TypeError(' : this method only allows TextUI type')

    def remove(self, index: int):
        self.components.pop(index)
        self.relative_pos.pop(index)

    def move_UI_element(self, x, y, index):
        self.relative_pos[index].x = x
        self.relative_pos[index].y = y
        tmppos = Coordinate(self.pos.x + self.relative_pos[index].x, self.pos.y + self.relative_pos[index].y)
        self.components[index].set_pos(tmppos)

    def blit(self, screen):
        for ui in self.components:
            screen.blit(ui.image, ui.rect)

    def length(self):
        return len(self.components)


class MenuUI(UIGroup):
    def __init__(self, title: str, choices: tuple, cursor: pygame.Surface, pos: Coordinate,
                 title_font: pygame.font.Font, choices_font: pygame.font.Font, title_offset: Coordinate,
                 cursor_offset: Coordinate, choices_offset: Coordinate, choices_space: int, default_index=0,
                 align="left", name=""):
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
        tmp_index = self.selected + index
        if len(self.cursor_cords) > tmp_index >= 0:
            self.selected += index
            new_cord = self.cursor_cords[self.selected]
            # print(new_cord.x, new_cord.y, new_cord.t)  これの謎を解明する
            self.move_UI_element(new_cord.t[0], new_cord.t[1], 0)


class TextBoxUI(UIGroup):
    def __init__(self, pos: Coordinate, width: int, font: pygame.font.Font, line_offset=Coordinate(0, 0),
                 text_offset=Coordinate(0, -20), allowed_chars="ALL", line_height=5, default_text=""):
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
        try:
            if chr(key) in self.allowed or self.allowed == "ALL":
                self.cont += chr(key)
                self.redraw()
        except ValueError:
            return

    def delete_char(self):
        if len(self.cont) > 0:
            self.cont = self.cont[:-1]
            self.redraw()

    def redraw(self):
        self.remove(0)
        tmp_txt = TextUI(self.font, DEFAULT_TEXT_COL, self.cont)
        if tmp_txt.image.get_width() > self.width:
            tmp_txt.image = pygame.transform.scale(tmp_txt.image, (self.width, tmp_txt.image.get_height()))
        self.add_UI_object(tmp_txt, Coordinate(self.text_offset.x + self.line_offset.x,
                                               self.text_offset.y + self.line_offset.y), 0)


