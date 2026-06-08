"""Simple sprite pools for high-churn entities."""

from __future__ import annotations


class SpritePool:
    def __init__(self):
        self._pools: dict[type, list] = {}

    def acquire(self, cls, *args, **kwargs):
        pool = self._pools.get(cls)
        if pool:
            sprite = pool.pop()
            sprite.reset(*args, **kwargs)
            return sprite
        return cls(*args, **kwargs)

    def release(self, sprite):
        pool = self._pools.setdefault(type(sprite), [])
        pool.append(sprite)


bullet_pool = SpritePool()
sun_pool = SpritePool()
fume_pool = SpritePool()
