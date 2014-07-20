'''
Catchem game.
'''
from __future__ import division

from math import cos, sin, fabs, pi
from random import randint
from os.path import join as pjoin

import sys

import sfml as sf

# work around for rectangle intersects bug
def intersects(rect1, rect2):
    '''
    Bug workaround for sf.Rectangle.intersects not working
    '''
    # make sure the rectangle is a rectangle (to get its right/bottom border)
    l, t, w, h = rect2
    rect2 = sf.Rectangle((l, t), (w, h))

    # compute the intersection boundaries
    left = max(rect1.left, rect2.left)
    top = max(rect1.top, rect2.top)
    right = min(rect1.right, rect2.right)
    bottom = min(rect1.bottom, rect2.bottom)

    # if the intersection is valid (positive non zero area), then
    # there is an intersection
    if left < right and top < bottom:
        return sf.Rectangle((left, top), (right-left, bottom-top))

def sub_rectangle(rect, amount=25):
    return sf.Rectangle((rect.left + amount,
                         rect.top + amount),
                        (rect.width - amount,
                         rect.height - amount))

class Blob(object):
    def __init__(self, speed=None, app=None):
        self.rectangle = sf.RectangleShape()
        r = self.rectangle
        r.size = sf.Vector2(10,10)
        r.outline_color = sf.Color.BLACK
        r.outline_thickness = 3
        r.fill_color = sf.Color(212, 0, 255)
        r.origin = r.size / 2
        r.position = sf.Vector2(randint(0,App.WIDTH - 1),1)
        self.speed = speed if speed else (App.BLOB_SPEED * randint(1,10))
        self.app = app if app else App.a
        
    def update(self):
        # move the blob down
        distance = 5000 * self.app.seconds * self.speed
        distance = distance if distance > 0.01 else 0.01
        self.rectangle.position += sf.Vector2(0,distance)

class BlobGroup(object):
    def __init__(self, speed=None, app=None):
        self.blobs = set()
        self.speed = speed if speed else App.BLOB_SPEED
        self.app = app if app else App.a

    def __iter__(self):
        return iter(self.blobs)

    def add(self, blob):
        self.blobs.add(blob)

    def update(self):
        for blob in self.blobs.copy():
            blob.update()
            if blob.rectangle.position.y > (App.HEIGHT - App.GROUND_HEIGHT):
                App.sounds[['splat1','splat2'][randint(0,1)]].play()
                self.blobs.remove(blob)        

    def draw(self, window):
        for blob in self.blobs:
            window.draw(blob.rectangle)        

class Player(object):
    def __init__(self, speed=None, app=None):
        texture = sf.Texture.from_file(pjoin('data','goof-car.png'))
        self.sprite = sf.Sprite(texture)
        self.sprite.position = sf.Vector2(App.WIDTH / 2,
                                          App.HEIGHT - App.GROUND_HEIGHT
                                          - App.PLY_HEIGHT / 2)
        self.color = sf.Color.RED
        self.tdelta = 0.
        self.speed = speed if speed else App.PLY_SPEED
        self.flipped = False
        self.app = app if app else App.a

    def update(self):
        if sf.Keyboard.is_key_pressed(sf.Keyboard.LEFT):
            self.move(sf.Keyboard.LEFT)
        elif sf.Keyboard.is_key_pressed(sf.Keyboard.RIGHT):
            self.move(sf.Keyboard.RIGHT)

        if self.is_hit():
            print "Hit!"
            App.sounds['fart'].play()
            while App.sounds['fart'].status: pass
            sys.exit(1)

    def flip_texture(self, direction):
        self.sprite.scale(sf.Vector2(-1,1))
        # move the sprite because mirror scaling moves texture
        # rectangle one play width over
        self.sprite.move(sf.Vector2({sf.Keyboard.LEFT: -1,
                                     sf.Keyboard.RIGHT: 1}[direction]
                                    *  self.sprite.texture_rectangle.width, 0))

    def move(self, direction):
        # check time delta to curb speed
        self.tdelta += self.app.seconds
        r = self.sprite

        if self.tdelta > self.speed:
            self.tdelta = 0.
            # TODO: parameterize movement amount
            if direction == sf.Keyboard.LEFT:
                if self.flipped:
                    self.flipped = False
                    self.flip_texture(direction)
                    
                vector = sf.Vector2(-1,0)
            elif direction == sf.Keyboard.RIGHT:
                if not self.flipped:
                    self.flipped = True
                    self.flip_texture(direction)
                vector = sf.Vector2(1,0)
            r.position = r.position + vector

        if self.is_out_of_bounds():
            # undo move if out of bounds
            r.position = r.position - vector

    def is_out_of_bounds(self):
        #r = self.rectangle
        r = self.sprite
        return r.position.x < 0 or (r.position.x) > App.WIDTH

    def is_hit(self):
        player_bounds = sub_rectangle(self.sprite.global_bounds)
        for blob in self.app.blob_group:
            blob_bounds = blob.rectangle.global_bounds
            if intersects(player_bounds, blob_bounds):
                return True
        return False

class App(object):
    '''
    Main app class.  Acts on a object tree structure for child objects
    to obtain references to global assets and is responsible for
    drawing.
    '''
        
    WIDTH = 800
    HEIGHT = 450
    GROUND_HEIGHT = 30
    BLOB_SPEED = 0.008
    PLY_SPEED = 0.002
    PLY_HEIGHT = 62
    PLY_WIDTH = 57
    a = None

    sounds = {
        'fart': sf.Sound(sf.SoundBuffer.from_file('data/bigfart.wav')),
        'splat1': sf.Sound(sf.SoundBuffer.from_file('data/splat1.wav')),
        'splat2': sf.Sound(sf.SoundBuffer.from_file('data/splat2.wav')),
        'bgm1': sf.Sound(sf.SoundBuffer.from_file('data/RP-InTheField.ogg'))
    }

    @staticmethod
    def init():
        App.a = App()
        App.a.setup()
        
    def setup(self):
        '''
        This method is used to setup the app object rather
        thin __init__ because some of these child objects expect
        App.a to contain the global app reference upon construction
        (unless an explicit app=app was passed in their arguments)
        however, App.a isn't set until App.__init__ completes.
        '''
        self.mode = sf.VideoMode(App.WIDTH, App.HEIGHT)
        self.window = sf.RenderWindow(self.mode, "Catch 'em")
        self.blob_group = BlobGroup()
        self.clock = sf.Clock()
        self.ground = self.get_ground()
        self.player = Player()
        self.clear()
        App.sounds['bgm1'].play()

    def get_ground(self):
        r = sf.RectangleShape()
        r.size = sf.Vector2(App.WIDTH,App.GROUND_HEIGHT)
        r.outline_color = sf.Color.BLACK
        r.outline_thickness = 1
        r.fill_color = sf.Color.GREEN
        r.origin = r.size / 2
        r.position = sf.Vector2(App.WIDTH / 2,
                                App.HEIGHT - App.GROUND_HEIGHT / 2)
        return r

    def clear(self):
        self.window.clear(sf.Color(0,102,133))

    def update(self):
        self.seconds = self.clock.restart().seconds
        self.player.update()
        self.blob_group.update()
        self.blob_group.draw(self.window)
        self.window.draw(self.ground)
        #self.window.draw(self.player.rectangle)
        self.window.draw(self.player.sprite)

def main():
    App.init()
    app = App.a
    while app.window.is_open:
        # handle events
        for event in app.window.events:
            # window closed or escape key pressed: exit
            if type(event) is sf.CloseEvent:
                app.window.close()
            if type(event) is sf.KeyEvent and event.code is sf.Keyboard.ESCAPE:
                app.window.close()

        if randint(1,1000) == 1:
            app.blob_group.add(Blob())

        app.clear()
        app.update()
        app.window.display()
    
if __name__ == '__main__': main()
