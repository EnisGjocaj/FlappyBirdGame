#! /usr/bin/env python3


import math
import os
from random import randint
from collections import deque

import pygame
from pygame.locals import *


FPS = 120
ANIMATION_SPEED = 0.18  # piksela per milisekonda
WIN_WIDTH = 570     # madhesia e prapaskenes: 284x512 px; tiled twice
WIN_HEIGHT = 1024


class Bird(pygame.sprite.Sprite):
    """Reprezenton lojtarin

    Attributet:
    x: Kordinata X.
    y: Kordinata Y.
    msec_to_climb: Numri i milisekondave per mu ngjit, ku nje ngjitje e plot zgjat.

    Konstantet:
    WIDTH: Gjeresia e imazhit te lojtarit.
    HEIGHT: Lartesia e imazhit te lojtarit.
    SINK_SPEED: Me cfare shpejtesia=e lojtari bie ne piksela per milisekond kur nuk ngjitet per 1s.
    CLIMB_SPEED: Shpejtesia mesatare me te cilen lojtari ngjitet brenda nje sekondi.
    CLIMB_DURATION: Numri i milisekondave qe i duhen lojtarit per te bere nje ngjitje te plote.
    """

    WIDTH = HEIGHT = 32
    SINK_SPEED = 0.18
    CLIMB_SPEED = 0.3
    CLIMB_DURATION = 333.3

    def __init__(self, x, y, msec_to_climb, images):
        """Inicializojme instancen e lojtarit.

        images: Nje tuple qe i permban imazhet e lojtarit.  Duhet ti permbaje keto imazhe ne kete renditje:
                0. Imazhi i lojtarit qe shkon lart
                1. Imazhi i lojtarit qe shkon poshte
        """
        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.msec_to_climb = msec_to_climb
        self._img_wingup, self._img_wingdown = images
        self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)

    def update(self, delta_frames=1):
        """Rivendosja e poztites.

        Ky funksion perdore funksionin e kosinusit per ta arritur nje ngjitje te lehte:
        Ne numrin e pare te frameve, lojtari ngjitet vetem pak, kurse ne mes te ngjitjes, ngjitet me shume.
        Nje ngjitje e plote zgjat CLIMB_DURATION milisekonda, pergjate te ciles lojtari ngjitet me shoejtesi
        prej CLIMB_SPEED px/ms.
        Atributi msec_to_climb ne menyre automatike zvogelohet nese ishte > 0 kur thirret metoda.

        Argumentet:
        delta_frames: Numri i framve te plotsuara prej qe u thirr metoda.
        """
        if self.msec_to_climb > 0:
            frac_climb_done = 1 - self.msec_to_climb/Bird.CLIMB_DURATION
            self.y -= (Bird.CLIMB_SPEED * frames_to_msec(delta_frames) *
                       (1 - math.cos(frac_climb_done * math.pi)))
            self.msec_to_climb -= frames_to_msec(delta_frames)
        else:
            self.y += Bird.SINK_SPEED * frames_to_msec(delta_frames)

    @property
    def image(self):
        """Siperfaqja qe e mban lojtarin.

        Kjo do vendose nese do e kthejme nje imazh ku lojtari do kete imazh te zbritjes apo te ngjitjes,
        duke u bazuar ne pygame.time.get_ticks(). Kjo do e animoje flutirimin, i clili praktikish nuk mbeshtetet nga ambienti.

        """
        if pygame.time.get_ticks() % 500 >= 250:
            return self._img_wingup
        else:
            return self._img_wingdown

    @property
    def mask(self):
        """Maska per dedektimin e goditjes.

        Kjo bitmaske i largon te gjithe pikselat ne self.image me transarence me te madhe se 127"""
        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown

    @property
    def rect(self):
        """Marrim poziten e lojtarit"""
        return Rect(self.x, self.y, Bird.WIDTH, Bird.HEIGHT)


class PipePair(pygame.sprite.Sprite):
    """Reprezenton objektin.

    PipePair ka pjesen e kokes dhe fundore objekt por mund te kaloje vetem ne mes.
    
    Attributet:
    x: Pozicioni X i PipePair.  Ky eshte numer me prejse dhjteore qe te beje animationin me naryral.
    Nuk ka koordinate Y.
    imazhi:  pygame.Surface e cila mund te ndertohet mbi siperfaqe per paraqitjen e pipepair.
    top_pieces: numri i pjeseve, pjeset e larta.
    bottom_pieces: Pjeset e fundit te objekteve, duke i perfshire ato.

    Konstantet:
    WIDTH: Gjeresia e objekteve. Meqe cdo imazh permban nje objekt, ateher ajo paraqet edhe gjeresine e imazhit.
    PIECE_HEIGHT: Lartesia e objektit.
    ADD_INTERVAL: Intervali i shtimit te objekteve te reja ne milisekonda.
    """

    WIDTH = 80
    PIECE_HEIGHT = 32
    ADD_INTERVAL = 3000

    def __init__(self, pipe_end_img, pipe_body_img):
        """Inicializimi i nje objekti re rendomte.
    
        Objekti i ri PipePair ne menyre automatike to vendoset ne nje x atrubute float(WIN_WIDTH - 1)

        Argumentet:
        pipe_end_img: Imazhi qe reprezenton fundin e objektit.
        pipe_body_img: Imazhi qe reprezenton prejen horizontale te objektit.
        """
        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False

        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()  
        self.image.fill((0, 0, 0, 0))
        total_pipe_body_pieces = int(
            (WIN_HEIGHT -                  # mbushim dritaren nga poshte lart
             3 * Bird.HEIGHT -             # hapsira qe mbush lojtari
             3 * PipePair.PIECE_HEIGHT) /  # 2 pjese fundore + 1 ne krye
            PipePair.PIECE_HEIGHT          # per te marre numrin e pjeseve
        )
        self.bottom_pieces = randint(1, total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces

        # objekt fundore
        for i in range(1, self.bottom_pieces + 1):
            piece_pos = (0, WIN_HEIGHT - i*PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)

        # objekt larte
        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))

        self.top_pieces += 1
        self.bottom_pieces += 1

        # per detektim te goditjes
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def top_height_px(self):
        """lartesia ne piksela e objkektit ne krye"""
        return self.top_pieces * PipePair.PIECE_HEIGHT

    @property
    def bottom_height_px(self):
        """Lartesia ne piksela e objektit ne fund"""
        return self.bottom_pieces * PipePair.PIECE_HEIGHT

    @property
    def visible(self):
        """Marrim konfirmimin nese objekti ehste ne dritare"""
        return -PipePair.WIDTH < self.x < WIN_WIDTH

    @property
    def rect(self):
        """Marrim drejtekendeshin qe e permban objekti"""
        return Rect(self.x, 0, PipePair.WIDTH, PipePair.PIECE_HEIGHT)

    def update(self, delta_frames=1):
        """Rivendoisja e pozicionit te objektit.

        Argumentet:
        delta_frames: Numri i frames qe elapsohet prej kur thirret metoda.
        """
        self.x -= ANIMATION_SPEED * frames_to_msec(delta_frames)

    def collides_with(self, bird):
        """Nese goditet lojrtari me objekt.

        Argumenti:
        bird: Lojtari qe testohet per goditje.
        """
        return pygame.sprite.collide_mask(self, bird)


def load_images(screen_width, screen_height):
    """I marrim te gjitha imazhet e lojes dhe i vendosim ne nje matrice.

    Matrica e kthyer i ka keta celesa:
    background:Prapaskena e lojes.
    bird-wingup: Nje imazh qe tregon se lojtari shkon lart.

    bird-wingdown: Nje imazh qe tregon se lojtari shkon poshte.

    pipe-end: Nje imazh qe tregon objektin fundore (Pak me i gjere).

    pipe-body: Pjesen e trupit te objektit. 
    """

    def load_image(img_file_name, use_alpha=False):
        """E kthen imazhin e loduar te pygame me emrin e file te saj.

        Ky funksion i kerkon dhe shikon per imazhet ne direktiven:
        (dirname(__file__)/images/). Te gjitha imazhet konvertohen para se te pranohen.

        Argumented:
        img_file_name: File name (perfshin ekstensionin, psh.
            '.png') e imazhit.
        """
        file_name = os.path.join(os.path.dirname(__file__),
                                 'images', img_file_name)
        img = pygame.image.load(file_name)
        img.convert()
        return img

    background = load_image('tafilkasumaj.png')

    # E bejme qe permasa e imazhit te jete sa e dritares
    background = pygame.transform.scale(background, (screen_width, screen_height))


    return {
            # 'background': background,
            'background': load_image('tafilkasumaj.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),


            'bird-wingup': load_image('bird_wing_up.png'),
            'bird-wingdown': load_image('bird_wing_down.png')}


def frames_to_msec(frames, fps=FPS):

    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):

    return fps * milliseconds / 1000.0


def main():


    pygame.init()

    screen_width, screen_height = 570, 1024

    display_surface = pygame.display.set_mode((screen_width, screen_height))

    pygame.display.set_caption('Tafil Kasumaj')

    clock = pygame.time.Clock()
    score_font = pygame.font.SysFont(None, 32, bold=True)
    images = load_images(screen_width, screen_height)


    bird = Bird(50, int(WIN_HEIGHT/2 - Bird.HEIGHT/2), 10,
                (images['bird-wingup'], images['bird-wingdown']))

    pipes = deque()

    frame_clock = 0 
    score = 0
    done = paused = False



    background = pygame.transform.scale(images['background'], (screen_width, screen_height))





    while not done:
        clock.tick(FPS)

        if not (paused or frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)):
            pp = PipePair(images['pipe-end'], images['pipe-body'])
            pipes.append(pp)

        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
            elif e.type == MOUSEBUTTONUP or (e.type == KEYUP and
                    e.key in (K_UP, K_RETURN, K_SPACE)):
                bird.msec_to_climb = Bird.CLIMB_DURATION

        if paused:
            continue 

        pipe_collision = any(p.collides_with(bird) for p in pipes)
        if pipe_collision or 0 >= bird.y or bird.y >= WIN_HEIGHT - Bird.HEIGHT:
            done = True

        display_surface.blit(background, (0, 0))


        while pipes and not pipes[0].visible:
            pipes.popleft()

        for p in pipes:
            p.update()
            display_surface.blit(p.image, p.rect)

        bird.update()
        display_surface.blit(bird.image, bird.rect)

        # piket
        for p in pipes:
            if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                score += 1
                p.score_counted = True

        score_surface = score_font.render(str(score), True, (255, 255, 255))
        score_x = WIN_WIDTH/2 - score_surface.get_width()/2
        display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))

        pygame.display.flip()
        frame_clock += 1
    print('Game over! Score: %i' % score)
    pygame.quit()


if __name__ == '__main__':

    main()
