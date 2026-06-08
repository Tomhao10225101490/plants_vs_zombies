"""Shared sprite frame caches to avoid per-instance surface duplication."""

from __future__ import annotations

from . import tool

_CROPPED_FRAMES: dict[tuple, list] = {}
_ROTATED_FRAMES: dict[tuple, object] = {}
_HYPNO_FLIP_FRAMES: dict[tuple, object] = {}


def get_cropped_frames(
    name: str,
    x: int,
    y: int,
    width: int,
    height: int,
    colorkey,
    scale: int = 1,
) -> list:
    key = (name, x, y, width, height, colorkey, scale)
    if key not in _CROPPED_FRAMES:
        frame_list = tool.GFX[name]
        _CROPPED_FRAMES[key] = [
            tool.get_image(frame, x, y, width, height, colorkey, scale)
            for frame in frame_list
        ]
    return _CROPPED_FRAMES[key]


def get_rotated_frame(frame, degree: int):
    key = (id(frame), degree)
    if key not in _ROTATED_FRAMES:
        import pygame as pg

        _ROTATED_FRAMES[key] = pg.transform.rotate(frame, degree)
    return _ROTATED_FRAMES[key]


def get_hypno_flipped_frame(frame):
    key = id(frame)
    if key not in _HYPNO_FLIP_FRAMES:
        import pygame as pg

        _HYPNO_FLIP_FRAMES[key] = pg.transform.flip(frame, True, False)
    return _HYPNO_FLIP_FRAMES[key]
