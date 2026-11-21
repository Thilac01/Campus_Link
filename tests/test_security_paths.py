import pytest

from campuslink.security.paths import UnsafePathError, safe_destination


def test_safe_nested_path(tmp_path):
    assert safe_destination(tmp_path, "project/src/main.py") == tmp_path / "project/src/main.py"


@pytest.mark.parametrize("path", ["../secret", "/absolute", "C:/Windows/file", "a/../../b"])
def test_unsafe_paths_are_rejected(tmp_path, path):
    with pytest.raises(UnsafePathError):
        safe_destination(tmp_path, path)
