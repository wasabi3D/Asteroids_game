import os
import random
import pygame
from pygame import Surface, sprite
from pygame.math import Vector2
from pygame.locals import *
from collections import Sequence

import GameComponents.Medialoader as Medialoader
from GameComponents.locals import *
ml = Medialoader.Loader()


def clamp(min_, max_, n) -> int:
    """
    :return: rend la valeur n en fesant en sorte quelle reste entre min_ et max_
    """
    if n < min_:
        return min_
    elif n > max_:
        return max_
    else:
        return n


class Coordinate:
    """Class qui permet de représenter les coordonnées des objets dans le jeu. """

    def __init__(self, x: int, y: int, clamp_coordinate=True) -> None:
        """
        :param x: coordonnée x
        :param y: coordonnée y
        :param clamp_coordinate: définit si les coordonées doivent rester dans les valeurs de la taille de la fenêtre
        """
        self.x = x
        self.y = y
        self.t = (self.x, self.y)  # TUPLE
        self.do_clamp = clamp_coordinate
        self.max_x = SCREEN_DIMENSION[0]
        self.max_y = SCREEN_DIMENSION[1]

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Coordinate(self.x + other.x, self.y + other.y, self.do_clamp)
        elif isinstance(other, Coordinate):
            return Coordinate(self.x + other.x, self.y + other.y, self.do_clamp)

    def update(self, x: int, y: int, additive=False) -> None:
        """ permet de modifier les valeurs de l'objet

        :param x: nouvelle coordonnée x ou valeur à ajouter à self.x
        :param y: nouvelle coordonnée y ou valeur à ajouter à self.y
        :param additive: additive = True : définit si on fait le somme des anciennes valeurs x et y
                         additive = False : remplace les anciennes valeurs par les nouvelles
        """
        if additive:
            self.x += x
            self.y += y
        else:
            self.x = x
            self.y = y
        if self.do_clamp:
            self.clamp()
        self.t = (self.x, self.y)

    def clamp(self) -> None:
        """ fait en sorte que les coordonnées restent dans la fenêtre:
            si les valeurs sont plus grandes que la taille de la fenêtre alors les nouvelles valeurs seront 0
            si les valeurs sont plus petites que 0 alors elles deviendront la taille maximale de la fenêtre 
        """
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
        """
        :param pos
        """
        self.r = radius
        self.pos = pos

    def update(self, new_position: Coordinate) -> None:
        """donner les nouvelles coordonnées de l'objet"""
        self.pos.update(new_position.x, new_position.y)


class Player(pygame.sprite.Sprite):
    def __init__(self, xy: tuple[int, int], img: Surface) -> None:
        """:param xy: tuple contenant deux elements int : les coordonées x et y
        :param img: pygame.Surface contenant l'image de l'objet
        """
        super().__init__()

        # variables de positionnement
        self.cords = Coordinate(xy[0], xy[1])
        self.vector = Vector2(0, -1)
        self.angle = 0

        # variables de mouvement
        self.acc_spd = 0
        self.speed_vector = Vector2(0, 0)
        self.turning_speed = 0
        self.acc_ang = 0

        # variables permettant d'afficher l'image
        self.image = img
        self.rect = self.image.get_rect(center=xy)
        self.clone = self.image.copy()

        # variables permettant d'avoir les collisions et de créer des class : Bullets
        self.pCollider = Collider(self.cords, round(self.image.get_rect().width / 2))
        self.shoot_vector = Vector2(0, -1)

    def update(self, acc: bool, acc_ang: bool, delta: float = 1 / UPD) -> None:
        """fonction qu'on lance à chaque update permettant de calculer les nouvelles positions et direction de l'objet
        :param acc: bool qui est True si on veut accelerer et false si on arrète d'accelerer
        :param acc_ang: bool que est True si on veut tourner dans le sens horaire, False pour antihoraire et est None si on ne veut pas tourner
        :param delta: float qui nous donne le temps qu'à mis le programme à executer une update
        """

        # Verifie que le vecteur de direction à bien une longueur de 1 et réctifie si ce n'est pas le cas
        if not self.vector.is_normalized:
            self.vector.normalize_ip()
        
        # Cette zone s'occupe de la rotation de l'objet
        if acc_ang is None: # si on ne veut pas tourner
            self.turning_speed *= TURN_MULTIPLIER_PF
        elif acc_ang: # si on veut tourner dans le sens des aiguilles d'une montre
            self.turning_speed += TURN_ACC * delta
        elif not acc_ang: # si on veut tourner dans le sens contraire des aiguilles d'une montre
            self.turning_speed -= TURN_ACC * delta
        self.turning_speed = clamp(-MAX_TURN_SPEED, MAX_TURN_SPEED, self.turning_speed)
        self.rotate(self.turning_speed * delta) # rotate l'objet

        # s'occupe de la modification de l'acceleration
        if acc is True: # si on veut accelerer
            self.acc_spd += ACC * delta
            self.acc_spd = clamp(0, ACC, self.acc_spd)
            tmp_vec = Vector2(0, -1)
            tmp_vec.rotate_ip(self.angle)
            self.speed_vector += tmp_vec * self.acc_spd * delta
        if acc is False: # si on veut fraîner
            self.acc_spd = 0


        # modifie le vecteur vitesse
        cur_spd = self.speed_vector.length_squared()
        if cur_spd > 0.1:
            self.speed_vector += -1 * self.speed_vector * BREAK_MULTIPLIER
        if cur_spd > MAX_SPEED ** 2:
            self.speed_vector.scale_to_length(MAX_SPEED)

        # modification des coordonées
        self.cords.update(self.speed_vector.x * delta, self.speed_vector.y * delta, additive=True)

        # On met les nouvelles coordonnées au collider et on déplace le rectangle permettant d'afficher l'image
        self.pCollider.update(self.cords)
        self.rect = self.image.get_rect(center=self.cords.t)

    def rotate(self, angle: int or float) -> None:
        """permet de roter l'image et les vecteurs
        :param angle: si positife va tourner de "angle" degrés l'objet dans le sens 
        """
        b4_rct = self.image.get_rect(center=self.rect.center)
        self.angle += angle
        rotated = pygame.transform.rotate(self.clone.copy(), -self.angle)
        rct = rotated.get_rect(center=b4_rct.center)
        self.image = rotated
        self.rect = rct
        self.shoot_vector.rotate_ip(angle)
        # print(self.shoot_vector.x, self.shoot_vector.y)

    def rotate_to(self, angle: float or int) -> None:
        """roter l'image à un certain angle
        :param angle: modifier l'angle (0 deg = face North, 90 deg = face East)
        """
        self.rotate(angle - self.angle)

    def blit(self, screen: Surface) -> None:
        """faire apparaitre l'image sur une surface
        :param screen: la Surface sur laquelle on veut afficher l'image
        """
        screen.blit(self.image, self.rect)

    def set_pos(self, xy: tuple, angle: float):
        """définir de nouvelles coordonnées et un nouvel angle
        :param xy: nouvelles coordonnées
        :param angle: nouvel angle (0 deg vers le nord, 90 deg vers l'est)
        """
        self.rotate_to(angle)
        self.cords.update(xy[0], xy[1])
        self.speed_vector = Vector2(0, 0)
        self.acc_spd = 0
        self.pCollider.update(self.cords)
        self.acc_ang = 0
        self.rect = self.image.get_rect(center=self.cords.t)

    def play_death_sound(self):
        ml.dat[S_BE_SHOT].play()


# Une classe pour les joueurs en ligne, simplement des vies et un nom ont été rajoutés
class MpPlayer(Player):

    def __init__(self, xy: tuple[int, int], img: Surface, name: str, health: int) -> None:
        """:param xy: les coordonées d'apparition
        :param img: image du joueur
        :param name: le nom du joueur
        :param health: les vies données au début de la partie
        """
        super().__init__(xy, img)
        self.name = name
        self.health = health


# Classe pour contenir les informations des particules de déstruction d'asteroïdes (particule seule)
class BreakParticle(pygame.sprite.Sprite):
    def __init__(self, lifetime: int, angle: int, pos: Coordinate, speed: int) -> None:
        """:param lifetime: durée de vie des particules
        :param angle: dans quel angle vont les particules (direction et sens)
        :param pos: coordonées de la particule
        :param speed: définit la vitesse de la particule
        """
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(ml.dat[BULLET].copy(), (2, 2))
        self.copy = self.image
        self.rect = self.image.get_rect(center=pos.t)
        self.pos = pos
        self.vector = Vector2(0, -1).rotate(angle)
        self.speed = speed
        self.alpha = 255
        self.dec = 255 / lifetime

    def update(self) -> None:
        """Modifie la position et la transparance des particules"""
        self.rect.move_ip(self.vector.x * self.speed / UPD, self.vector.y * self.speed / UPD)
        self.alpha = int(self.alpha - self.dec / UPD)
        if self.alpha < 0:
            self.alpha = 0
        self.image.fill((255, 255, 255, self.alpha), None, pygame.BLEND_RGBA_MULT)


# Classe qui parmet d'avoir un groupe de particules et de les afficher
class BreakParticlesParent(sprite.Group):
    def __init__(self, lifetime: int, number: int, pos: Coordinate) -> None:
        """En créant l'objet, on crée en même temps toutes les particules qu'on veut
        :param lifetime: durée de vie des particules
        :param number: nombre de particules à créer
        :param pos: coordonées du point d'apparition des particules
        """
        pygame.sprite.Group.__init__(self)
        self.lifetme = lifetime
        self.timer = 0

        # Création des particules (angle au hazar)
        for _ in range(number):
            p = BreakParticle(PARTICLE_LIFETIME, random.randint(0, 359), pos, PARTICLE_SPD)
            self.add(p)

    def update(self) -> None:
        """Met à jour toutes les particules et le groupe"""
        for sp in self.sprites():
            sp.update()

        self.timer += 1 / UPD

    def lifetime_reached(self) -> bool:
        """Nous dit si le groupe de particules est arrivé à sa fin
        :return: True si le temps de vie est passé sinon F
        """
        return self.timer >= self.lifetme


# Classe permetant de contenir tous les groupes de particules
class ParticlesGroup:
    def __init__(self) -> None:
        self.particles = []

    def add_particle(self, pt: BreakParticlesParent):
        """Rajouter ungroupe de particules"""
        self.particles.append(pt)

    def update(self):
        """Mettre à jour tous les groupes"""
        for i, p in enumerate(self.particles):
            p.update()
            if p.lifetime_reached():
                self.particles.pop(i)

    def blit(self, screen):
        """Afficher toutes les particules"""
        for p in self.particles:
            p.draw(screen) # fonction de pygame qui nous permet d'afficher tous les sprites


# classe qui contien les informations d'une balle
class Bullet(pygame.sprite.Sprite):

    def __init__(self, xy: tuple[int, int], vector: Vector2, bul_id=0) -> None:
        """:param xy: coordonées d'apparition de la balle
        :param vector: vecteur représantant la vitesse de la balle
        :param bul_id: nombre de la balle
        """
        super().__init__()
        self.cords = Coordinate(xy[0], xy[1], clamp_coordinate=False)
        self.vector = vector * BULLET_SPEED
        self.image = ml.dat[BULLET]
        self.rect = self.image.get_rect(center=xy)
        self.pCollider = Collider(self.cords, self.image.get_width())
        self.id = bul_id

        ml.dat[S_SHOOT].play()

    def update(self) -> bool:
        """Met à jour les coordonées de la balle
        :return: True si la balle à dépassé les bordures de la fenêtre sinon False"""
        self.cords = self.cords + self.vector / UPD
        self.pCollider.update(self.cords)
        self.rect = self.image.get_rect(center=self.cords.t)
        if self.cords.x > SCREEN_DIMENSION[0] or self.cords.x < 0 or self.cords.y < 0 or self.cords.y > \
                SCREEN_DIMENSION[1]:
            return True
        return False

    def set_pos(self, xy: tuple) -> None:
        """Donner de nouvelles coordonées à la balle
        :param xy: nouvelles coordonées de la balle
        """
        self.cords.update(xy[0], xy[1])
        self.pCollider.update(self.cords)
        self.rect = self.image.get_rect(center=self.cords.t)

    def blit(self, screen) -> None:
        """Afficher la balle
        :param screen: sur quoi afficher l'image
        """
        screen.blit(self.image, self.rect)


# Classe contenant les informations d'un asteroïde
class Asteroid(pygame.sprite.Sprite):
    def __init__(self, xy: tuple[int, int], angle: float = 0., small: bool = False, ast_id=0, img="") -> None:
        """:param xy: """
        super().__init__()
        if img == "":
            self.img_index = random.randrange(0, len(ASTS))
        else:
            self.img_index = int(img)

        if not small:
            self.image = ml.dat[ASTS[self.img_index]]
        else:
            self.image = ml.dat['smallA' + ASTS[self.img_index][1:]]

        self.clone = self.image.copy()
        self.rect = self.image.get_rect(center=xy)
        self.cords = Coordinate(xy[0], xy[1])
        self.speed = ASTEROID_SPD
        self.angle = angle
        self.torque = ASTEROID_ANIM_TORQUE  # degree/s
        self.vector = Vector2(0, -1)
        self.vector.rotate_ip(angle)
        self.pCollider = Collider(self.cords, round(self.image.get_width() / 2))
        self.id = ast_id
        self.small = small

    def update(self):
        self.move()
        self.angle %= 360

    def move(self, delta=1 / UPD):
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

    def rotate_to(self, angle):
        self.rotate(angle - self.angle)

    def set_pos(self, xy: tuple, angle: float):
        self.rotate_to(angle)
        self.cords.update(xy[0], xy[1])
        self.pCollider.update(self.cords)
        self.rect = self.image.get_rect(center=self.cords.t)

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
                self.remove(sp)
                return True
        return False

    def is_colliding_destroy_bullet(self, other: BulletGroup, particlesList: ParticlesGroup,
                                    render_particles=True) -> list[Coordinate]:
        destroyed_list_cords = []
        bu: Bullet
        for bu in other.sprites():
            sp: Asteroid
            for sp in self.sprites():
                if is_colliding(sp.pCollider, bu.pCollider):
                    destroyed_list_cords.append(sp.cords)
                    if render_particles:
                        particlesList.add_particle(BreakParticlesParent(PARTICLE_PARENT_LIFETIME,
                                                                        random.randint(PARTICLE_MIN,
                                                                                       PARTICLE_MAX), sp.cords))
                    self.remove(sp)
                    other.remove(bu)
                    ml.dat[S_DESTROY].play()
        return destroyed_list_cords


def distance_square(p1: Coordinate, p2: Coordinate) -> int:
    """Fonction qui retourne la distance des 2 coordonées au carré.
    """
    return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2


def is_colliding(col1: Collider, col2: Collider) -> bool:
    return distance_square(col1.pos, col2.pos) <= (col1.r + col2.r) ** 2


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
    return t_, a_ == 1
