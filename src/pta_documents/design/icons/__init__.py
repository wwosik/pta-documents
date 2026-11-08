"""The bundled stroke icons: a subset of Tabler Icons for consulting and IT (E15-S03).

The SVGs are the files of ``icons/outline/`` of the npm package ``@tabler/icons`` version
``TABLER_VERSION``, unchanged; MIT licence in ``LICENSE-tabler-icons.txt`` next to them
(package data, read through ``importlib.resources``). Each is a 24 × 24 grid of ``<path>``
outlines, stroked 2 px with round ends and joins, not filled. In Markdown an icon is
``:icon-check:`` (``markdown.icon``); ``loader.drawing`` makes a ``Drawing`` of it,
``raster.png`` a PNG without any extra.
"""

from __future__ import annotations

import difflib
from importlib import resources
from typing import Final

TABLER_VERSION: Final = "3.50.0"
LICENSE_FILE: Final = "LICENSE-tabler-icons.txt"
GRID: Final = 24
"""The width and height of every icon's ``viewBox``."""
STROKE_WIDTH: Final = 2.0
"""The line width of the icons on their grid."""

ICONS: Final = (
    "access-point",
    "adjustments",
    "alert-circle",
    "alert-triangle",
    "api",
    "arrow-down",
    "arrow-left",
    "arrow-right",
    "arrow-up",
    "arrows-exchange",
    "award",
    "ban",
    "bell",
    "bolt",
    "book",
    "brain",
    "briefcase",
    "bug",
    "building",
    "building-community",
    "bulb",
    "calculator",
    "calendar",
    "calendar-event",
    "cash",
    "certificate",
    "chart-bar",
    "chart-dots",
    "chart-line",
    "chart-pie",
    "check",
    "checklist",
    "circle-check",
    "circle-x",
    "clipboard-check",
    "clipboard-list",
    "clock",
    "cloud",
    "cloud-download",
    "cloud-upload",
    "code",
    "coin",
    "compass",
    "components",
    "copyright",
    "cpu",
    "currency-euro",
    "database",
    "device-desktop",
    "device-laptop",
    "device-mobile",
    "download",
    "edit",
    "eye",
    "file",
    "file-check",
    "file-text",
    "files",
    "filter",
    "flag",
    "flame",
    "flask",
    "folder",
    "folder-open",
    "gavel",
    "git-branch",
    "git-merge",
    "globe",
    "hand-stop",
    "headset",
    "heart",
    "heart-handshake",
    "help-circle",
    "hierarchy",
    "hierarchy-2",
    "home",
    "hourglass",
    "id-badge-2",
    "infinity",
    "info-circle",
    "key",
    "layers-intersect",
    "layout-dashboard",
    "leaf",
    "license",
    "lifebuoy",
    "link",
    "list-check",
    "loader",
    "lock",
    "lock-open",
    "mail",
    "map",
    "map-pin",
    "message",
    "message-circle",
    "messages",
    "microscope",
    "minus",
    "mood-sad",
    "mood-smile",
    "network",
    "notebook",
    "package",
    "pencil",
    "percentage",
    "phone",
    "player-pause",
    "player-play",
    "plug",
    "plus",
    "presentation",
    "printer",
    "progress",
    "puzzle",
    "receipt",
    "recycle",
    "refresh",
    "repeat",
    "report-analytics",
    "report-money",
    "robot",
    "rocket",
    "rotate",
    "route",
    "scale",
    "school",
    "search",
    "server",
    "server-2",
    "settings",
    "share",
    "shield",
    "shield-check",
    "shopping-cart",
    "sitemap",
    "sort-ascending",
    "sparkles",
    "square-check",
    "star",
    "target",
    "target-arrow",
    "terminal-2",
    "test-pipe",
    "thumb-down",
    "thumb-up",
    "tool",
    "tools",
    "trash",
    "trending-down",
    "trending-up",
    "truck",
    "upload",
    "user",
    "user-check",
    "users",
    "users-group",
    "wifi",
    "world",
    "writing",
    "x",
    "zoom-check",
)
"""Every bundled icon by name, in alphabetical order: the files are ``<name>.svg``."""

_KNOWN: Final = frozenset(ICONS)


def is_icon(name: str) -> bool:
    return name in _KNOWN


def svg(name: str) -> bytes:
    """The SVG of the icon ``name`` as bundled; ``KeyError`` for an unknown name."""
    if name not in _KNOWN:
        raise KeyError(name)
    return (resources.files(__name__) / f"{name}.svg").read_bytes()


def license_text() -> str:
    """The licence of the icon set (MIT), as bundled."""
    return (resources.files(__name__) / LICENSE_FILE).read_text(encoding="utf-8")


def suggestions(name: str) -> list[str]:
    """The (up to) three bundled names most like ``name``, best first."""
    return difflib.get_close_matches(name, ICONS, n=3, cutoff=0.5)


ALT_PREFIX: Final = "icon:"
"""The alternative text of an icon's picture or shape group is ``icon:check``: the converters
read it back as ``:icon-check:``."""


def alt(name: str) -> str:
    """The alternative text of the icon ``name``'s picture: ``icon:name``."""
    return ALT_PREFIX + name


def from_alt(text: str | None) -> str | None:
    """The name of a bundled icon in an alternative text ``icon:check``; None for any other."""
    if text is None or not text.startswith(ALT_PREFIX):
        return None
    name = text[len(ALT_PREFIX) :]
    return name if is_icon(name) else None


def colored_svg(name: str, color: str) -> bytes:
    """The SVG of the icon ``name`` stroked in ``color`` (``RRGGBB``) instead of
    ``currentColor``."""
    return svg(name).replace(b'"currentColor"', f'"#{color}"'.encode("ascii"))


def unknown(name: str) -> str:
    """The reason an unknown icon is refused, with the names it may have meant."""
    close = suggestions(name)
    hint = (
        f" Did you mean {', '.join(f':icon-{c}:' for c in close)}?"
        if close
        else " The authoring guide lists every icon."
    )
    return f"Unknown icon ':icon-{name}:'.{hint}"
