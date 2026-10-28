"""Structural checks for the Fleet protocol: leaflow/fleet, the machines and
their sessions, and leaflow/virtualdesktop, the desktop feature of sessions.

The packages form layers. A package may import only the packages listed for it
below, so that dependencies point one way: the desktop builds on the session
layer and never the other way round, the peer-to-peer packages never depend on
the control plane, and no domain depends on another one it does not build on.
A new package is added to the table on purpose, together with what it may
import.
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
FAMILIES = ("fleet", "virtualdesktop")

DISPLAY = {"virtualdesktop.display"}

# Package -> the packages it may import, as "<family>.<package>".
ALLOWED_IMPORTS: dict[str, set[str]] = {
    # Fleet, the session layer: what travels end to end between a viewer and
    # a session, with or without a desktop.
    "fleet.rpc": set(),
    "fleet.transport": set(),
    "fleet.session": set(),
    "fleet.terminal": set(),
    "fleet.exec": set(),
    "fleet.filetransfer": set(),
    "fleet.portforward": set(),
    "fleet.sshagent": set(),
    "fleet.privilege": set(),
    "fleet.logs": set(),
    # Fleet, the control plane: endpoints and the service.
    "fleet.control": {"fleet.rpc", "fleet.transport", "fleet.session"},
    "fleet.machine": set(),
    "fleet.directory": set(),
    "fleet.command": set(),
    "fleet.host": set(),
    # VirtualDesktop: the desktop. Who operates it.
    "virtualdesktop.lease": {"fleet.session"},
    # The canvas, and the desktop domains on its coordinates and images.
    "virtualdesktop.display": set(),
    "virtualdesktop.window": DISPLAY,
    "virtualdesktop.draw": DISPLAY,
    "virtualdesktop.input": DISPLAY,
    "virtualdesktop.cursor": DISPLAY,
    "virtualdesktop.tray": DISPLAY,
    "virtualdesktop.application": DISPLAY,
    "virtualdesktop.notification": DISPLAY,
    "virtualdesktop.capture": DISPLAY,
    "virtualdesktop.accessibility": DISPLAY,
    # What changed across the desktop domains.
    "virtualdesktop.change": {
        "virtualdesktop.display",
        "virtualdesktop.window",
        "virtualdesktop.accessibility",
        "virtualdesktop.tray",
        "virtualdesktop.notification",
    },
    # Copy and paste and drag and drop, which move files too.
    "virtualdesktop.datatransfer": {"fleet.filetransfer"},
    # Device redirection, and the devices built on it.
    "virtualdesktop.device": set(),
    "virtualdesktop.audio": {"virtualdesktop.device"},
    "virtualdesktop.camera": {"virtualdesktop.device"},
    "virtualdesktop.gamepad": {"virtualdesktop.device"},
    "virtualdesktop.printing": set(),
    # What a desktop session is opened with and reports, carried by
    # fleet.host as google.protobuf.Any.
    "virtualdesktop.host": DISPLAY,
}

CONTROL_PLANE = {"fleet.control", "fleet.machine", "fleet.directory", "fleet.command", "fleet.host"}

CONTAINER_WORDS = {"common", "shared", "types", "type", "util", "utils", "misc", "base"}
IMPORT = re.compile(r'^import\s+(?:public\s+)?"([^"]+)";', re.MULTILINE)
PACKAGE = re.compile(r"^package\s+([\w.]+);", re.MULTILINE)
GO_PACKAGE = re.compile(r'^option go_package = "([^"]+)";', re.MULTILINE)
# Public contracts cite public standards only, never documents of our own.
LOCAL_DOCUMENT = re.compile(r"\b[\w-]+\.md\b|\bglossary\b|\barchitecture\s*§|\breview-v1\b", re.IGNORECASE)


def proto_files() -> list[Path]:
    return sorted(path for family in FAMILIES for path in (ROOT / "leaflow" / family).glob("*/v1/*.proto"))


def name_of(path: Path) -> str:
    """ "fleet.session" for leaflow/fleet/session/v1/session.proto."""
    family, package = path.relative_to(ROOT / "leaflow").parts[:2]
    return f"{family}.{package}"


class FleetContract(unittest.TestCase):
    def test_there_are_packages(self) -> None:
        for family in FAMILIES:
            with self.subTest(family=family):
                self.assertTrue(list((ROOT / "leaflow" / family).glob("*/v1/*.proto")), f"no .proto files in {family}")

    def test_every_package_is_registered(self) -> None:
        for path in proto_files():
            with self.subTest(path=path.name):
                self.assertIn(name_of(path), ALLOWED_IMPORTS, "add the package to ALLOWED_IMPORTS")

    def test_no_container_packages(self) -> None:
        for name in ALLOWED_IMPORTS:
            self.assertNotIn(name.split(".")[1], CONTAINER_WORDS, f"{name} names no domain")

    def test_package_matches_directory(self) -> None:
        for path in proto_files():
            with self.subTest(path=str(path.relative_to(ROOT))):
                match = PACKAGE.search(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(match, "missing package")
                self.assertEqual(match.group(1), f"leaflow.{name_of(path)}.v1")

    def test_go_package_matches_directory(self) -> None:
        # leaflow-go has one Go module per directory of leaflow/: the fleet
        # module holds the Fleet packages next to the generated REST package
        # fleet/v1/server, and the virtualdesktop module the desktop's.
        for path in proto_files():
            with self.subTest(path=str(path.relative_to(ROOT))):
                match = GO_PACKAGE.search(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(match, "missing go_package")
                family, package = name_of(path).split(".")
                self.assertEqual(
                    match.group(1),
                    f"github.com/leaflowapis/leaflow-go/{family}/{package}/v1;{package}v1",
                )

    def test_imports_follow_the_layers(self) -> None:
        for path in proto_files():
            name = name_of(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                for imported in IMPORT.findall(path.read_text(encoding="utf-8")):
                    if imported.startswith("google/"):
                        continue
                    parts = imported.split("/")
                    self.assertEqual(parts[0], "leaflow", f"imports {imported}")
                    self.assertIn(parts[1], FAMILIES, f"imports {imported}")
                    target = f"{parts[1]}.{parts[2]}"
                    if target == name:
                        continue
                    self.assertIn(target, ALLOWED_IMPORTS.get(name, set()), f"{name} may not import {target}")

    def test_fleet_never_imports_the_desktop(self) -> None:
        for name, imported in ALLOWED_IMPORTS.items():
            if name.startswith("fleet."):
                with self.subTest(package=name):
                    self.assertFalse(
                        {target for target in imported if target.startswith("virtualdesktop.")},
                        f"{name} may not depend on the desktop",
                    )

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
