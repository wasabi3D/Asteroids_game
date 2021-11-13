import random

import pygame
from pygame import Surface, sprite
from pygame.math import Vector2

import GameComponents.Medialoader as Medialoader
import GameComponents.locals as glocals

ml = Medialoader.Loader()


def clamp(min_, max_, n):
    if n < min_:
        return min_
    elif n > max_:
        return max_
    else:
        return n


def lerp(org, arr, value):
    return org + (arr - org) * value


class Coordinate:
    """
    Class qui permet de représenter les coordonnées des objets dans le jeu. 
    """

    def __init__(self, x: int, y: int, clamp_coordinate=True):
        self.x = x
        self.y = y
        self.t = (self.x, self.y)  # TUPLE
        self.do_clamp = clamp_coordinate
        self.max_x = glocals.SCREEN_DIMENSION[0]
        self.max_y = glocals.SCREEN_DIMENSION[1]

    def update(self, x: int, y: int, additive=False):
        if additive:
            self.x += x
            self.y += y
        else:
            self.x = x
            self.y = y
        if self.do_clamp:
            self.clamp()
        self.t = (self.x, self.y)

    def __add__(self, other):
        if type(other) is Coordinate:
            return Coordinate(self.x + other.x, self.y + other.y, clamp_coordinate=(self.do_clamp or other.do_clamp))
        elif type(other) is tuple:
            return Coordinate(self.x + other[0], self.y + other[1], clamp_coordinate=self.do_clamp)
        elif type(other) is Vector2:
            return Coordinate(self.x + other.x, self.y + other.y, clamp_coordinate=self.do_clamp)
        elif type(other) is int or type(other) is float:
            return Coordinate(self.x + other, self.y + other, clamp_coordinate=self.do_clamp)

    def clamp(self):
        if self.x < 0:
            self.x = self.max_x
        elif self.x > self.max_x:
            self.x = 0

        if self.y < 0:
            self.y = self.max_y
        elif self.y > self.max_y:
            self.y = 0


class Collider:
    def __init__(self, pos: Coordinate, radius: int) -> None:
        self.r = radius
        self.pos = pos

    def update(self, new_position: Coordinate):
        self.pos.update(new_position.x, new_position.y)


class Player(pygame.sprite.Sprite):
    def __init__(self, xy: tuple[int, int], img: Surface) -> None:
        super().__init__()
        self.cords = Coordinate(xy[0], xy[1])
        self.vector = Vector2(0, -1)
        self.acc_spd = 0
        self.speed_vector = Vector2(0, 0)
        self.angle = 0
        self.turning_speed = 0
        self.acc_ang = 0
        self.image = img
        self.rect = self.image.get_rect(center=xy)
        self.clone = self.image.copy()
        self.pCollider = Collider(self.cords, round(self.image.get_rect().width / 2))
        self.shoot_vector = Vector2(0, -1)

    def update(self, acc: bool, acc_ang: bool, delta=1 / glocals.UPD) -> None:

        if not self.vector.is_normalized:
            self.vector.normalize_ip()
        # Image rotate
        if acc_ang is None:
            self.turning_speed *= glocals.TURN_MULTIPLIER_PF
        elif acc_ang:
            self.turning_speed += glocals.TURN_ACC * delta
        elif not acc_ang:
            self.turning_speed -= glocals.TURN_ACC * delta
        self.turning_speed = clamp(-glocals.MAX_TURN_SPEED, glocals.MAX_TURN_SPEED, self.turning_speed)
        self.rotate(self.turning_speed * delta)

        if acc:
            self.acc_spd += glocals.ACC * delta
            self.acc_spd = clamp(0, glocals.ACC, self.acc_spd)
            tmp_vec = Vector2(0, -1)
            tmp_vec.rotate_ip(self.angle)
            self.speed_vector += tmp_vec * self.acc_spd * delta
        else:
            self.acc_spd = 0

        cur_spd = self.speed_vector.length_squared()
        if cur_spd > 0.1:
            self.speed_vector += -self.speed_vector * glocals.BREAK_MULTIPLIER
        if cur_spd > glocals.MAX_SPEED ** 2:
            self.speed_vector.scale_to_length(glocals.MAX_SPEED)

        self.cords.update(self.speed_vector.x * delta, self.speed_vector.y * delta, additive=True)

        self.pCollider.update(self.cords)
        self.rect = self.image.get_rect(center=self.cords.t)

    def rotate(self, angle):
        b4_rct = self.image.get_rect(center=self.rect.center)
        self.angle += angle
        rotated = pygame.transform.rotate(self.clone.copy(), -self.angle)
        rct = rotated.get_rect(center=b4_rct.center)
        self.image = rotated
        self.rect = rct
        self.shoot_vector.rotate_ip(angle)

    def rotate_to(self, angle):
        self.rotate(angle - self.angle)

    def blit(self, screen):
        screen.blit(self.image, self.rect)

    def set_pos(self, xy: tuple, angle: float):
        self.rotate_to(angle)
        self.cords.update(xy[0], xy[1])
        self.speed_vector = Vector2(0, 0)
        self.acc_spd = 0
        self.pCollider.update(self.cords)
        self.acc_ang = 0
        self.rect = self.image.get_rect(center=self.cords.t)

    def set_img(self, image_: pygame.Surface):
        old_ang = self.angle
        self.rotate_to(0)
        self.image = image_
        self.rect = self.image.get_rect(center=self.cords.t)
        self.rotate_to(old_ang)


class MpPlayer(Player):
    def __init__(self, xy: tuple[int, int], img: Surface, name: str):
        super().__init__(xy, img)
        self.name = name


class BreakParticle(pygame.sprite.Sprite):
    def __init__(self, lifetime: int, angle: int, pos: Coordinate, speed: int) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(ml.dat[glocals.BULLET].copy(), (2, 2))
        self.copy = self.image
        self.rect = self.image.get_rect(center=pos.t)
        self.pos = pos
        self.vector = Vector2(0, -1).rotate(angle)
        self.speed = speed
        self.alpha = 255
        self.dec = 255 / lifetime

    def update(self):
        self.rect.move_ip(self.vector.x * self.speed / glocals.UPD, self.vector.y * self.speed / glocals.UPD)
        self.alpha = int(self.alpha - self.dec / glocals.UPD)
        if self.alpha < 0:
            self.alpha = 0
        self.image.fill((255, 255, 255, self.alpha), None, pygame.BLEND_RGBA_MULT)


class BreakParticlesParent(sprite.Group):
    def __init__(self, lifetime: int, number: int, pos: Coordinate) -> None:
        pygame.sprite.Group.__init__(self)
        self.lifetme = lifetime
        self.timer = 0

        for _ in range(number):
            p = BreakParticle(glocals.PARTICLE_LIFETIME, random.randint(0, 360), pos, glocals.PARTICLE_SPD)
            self.add(p)

    def update(self):
        for sp in self.sprites():
            sp.update()

        self.timer += 1 / glocals.UPD

    def lifetime_reached(self):
        return self.timer >= self.lifetme


class ParticlesGroup:
    def __init__(self) -> None:
        self.particles = []

    def add_particle(self, pt: BreakParticlesParent):
        self.particles.append(pt)

    def update(self):
        for i, p in enumerate(self.particles):
            p.update()
            if p.lifetime_reached():
                self.particles.pop(i)

    def blit(self, screen):
        for p in self.particles:
            p.draw(screen)


class Bullet(pygame.sprite.Sprite):

    def __init__(self, xy: tuple[int, int], vector: Vector2, bul_id=0) -> None:
        super().__init__()
        self.cords = Coordinate(xy[0], xy[1], clamp_coordinate=False)
        self.vector = vector * glocals.BULLET_SPEED
        self.image = ml.dat[glocals.BULLET]
        self.rect = self.image.get_rect(center=xy)
        self.pCollider = Collider(self.cords, self.image.get_width())
        self.id = bul_id

    def update(self):
        self.cords = self.cords + self.vector / glocals.UPD
        self.pCollider.update(self.cords)
        self.rect = self.image.get_rect(center=self.cords.t)
        if self.cords.x > glocals.SCREEN_DIMENSION[0] or self.cords.x < 0 or self.cords.y < 0 or self.cords.y > \
                glocals.SCREEN_DIMENSION[1]:
            return True
        return False

    def blit(self, screen):
        screen.blit(self.image, self.rect)


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, xy: tuple[int, int], angle: float = 0., small: bool = False, ast_id=0, img="") -> None:
        super().__init__()
        if img == "":
            self.img_index = random.randrange(0, len(glocals.ASTS))
        else:
            self.img_index = img

        if not small:
            self.image = ml.dat[glocals.ASTS[self.img_index]]
        else:
            self.image = ml.dat['smallA' + glocals.ASTS[self.img_index]]

        self.clone = self.image.copy()
        self.rect = self.image.get_rect(center=xy)
        self.cords = Coordinate(xy[0], xy[1])
        self.speed = glocals.ASTEROID_SPD
        self.angle = angle
        self.torque = glocals.ASTEROID_ANIM_TORQUE  # degree/s
        self.vector = Vector2(0, -1)
        self.vector.rotate_ip(angle)
        self.pCollider = Collider(self.cords, round(self.image.get_width() / 2))
        self.id = ast_id
        self.small = small

    def update(self):
        self.move()
        self.angle %= 360

    def move(self, delta=1 / glocals.UPD):
        self.cords.update(self.speed * self.vector.x * delta, self.speed * self.vector.y * delta, additive=True)
        self.rect = self.image.get_rect(center=self.cords.t)
        self.pCollider.update(self.cords)
        self.rotate(self.torque * delta)

    def rotate(self, angle):
        b4_rct = self.image.get_rect(center=self.rect.center)
        self.angle += angle
        rotated = pygame.transform.rotate(self.clone.copy(), -self.angle)
        rct = rotated.get_rect(center=b4_rct.center)
        self.image = rotated
        self.rect = rct

    def blit(self, screen):
        screen.blit(self.image, self.rect)


class BulletGroup(sprite.Group):
    def __init__(self, *sprites) -> None:
        super().__init__(*sprites)

    def update(self) -> None:
        for sp in self.sprites():
            if sp.update():
                self.remove(sp)


class AstGroup(sprite.Group):

    def __init__(self, *sprites) -> None:
        super().__init__(*sprites)

    def is_colliding_player(self, pl: Player) -> bool:
        sp: Asteroid
        for sp in self.sprites():
            if is_colliding(sp.pCollider, pl.pCollider):
                return True
        return False

    def is_colliding_destroy_bullet(self, other: BulletGroup, particlesList: ParticlesGroup) -> list[Coordinate]:
        destroyed_list_cords = []
        bu: Bullet
        for bu in other.sprites():
            sp: Asteroid
            for sp in self.sprites():
                if is_colliding(sp.pCollider, bu.pCollider):
                    destroyed_list_cords.append(sp.cords)
                    particlesList.add_particle(BreakParticlesParent(glocals.PARTICLE_PARENT_LIFETIME,
                                                                    random.randint(glocals.PARTICLE_MIN,
                                                                                   glocals.PARTICLE_MAX), sp.cords))
                    self.remove(sp)
                    other.remove(bu)
        return destroyed_list_cords


def distance_square(p1: Coordinate, p2: Coordinate) -> int:
    return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2


def is_colliding(col1: Collider, col2: Collider) -> bool:
    return distance_square(col1.pos, col2.pos) <= (col1.r + col2.r) ** 2
