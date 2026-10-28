"""Structural checks for the VirtualDesktop protocol under leaflow/virtualdesktop.

The packages form layers. A package may import only the packages listed for it
below, so that the peer-to-peer side never depends on the service side and no
domain depends on another one it does not build on. A new package is added to
the table on purpose, together with what it may import.

The control plane, between endpoints and the VirtualDesktop service, sits on
top: it may import peer-to-peer packages, and none of them imports it.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = (
    Path(sys.argv.pop(1)).resolve()
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-")
    else Path(__file__).resolve().parents[1]
)
PROTOCOL = ROOT / "leaflow" / "virtualdesktop"
PREFIX = "leaflow.virtualdesktop."

DISPLAY = {"display"}

# Package -> the packages it may import.
ALLOWED_IMPORTS: dict[str, set[str]] = {
    # Foundations: no imports.
    "rpc": set(),
    "transport": set(),
    "session": set(),
    "display": set(),
    # Desktop domains build on the display's coordinates and images.
    "window": DISPLAY,
    "draw": DISPLAY,
    "input": DISPLAY,
    "cursor": DISPLAY,
    "tray": DISPLAY,
    "application": DISPLAY,
    "notification": DISPLAY,
    "capture": DISPLAY,
    "accessibility": DISPLAY,
    # What changed across the desktop domains.
    "change": {"display", "window", "accessibility", "tray", "notification"},
    # Files, and copy and paste and drag and drop, which move files too.
    "filetransfer": set(),
    "datatransfer": {"filetransfer"},
    # Device redirection, and the devices built on it.
    "device": set(),
    "audio": {"device"},
    "camera": {"device"},
    "gamepad": {"device"},
    # Independent domains.
    "terminal": set(),
    "command": set(),
    "portforward": set(),
    "sshagent": set(),
    "printing": set(),
    "logs": set(),
    "privilege": set(),
    # The control plane: the control connection, authorization and signaling,
    # and the machines with their sessions and users.
    "control": {"rpc", "transport", "session"},
    "machine": {"display"},
}

CONTROL_PLANE = {"control", "machine"}

CONTAINER_WORDS = {"common", "shared", "types", "type", "util", "utils", "misc", "base"}
IMPORT = re.compile(r'^import\s+(?:public\s+)?"([^"]+)";', re.MULTILINE)
PACKAGE = re.compile(r"^package\s+([\w.]+);", re.MULTILINE)
GO_PACKAGE = re.compile(r'^option go_package = "([^"]+)";', re.MULTILINE)
# Public contracts cite public standards only, never documents of our own.
LOCAL_DOCUMENT = re.compile(r"\b[\w-]+\.md\b|\bglossary\b|\barchitecture\s*§|\breview-v1\b", re.IGNORECASE)


def proto_files() -> list[Path]:
    return sorted(PROTOCOL.glob("*/v1/*.proto"))


def package_of(path: Path) -> str:
    return path.relative_to(PROTOCOL).parts[0]


class VirtualDesktopContract(unittest.TestCase):
    def test_there_are_packages(self) -> None:
        self.assertTrue(proto_files(), f"no .proto files under {PROTOCOL}")

    def test_every_package_is_registered(self) -> None:
        for path in proto_files():
            with self.subTest(path=path.name):
                self.assertIn(package_of(path), ALLOWED_IMPORTS, "add the package to ALLOWED_IMPORTS")

    def test_no_container_packages(self) -> None:
        for name in ALLOWED_IMPORTS:
            self.assertNotIn(name, CONTAINER_WORDS, f"{name} names no domain")

    def test_package_matches_directory(self) -> None:
        for path in proto_files():
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text(encoding="utf-8")
                match = PACKAGE.search(text)
                self.assertIsNotNone(match, "missing package")
                self.assertEqual(match.group(1), f"{PREFIX}{package_of(path)}.v1")

    def test_go_package_matches_directory(self) -> None:
        # leaflow-go has one Go module per service. The protocol packages live
        # in the virtualdesktop module, next to the generated REST package
        # virtualdesktop/v1/server, so that one version covers both.
        for path in proto_files():
            with self.subTest(path=str(path.relative_to(ROOT))):
                match = GO_PACKAGE.search(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(match, "missing go_package")
                name = package_of(path)
                self.assertEqual(
                    match.group(1),
                    f"github.com/leaflowapis/leaflow-go/virtualdesktop/{name}/v1;{name}v1",
                )

    def test_imports_follow_the_layers(self) -> None:
        for path in proto_files():
            name = package_of(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                for imported in IMPORT.findall(path.read_text(encoding="utf-8")):
                    if imported.startswith("google/"):
                        continue
                    parts = imported.split("/")
                    self.assertEqual(parts[:2], ["leaflow", "virtualdesktop"], f"imports {imported}")
                    target = parts[2]
                    if target == name:
                        continue
                    self.assertIn(target, ALLOWED_IMPORTS.get(name, set()), f"{name} may not import {target}")

    def test_peer_to_peer_never_imports_the_control_plane(self) -> None:
        for name, imported in ALLOWED_IMPORTS.items():
            if name in CONTROL_PLANE:
                continue
            with self.subTest(package=name):
                self.assertFalse(imported & CONTROL_PLANE, f"{name} may not depend on the control plane")

    def test_no_local_documents(self) -> None:
        for path in proto_files():
            with self.subTest(path=str(path.relative_to(ROOT))):
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    self.assertIsNone(LOCAL_DOCUMENT.search(line), f"line {number} cites a local document: {line.strip()}")


if __name__ == "__main__":
    unittest.main()
