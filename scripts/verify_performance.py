#!/usr/bin/env python3
"""Lightweight verification for performance modules (no game resources required)."""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from source import constants as c
from source.pool import SpritePool


def test_lazy_sound():
    sound = c.LazySound('tap.ogg')
    assert sound._sound is None
    sound_path = os.path.join(c._SOUND_DIR, 'tap.ogg')
    if os.path.exists(sound_path):
        import pygame as pg

        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
        try:
            pg.mixer.init()
            sound.set_volume(0.5)
            assert sound._sound is not None
            pg.mixer.quit()
        except pg.error:
            print('lazy sound: skipped (no audio device)')
            return
    print('lazy sound: ok')


def test_sprite_pool():
    class Dummy:
        def __init__(self, value):
            self.value = value

        def reset(self, value):
            self.value = value

    pool = SpritePool()
    a = pool.acquire(Dummy, 1)
    assert a.value == 1
    pool.release(a)
    b = pool.acquire(Dummy, 2)
    assert b is a and b.value == 2
    print('sprite pool: ok')


def test_constants():
    assert c.SHOW_FPS is False
    assert len(c.SOUNDS) > 0
    assert isinstance(c.SOUNDS[0], c.LazySound)
    print('constants: ok')


def main():
    start = time.perf_counter()
    test_constants()
    test_lazy_sound()
    test_sprite_pool()
    elapsed = time.perf_counter() - start
    print(f'verification completed in {elapsed:.3f}s')


if __name__ == '__main__':
    main()
