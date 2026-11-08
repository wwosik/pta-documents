"""E15-S02: the risk matrix as a ``Drawing`` — cells in signal colours, numbered circles."""

from __future__ import annotations

from pta_documents.design import colors
from pta_documents.design.colors import STATUS_COLORS, StatusCategory
from pta_documents.drawing import DrawingShape, DrawingText, ShapeKind
from pta_documents.drawing import riskmatrix as drawing
from pta_documents.drawing.harvey import DIAMETER, ball
from pta_documents.generation.common.risks import Risk, RiskMatrix, Thresholds

HEADINGS = ("Nr", "Risiko", "Wahrscheinlichkeit", "Auswirkung")


def matrix(*risks: Risk, thresholds: Thresholds | None = None) -> RiskMatrix:
    return RiskMatrix(risks, HEADINGS, thresholds or Thresholds())


def cells(picture: drawing.Drawing) -> list[DrawingShape]:
    return [
        i for i in picture.items if isinstance(i, DrawingShape) and i.kind is ShapeKind.RECTANGLE
    ]


def tinted(category: StatusCategory) -> str:
    return colors.tint(STATUS_COLORS[category], drawing.RISK_MATRIX.tint)


def test_five_by_five_cells_of_1_6_cm_coloured_by_the_product() -> None:
    picture = drawing.draw(matrix(Risk("1", "a", 1, 1)))
    found = cells(picture)
    assert len(found) == 25
    style = drawing.RISK_MATRIX
    assert abs(style.cell - 1.6 / 2.54 * 96) < 1e-6
    by_place = {
        (
            round((s.path.bounds.x - style.tick) // style.cell) + 1,
            5 - round((s.path.bounds.y - style.band) // style.cell),
        ): s.fill
        for s in found
    }
    assert by_place[(1, 1)] == tinted(StatusCategory.SUCCESS)
    assert by_place[(2, 2)] == tinted(StatusCategory.SUCCESS)
    assert by_place[(1, 5)] == tinted(StatusCategory.WARNING)
    assert by_place[(3, 4)] == tinted(StatusCategory.WARNING)
    assert by_place[(4, 4)] == tinted(StatusCategory.DANGER)
    strict = cells(drawing.draw(matrix(Risk("1", "a", 1, 1), thresholds=Thresholds(1, 2))))
    assert sum(s.fill == tinted(StatusCategory.SUCCESS) for s in strict) == 1


def test_a_risk_is_a_dark_blue_circle_with_its_number() -> None:
    picture = drawing.draw(matrix(Risk("7", "a", 5, 1)))
    (dot,) = [
        i for i in picture.items if isinstance(i, DrawingShape) and i.kind is ShapeKind.ELLIPSE
    ]
    assert dot.fill == colors.DARK_BLUE
    assert abs(dot.path.bounds.width - 0.6 / 2.54 * 96) < 1e-6
    number = next(t for t in picture.items if isinstance(t, DrawingText) and t.text == "7")
    assert number.color == colors.WHITE
    style = drawing.RISK_MATRIX
    # Probability 5 is the right column, impact 1 the bottom row.
    assert (
        abs(dot.path.bounds.x + dot.path.bounds.width / 2 - (style.tick + 4.5 * style.cell)) < 1e-6
    )
    assert (
        abs(dot.path.bounds.y + dot.path.bounds.height / 2 - (style.band + 4.5 * style.cell)) < 1e-6
    )


def test_several_risks_in_a_cell_sit_side_by_side() -> None:
    assert drawing.offsets(1) == [(0.0, 0.0)]
    two = drawing.offsets(2)
    assert two[0][1] == two[1][1] and two[0][0] == -two[1][0] and two[1][0] > 0
    distance = two[1][0] - two[0][0]
    assert distance >= drawing.RISK_MATRIX.dot
    nine = drawing.offsets(9)
    assert len(set(nine)) == 9
    half = (drawing.RISK_MATRIX.cell - drawing.RISK_MATRIX.dot) / 2
    assert all(abs(x) <= half and abs(y) <= half for x, y in nine)


def test_the_axes_carry_the_headings() -> None:
    picture = drawing.draw(matrix(Risk("1", "a", 1, 1)))
    texts = {t.text for t in picture.items if isinstance(t, DrawingText)}
    assert {"Wahrscheinlichkeit", "Auswirkung", "1", "5"} <= texts


def test_a_harvey_ball_is_filled_by_quarters() -> None:
    assert abs(DIAMETER - 0.45 / 2.54 * 96) < 1e-6
    kinds = [[s.kind for s in ball(n).items if isinstance(s, DrawingShape)] for n in range(5)]
    assert kinds[0] == [ShapeKind.ELLIPSE, ShapeKind.ELLIPSE]
    assert kinds[3] == [ShapeKind.ELLIPSE, ShapeKind.PIE, ShapeKind.ELLIPSE]
    assert kinds[4] == [ShapeKind.ELLIPSE, ShapeKind.ELLIPSE]
    full = [s for s in ball(4).items if isinstance(s, DrawingShape)]
    assert full[0].fill == colors.PTA_BLUE and full[-1].stroke == colors.DARK_BLUE
    three = next(
        s for s in ball(3).items if isinstance(s, DrawingShape) and s.kind is ShapeKind.PIE
    )
    assert three.angles == (270, 180)
