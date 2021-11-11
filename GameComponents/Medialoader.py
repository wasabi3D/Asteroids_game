
IMAGE = "image"
SOUND = "sound"



class Loader:

    def __init__(self):
        self.dat = {}
        self.load()

    def load(self):
        import os
        import pygame

        pygame.mixer.init()

        def get_prefix(s):
            if s == "+img":
                return os.path.join("media", "images"), IMAGE
            elif s == "+sound":
                return os.path.join("media", "sounds"), SOUND

        prefix = ""
        mediatype = ""
        d = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(d, "assets.txt"), 'r') as f:
            lines = f.readlines()

            for string in lines:
                string = string[:-1] if string[-1] == "\n" else string
                if string == "":
                    continue
                if string[0] == "+":
                    prefix, mediatype = get_prefix(string)
                    continue

                tag, file = string.split(":")

                if mediatype == IMAGE:
                    self.dat.setdefault(tag, pygame.image.load(os.path.join(d, prefix, file)))
                elif mediatype == SOUND:
                    self.dat.setdefault(tag, pygame.mixer.Sound(os.path.join(d, prefix, file)))

        with open(os.path.join(d, "image_resize.txt"), "r") as f:
            lines = f.readlines()
            for s in lines:
                s = s[:-1] if s[-1] == '\n' else s
                if s == "":
                    continue
                tag, size = s.split(":")
                size = size.split('x')
                self.dat[tag] = pygame.transform.scale(self.dat[tag], (int(size[0]), int(size[1])))

