"""Which side-view image to show for a truck: a display convention, not trailer data."""
from __future__ import annotations

from enum import Enum

TRAILER_LICENSE = "CE"

VISUAL_CONVENTION_NOTE = (
    "Illustrative image. A trailer is drawn when the truck requires licence CE and has an "
    "In Transit job. The database stores no trailer records."
)


class VisualConfig(str, Enum):
    """Available illustration variants for a truck side-view image."""

    TRACTOR_ONLY = "tractor"
    TRACTOR_WITH_TRAILER = "trailer"


def choose_visual_config(required_license: str | None, has_in_transit_job: bool) -> VisualConfig:
    """Choose the trailer illustration only for an in-transit CE truck."""
    if has_in_transit_job and (required_license or "").strip().upper() == TRAILER_LICENSE:
        return VisualConfig.TRACTOR_WITH_TRAILER
    return VisualConfig.TRACTOR_ONLY
