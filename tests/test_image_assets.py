import pytest

from services import image_assets


def test_driver_upload_stores_png_and_replaces_other_extensions(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    old = tmp_path / "assets" / "drivers" / "12.jpg"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"old")

    saved = image_assets.save_uploaded_image("drivers", 12, b"\x89PNG\r\n\x1a\nimage")

    assert saved == tmp_path / "assets" / "drivers" / "12.png"
    assert saved.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert not old.exists()


def test_brand_and_truck_uploads_follow_asset_names(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    png = b"\x89PNG\r\n\x1a\nimage"
    assert image_assets.save_uploaded_image("brands", 3, png).name == "3.png"
    assert image_assets.save_uploaded_image("trucks", 8, png, "trailer").name == "8_trailer.png"


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
