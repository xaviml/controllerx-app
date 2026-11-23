"""Tests for check_version.py, and for how AwesomeVersion (what Home Assistant
uses to decide whether there's an update) orders app versions.

    python -m unittest discover -s .github/scripts
"""

from __future__ import annotations

import hashlib
import io
import unittest
import zipfile

from check_version import (
    controllerx_errors,
    format_errors,
    is_newer,
    order_errors,
)


class AwesomeVersionTest(unittest.TestCase):
    def test_new_controllerx_version_is_newer(self) -> None:
        self.assertTrue(is_newer("5.3.1-1", "5.3.0"))
        self.assertTrue(is_newer("5.3.1-1", "5.3.0-1"))

    def test_new_app_revision_is_newer(self) -> None:
        self.assertTrue(is_newer("5.3.0-2", "5.3.0-1"))

    def test_revision_after_plain_version_is_older(self) -> None:
        # The case the X.Y.Z-N scheme avoids: SemVer reads "-1" as a
        # pre-release, so 5.3.0-1 comes before 5.3.0.
        self.assertFalse(is_newer("5.3.0-1", "5.3.0"))

    def test_two_digit_revision_is_not_newer(self) -> None:
        # Why N stops at 9
        self.assertTrue(is_newer("5.3.0-9", "5.3.0-8"))
        self.assertFalse(is_newer("5.3.0-10", "5.3.0-9"))


class FormatTest(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(format_errors("5.3.1-1"), [])
        self.assertEqual(format_errors("5.3.1-9"), [])

    def test_invalid(self) -> None:
        for version in ("5.3.1", "v5.3.1-1", "5.3-1", "5.3.1-1-1", "5.3.1-a", "5.3.1-0", "5.3.1-10"):
            with self.subTest(version=version):
                self.assertNotEqual(format_errors(version), [])


class OrderTest(unittest.TestCase):
    TAGS = ["5.2.5", "5.3.0", "5.3.0-1"]

    def test_greater_than_every_tag(self) -> None:
        self.assertEqual(order_errors("5.3.1-1", self.TAGS, release=True), [])

    def test_not_greater_than_plain_tag(self) -> None:
        self.assertNotEqual(order_errors("5.3.0-2", self.TAGS, release=True), [])

    def test_already_released(self) -> None:
        self.assertEqual(order_errors("5.3.0-1", self.TAGS, release=False), [])
        self.assertNotEqual(order_errors("5.3.0-1", self.TAGS, release=True), [])


def make_zip(cx_version: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("cx_version.py", f'__version__ = "{cx_version}"\n')
        archive.writestr("controllerx.py", "")
    return buffer.getvalue()


class ControllerXTest(unittest.TestCase):
    def test_matches(self) -> None:
        data = make_zip("v5.3.1")
        sha256 = hashlib.sha256(data).hexdigest()
        self.assertEqual(controllerx_errors("5.3.1", sha256, data), [])

    def test_other_checksum(self) -> None:
        data = make_zip("v5.3.1")
        self.assertNotEqual(controllerx_errors("5.3.1", "0" * 64, data), [])

    def test_other_controllerx_version(self) -> None:
        data = make_zip("v5.3.0")
        sha256 = hashlib.sha256(data).hexdigest()
        self.assertNotEqual(controllerx_errors("5.3.1", sha256, data), [])


if __name__ == "__main__":
    unittest.main()
