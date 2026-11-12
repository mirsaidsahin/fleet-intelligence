from io import BytesIO

import pytest
from PIL import Image

from services import image_assets


def image_bytes(image_format="PNG"):
    stream = BytesIO()
    Image.new("RGB", (2, 2), color="steelblue").save(stream, format=image_format)
    return stream.getvalue()


def test_driver_upload_stores_png_and_replaces_other_extensions(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    old = tmp_path / "assets" / "drivers" / "12.jpg"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"old")

    saved = image_assets.save_uploaded_image("drivers", 12, image_bytes())

    assert saved == tmp_path / "assets" / "drivers" / "12.png"
    assert saved.read_bytes() == image_bytes()
    assert not old.exists()


def test_brand_and_truck_uploads_follow_asset_names(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    png = image_bytes()
    assert image_assets.save_uploaded_image("brands", 3, png).name == "3.png"
    assert image_assets.save_uploaded_image("trucks", 8, png, "trailer").name == "8_trailer.png"


def test_driver_jpeg_upload_and_replacement_keep_only_latest_format(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    folder = tmp_path / "assets" / "drivers"
    folder.mkdir(parents=True)
    old_png = folder / "5.png"
    old_png.write_bytes(b"old png")

    jpeg_bytes = image_bytes("JPEG")
    saved = image_assets.save_uploaded_image("drivers", 5, jpeg_bytes)

    assert saved == folder / "5.jpg"
    assert saved.read_bytes() == jpeg_bytes
    assert not old_png.exists()


def test_replacing_brand_and_truck_view_overwrites_only_matching_asset(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    png = image_bytes()
    brand = image_assets.save_uploaded_image("brands", 3, png + b"first")
    image_assets.save_uploaded_image("trucks", 8, png + b"tractor", "tractor")
    trailer = image_assets.save_uploaded_image("trucks", 8, png + b"trailer", "trailer")

    replaced_brand = image_assets.save_uploaded_image("brands", 3, png + b"updated")
    image_assets.save_uploaded_image("trucks", 8, png + b"updated tractor", "tractor")

    assert replaced_brand == brand and brand.read_bytes() == png + b"updated"
    assert (tmp_path / "assets" / "trucks" / "by_truck" / "8_tractor.png").read_bytes() == png + b"updated tractor"
    assert trailer.read_bytes() == png + b"trailer"


def test_driver_lookup_checks_supported_extensions_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    folder = tmp_path / "assets" / "drivers"
    folder.mkdir(parents=True)
    jpeg = folder / "11.jpeg"
    jpeg.write_bytes(b"jpeg")

    assert image_assets.driver_image(11) == jpeg
    assert image_assets.driver_image(12) is None


@pytest.mark.parametrize(
    ("category", "entity_id", "data", "visual"),
    [
        ("drivers", 1, b"not an image", None),
        ("brands", 1, b"\xff\xd8\xffjpeg", None),
        ("trucks", 1, b"\x89PNG\r\n\x1a\nimage", "wrong"),
        ("drivers", 0, b"\x89PNG\r\n\x1a\nimage", None),
    ],
)
def test_invalid_uploads_are_rejected(tmp_path, monkeypatch, category, entity_id, data, visual):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ValueError):
        image_assets.save_uploaded_image(category, entity_id, data, visual)


def test_large_upload_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ValueError, match="10 MB"):
        image_assets.save_uploaded_image("drivers", 2, b"\x89PNG\r\n\x1a\n" + b"x" * (10 * 1024 * 1024))


@pytest.mark.parametrize(
    ("category", "entity_id", "data", "visual"),
    [
        ("unknown", 1, image_bytes(), None),
        ("drivers", True, image_bytes(), None),
        ("drivers", 1, b"", None),
        ("drivers", 1, b"\xff\xd8\xff", None),
        ("brands", 1, image_bytes("JPEG"), None),
        ("trucks", 1, image_bytes(), None),
    ],
)
def test_rejects_unsupported_category_id_or_image_variant(tmp_path, monkeypatch, category, entity_id, data, visual):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ValueError):
        image_assets.save_uploaded_image(category, entity_id, data, visual)
    assert not (tmp_path / "assets").exists()
