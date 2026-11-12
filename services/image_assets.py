"""Resolve optional local portraits and vehicle images without bundling third-party art."""
from pathlib import Path
from io import BytesIO
import os
from tempfile import NamedTemporaryFile

from PIL import Image, UnidentifiedImageError

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
    folder = PROJECT_ROOT / "assets" / "brands"
    return _first([folder / f"{brand_id}.png"])


def truck_image(truck_id: int, brand_id: int | None, visual: str) -> Path | None:
    """Prefer a truck-specific image, then brand artwork, then a shared default."""
    folder = PROJECT_ROOT / "assets" / "trucks"
    candidates = [folder / "by_truck" / f"{truck_id}_{visual}.png", folder / "by_truck" / f"{truck_id}_{visual}.jpg"]
    if brand_id is not None:
        candidates.extend((folder / "by_brand" / f"{brand_id}_{visual}.png", folder / "by_brand" / f"{brand_id}_{visual}.jpg"))
    candidates.extend((folder / f"default_{visual}.png", folder / f"default_{visual}.jpg"))
    return _first(candidates)


def save_uploaded_image(category: str, entity_id: int, data: bytes, visual: str | None = None) -> Path:
    """Validate image bytes and save to the documented local asset convention."""
    if type(entity_id) is not int or entity_id < 1:
        raise ValueError("Invalid record ID")
    if not data or len(data) > 10 * 1024 * 1024:
        raise ValueError("Choose an image smaller than 10 MB")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        # Detect PNG from its file signature before inspecting its decoded content.
        extension = ".png"
    elif data.startswith(b"\xff\xd8\xff"):
        # Normalize both JPEG upload extensions to the app's .jpg convention.
        extension = ".jpg"
    else:
        raise ValueError("Only valid PNG and JPEG images are supported")
    try:
        # Pillow verifies the file structure so a matching header alone is insufficient.
        with Image.open(BytesIO(data)) as image:
            if image.format != ("PNG" if extension == ".png" else "JPEG"):
                raise ValueError("Image content does not match its file format")
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError("The selected file is not a valid image") from exc

    # Resolve the destination and old variants from the selected entity type.
    root = PROJECT_ROOT / "assets"
    if category == "drivers":
        target = root / "drivers" / f"{entity_id}{extension}"
        previous = [root / "drivers" / f"{entity_id}{ext}" for ext in _EXTENSIONS]
    elif category == "brands":
        if extension != ".png":
            raise ValueError("Brand logos must be PNG images")
        target = root / "brands" / f"{entity_id}.png"
        previous = [target]
    elif category == "trucks":
        if extension != ".png" or visual not in ("tractor", "trailer"):
            raise ValueError("Truck images must be PNG and use a valid vehicle view")
        target = root / "trucks" / "by_truck" / f"{entity_id}_{visual}.png"
        previous = [target]
    else:
        raise ValueError("Unsupported image category")

    # Keep the temporary file beside the target so os.replace stays atomic.
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="wb", dir=target.parent, prefix=f".{target.stem}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        # Replace the target only after the complete upload has been written.
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    # Remove old driver formats only after the new image is safely in place.
    for old in previous:
        if old != target and old.is_file():
            old.unlink()
    return target
