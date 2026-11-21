from campuslink.app.config import AppSettings, SettingsStore


def test_settings_round_trip(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    expected = AppSettings(theme="dark", discoverable=True)
    store.save(expected)
    assert store.load() == expected


def test_corrupt_settings_fall_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("not-json", encoding="utf-8")
    assert SettingsStore(path).load() == AppSettings()

