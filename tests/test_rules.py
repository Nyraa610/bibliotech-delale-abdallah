import pytest
from bibliotech import late_fee


@pytest.mark.parametrize(
    "days_late, kind, member_type, price, expected",
    [
        (0, "book", "standard", 10.0, 0.0),       # Rendu à temps
        (-2, "book", "standard", 10.0, 0.0),      # Rendu en avance
        (4, "book", "standard", 10.0, 2.0),       # Livre standard (4 * 0.50)
        (2, "dvd", "standard", 10.0, 2.0),        # DVD standard (2 * 1.00)
        (5, "magazine", "standard", 10.0, 1.0),   # Magazine standard (5 * 0.20)
        (10, "dvd", "student", 20.0, 5.0),        # Étudiant 50% (10 * 1.0 * 0.5)
        (10, "dvd", "premium", 20.0, 0.0),        # Premium 100% gratuit
        (50, "book", "standard", 15.0, 15.0),     # Plafond au prix du document
        (4, "unknown", "standard", 10.0, 2.0),    # Type inconnu traité comme livre (0.50)
    ],
)
def test_late_fee(days_late, kind, member_type, price, expected):
    assert late_fee(days_late, kind, member_type, price) == pytest.approx(expected)
