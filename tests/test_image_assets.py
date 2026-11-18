from services import image_assets


def test_driver_lookup_checks_supported_extensions_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(image_assets, "PROJECT_ROOT", tmp_path)
    folder = tmp_path / "assets" / "drivers"
    folder.mkdir(parents=True)
    jpeg = folder / "11.jpeg"
    jpeg.write_bytes(b"jpeg")

    assert image_assets.driver_image(11) == jpeg
    assert image_assets.driver_image(12) is None

