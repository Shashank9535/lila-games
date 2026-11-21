"""Map LILA BLACK world coordinates to the documented logical minimap canvas."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


LOGICAL_MINIMAP_SIZE = 1024


@dataclass(frozen=True)
class MapConfig:
    """World-space calibration supplied in the dataset README."""

    origin_x: float
    origin_z: float
    scale: float


MAP_CONFIGS = {
    "AmbroseValley": MapConfig(origin_x=-370.0, origin_z=-473.0, scale=900.0),
    "GrandRift": MapConfig(origin_x=-290.0, origin_z=-290.0, scale=581.0),
    "Lockdown": MapConfig(origin_x=-500.0, origin_z=-500.0, scale=1000.0),
}


def map_world_position(map_id: str, x: float, z: float) -> dict[str, float | bool]:
    """Return normalized and logical-pixel coordinates for a world position.

    Pixel coordinates use the README's logical 1024x1024 rendering canvas.
    They deliberately do not use, crop, or resize the source minimap images.
    """
    if map_id not in MAP_CONFIGS:
        raise ValueError(f"Unknown or missing map_id: {map_id!r}")
    if not all(isinstance(value, (int, float)) and isfinite(value) for value in (x, z)):
        raise ValueError("x and z must be finite numeric world coordinates")

    config = MAP_CONFIGS[map_id]
    u = (float(x) - config.origin_x) / config.scale
    v = (float(z) - config.origin_z) / config.scale
    return {
        "u": u,
        "v": v,
        "pixel_x": u * LOGICAL_MINIMAP_SIZE,
        "pixel_y": (1.0 - v) * LOGICAL_MINIMAP_SIZE,
        "in_bounds": 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0,
    }
