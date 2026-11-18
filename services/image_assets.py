"""Resolve optional local portraits and vehicle images without bundling third-party art."""
from pathlib import Path

from utils.config import PROJECT_ROOT

_EXTENSIONS = (".png", ".jpg", ".jpeg")


def _first(paths: list[Path]) -> Path | None:
    """Return the first existing asset candidate, preserving the documented priority."""
    return next((path for path in paths if path.is_file()), None)


def driver_image(driver_id: int) -> Path | None:
    """Find a driver's local portrait in the supported extension order."""
    folder = PROJECT_ROOT / "assets" / "drivers"
    return _first([folder / f"{driver_id}{ext}" for ext in _EXTENSIONS])


def brand_image(brand_id: int | None) -> Path | None:
    """Resolve a brand's optional PNG logo, or return None when no brand is selected."""
    if brand_id is None:
        return None
    path = PROJECT_ROOT / "assets" / "brands" / f"{brand_id}.png"
    return path if path.is_file() else None


def truck_image(truck_id: int, brand_id: int | None) -> Path | None:
    """Prefer a truck-specific image, then brand artwork, then a shared default."""
    folder = PROJECT_ROOT / "assets" / "trucks"
    candidates = [folder / "by_truck" / f"{truck_id}_tractor.png", folder / "by_truck" / f"{truck_id}_tractor.jpg"]
    if brand_id is not None:
        candidates.extend((folder / "by_brand" / f"{brand_id}_tractor.png", folder / "by_brand" / f"{brand_id}_tractor.jpg"))
    candidates.extend((folder / "default_tractor.png", folder / "default_tractor.jpg"))
    return _first(candidates)
