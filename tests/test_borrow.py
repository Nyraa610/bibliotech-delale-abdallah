import pytest


def test_inactive_member_is_refused(library, capsys):
    accepted = library.do_stuff("M004", "B002")
    assert accepted is False
    assert "membre inactif" in capsys.readouterr().out


@pytest.mark.parametrize(
    "member_id, book_id, expected_msg",
    [
        ("M001", "B002", "emprunts en retard"),
        ("M005", "B001", "deja emprunte par ce membre"),
        ("M005", "B003", "plus d'exemplaire disponible"),
    ],
)
def test_borrow_refusals(library, capsys, member_id, book_id, expected_msg):
    accepted = library.do_stuff(member_id, book_id)
    assert accepted is False
    assert expected_msg in capsys.readouterr().out


def test_borrow_limit_reached(library, capsys):
    # M005 a droit a 3 emprunts max (standard) et en a deja 1
    assert library.do_stuff("M005", "B005") is True
    assert library.do_stuff("M005", "B002") is True
    # 3e demande -> refus limite
    accepted = library.do_stuff("M005", "B007")
    assert accepted is False
    assert "limite d'emprunts atteinte (3)" in capsys.readouterr().out


def test_borrow_success(library, capsys):
    accepted = library.do_stuff("M005", "B005")
    assert accepted is True
    out = capsys.readouterr().out
    assert "Emprunt L013 enregistre" in out
    assert "2026-10-28" in out
