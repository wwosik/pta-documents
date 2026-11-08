"""A small EMF interpreter for the PTA logos: pure path EMFs without EMF+ become SVG.

It knows exactly the records the logos of the PTA templates use (see E01-S04). Any other record
or an unsupported parameter (stroked pens, hatched brushes, other map modes) raises
``EmfError`` with the record type — nothing is left out silently.

Coordinates: points are logical units; they are mapped through window and viewport to device
units (the unit of the header bounds), and shifted so the header bounds start at 0, 0. The SVG
``viewBox`` is the size of the header bounds.
"""

from __future__ import annotations

import struct
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum


class Record(IntEnum):
    """The EMF record types the interpreter knows."""

    HEADER = 1
    EOF = 14
    SETWINDOWEXTEX = 9
    SETWINDOWORGEX = 10
    SETVIEWPORTEXTEX = 11
    SETVIEWPORTORGEX = 12
    SETMAPMODE = 17
    SETBKMODE = 18
    SETPOLYFILLMODE = 19
    MOVETOEX = 27
    SELECTOBJECT = 37
    CREATEBRUSHINDIRECT = 39
    DELETEOBJECT = 40
    BEGINPATH = 59
    ENDPATH = 60
    CLOSEFIGURE = 61
    FILLPATH = 62
    POLYBEZIERTO16 = 88
    POLYPOLYGON16 = 91
    EXTCREATEPEN = 95


MM_ANISOTROPIC = 8
ALTERNATE = 1
WINDING = 2
BS_SOLID = 0
PS_NULL = 5

SVG_NS = "http://www.w3.org/2000/svg"


class EmfError(ValueError):
    """The EMF uses something this interpreter does not know."""


@dataclass(frozen=True)
class Shape:
    """One filled area: SVG path data in device units, colour ``RRGGBB`` and fill rule."""

    path: str
    color: str
    even_odd: bool


@dataclass(frozen=True)
class Picture:
    """The shapes of an EMF and its size in device units (from the header bounds)."""

    width: float
    height: float
    shapes: tuple[Shape, ...]

    def svg(self, color: Callable[[str], str]) -> bytes:
        """The picture as SVG; ``color`` maps each EMF colour to the colour to write."""
        width, height = number(self.width), number(self.height)
        lines = [
            f'<svg xmlns="{SVG_NS}" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}">'
        ]
        for shape in self.shapes:
            rule = "evenodd" if shape.even_odd else "nonzero"
            lines.append(
                f'<path d="{shape.path}" fill="#{color(shape.color)}" fill-rule="{rule}"/>'
            )
        lines.append("</svg>")
        return ("\n".join(lines) + "\n").encode("utf-8")


def number(value: float) -> str:
    """Fixed formatting: at most three decimals, no trailing zeros, no ``-0``."""
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


@dataclass
class _State:
    left: int = 0
    top: int = 0
    window_origin: tuple[int, int] = (0, 0)
    window_extent: tuple[int, int] = (1, 1)
    viewport_origin: tuple[int, int] = (0, 0)
    viewport_extent: tuple[int, int] = (1, 1)
    map_mode: int | None = None
    even_odd: bool = True
    objects: dict[int, tuple[str, str | None]] = field(
        default_factory=lambda: dict[int, tuple[str, str | None]]()
    )
    brush: str | None = None
    in_path: bool = False
    path: list[str] = field(default_factory=lambda: list[str]())
    shapes: list[Shape] = field(default_factory=lambda: list[Shape]())

    def point(self, x: int, y: int) -> str:
        if self.map_mode != MM_ANISOTROPIC:
            raise EmfError(f"points before SETMAPMODE {MM_ANISOTROPIC} (map mode {self.map_mode})")
        (wx, wy), (ww, wh) = self.window_origin, self.window_extent
        (vx, vy), (vw, vh) = self.viewport_origin, self.viewport_extent
        device_x = (x - wx) * vw / ww + vx
        device_y = (y - wy) * vh / wh + vy
        return f"{number(device_x - self.left)} {number(device_y - self.top)}"

    def fill(self, path: str, record: int) -> None:
        if self.brush is None:
            raise EmfError(f"record {record} fills without a selected brush")
        self.shapes.append(Shape(path, self.brush, self.even_odd))


def read(data: bytes) -> Picture:
    """Interprets the EMF ``data``; raises ``EmfError`` for anything unknown."""
    state = _State()
    width = height = 0
    offset = 0
    ended = False
    while offset < len(data):
        record, size = struct.unpack_from("<II", data, offset)
        if size < 8 or offset + size > len(data):
            raise EmfError(f"record {record} at offset {offset} has a broken size {size}")
        body = data[offset + 8 : offset + size]
        offset += size
        if ended:
            raise EmfError(f"record {record} after EOF")
        if offset == size:
            if record != Record.HEADER:
                raise EmfError(f"the first record is {record}, not the header")
            left, top, right, bottom = struct.unpack_from("<4i", body, 0)
            state.left, state.top = left, top
            width, height = right - left, bottom - top
            continue
        match record:
            case Record.EOF:
                ended = True
            case Record.SETMAPMODE:
                (state.map_mode,) = struct.unpack_from("<I", body)
                if state.map_mode != MM_ANISOTROPIC:
                    raise EmfError(f"record {record}: map mode {state.map_mode} not supported")
            case Record.SETBKMODE:  # only affects text and hatches, neither is used
                pass
            case Record.SETPOLYFILLMODE:
                (mode,) = struct.unpack_from("<I", body)
                if mode not in (ALTERNATE, WINDING):
                    raise EmfError(f"record {record}: fill mode {mode} not supported")
                state.even_odd = mode == ALTERNATE
            case Record.SETWINDOWEXTEX:
                state.window_extent = struct.unpack_from("<2i", body)
            case Record.SETWINDOWORGEX:
                state.window_origin = struct.unpack_from("<2i", body)
            case Record.SETVIEWPORTEXTEX:
                state.viewport_extent = struct.unpack_from("<2i", body)
            case Record.SETVIEWPORTORGEX:
                state.viewport_origin = struct.unpack_from("<2i", body)
            case Record.CREATEBRUSHINDIRECT:
                index, style, red, green, blue = struct.unpack_from("<II3B", body)
                if style != BS_SOLID:
                    raise EmfError(f"record {record}: brush style {style} not supported")
                state.objects[index] = ("brush", f"{red:02X}{green:02X}{blue:02X}")
            case Record.EXTCREATEPEN:
                index = struct.unpack_from("<I", body)[0]
                (pen_style,) = struct.unpack_from("<I", body, 20)
                if pen_style & 0xF != PS_NULL:
                    raise EmfError(f"record {record}: only null pens are supported")
                state.objects[index] = ("pen", None)
            case Record.SELECTOBJECT:
                (index,) = struct.unpack_from("<I", body)
                if index not in state.objects:
                    raise EmfError(f"record {record}: object {index:#x} not supported")
                kind, color = state.objects[index]
                if kind == "brush":
                    state.brush = color
            case Record.DELETEOBJECT:
                (index,) = struct.unpack_from("<I", body)
                state.objects.pop(index, None)
            case Record.BEGINPATH:
                state.in_path, state.path = True, []
            case Record.ENDPATH:
                state.in_path = False
            case Record.MOVETOEX:
                x, y = struct.unpack_from("<2i", body)
                if not state.in_path:
                    raise EmfError(f"record {record} outside a path is not supported")
                state.path.append("M" + state.point(x, y))
            case Record.POLYBEZIERTO16:
                if not state.in_path or not state.path:
                    raise EmfError(f"record {record} needs an open path with a start point")
                (count,) = struct.unpack_from("<I", body, 16)
                if count % 3:
                    raise EmfError(f"record {record}: {count} points are not Bézier triples")
                points = struct.unpack_from(f"<{2 * count}h", body, 20)
                for i in range(0, 2 * count, 6):
                    controls = [state.point(points[i + j], points[i + j + 1]) for j in (0, 2, 4)]
                    state.path.append("C" + " ".join(controls))
            case Record.CLOSEFIGURE:
                if not state.in_path:
                    raise EmfError(f"record {record} outside a path")
                state.path.append("Z")
            case Record.FILLPATH:
                if state.in_path or not state.path:
                    raise EmfError(f"record {record} without a closed path")
                state.fill("".join(state.path), record)
                state.path = []
            case Record.POLYPOLYGON16:
                if state.in_path:
                    raise EmfError(f"record {record} inside a path is not supported")
                polygons, total = struct.unpack_from("<II", body, 16)
                counts = struct.unpack_from(f"<{polygons}I", body, 24)
                points = struct.unpack_from(f"<{2 * total}h", body, 24 + 4 * polygons)
                parts: list[str] = []
                start = 0
                for count in counts:
                    corners = [
                        state.point(points[2 * k], points[2 * k + 1])
                        for k in range(start, start + count)
                    ]
                    parts.append("M" + corners[0] + "".join("L" + c for c in corners[1:]) + "Z")
                    start += count
                state.fill("".join(parts), record)
            case _:
                raise EmfError(f"record type {record} is not supported")
    if not ended:
        raise EmfError("the EMF has no EOF record")
    if state.in_path or state.path:
        raise EmfError("the EMF ends with an unfilled path")
    return Picture(width, height, tuple(state.shapes))
