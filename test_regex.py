from graps import not_one_off


def test_regex():
    assert not_one_off("El Motho", "El Motho (Martina) & Martin Steers") is False, "Should not match"
    assert not_one_off("El Motho", "El Motho (c) defeats Gabriel Kidd") is True, "Should match"
    assert not_one_off("El Motho", "El Motho (Charlie Carter, Oisin Delaney & The OJMO)") is False, "Should not match"
    assert not_one_off("El Motho", "El Motho (w/Jinny)") is True, "Should match"
    assert not_one_off("El Motho", "El Motho defeats Gabriel Kidd") is True, "Should match"
    assert not_one_off("El Motho", "Gabriel Kidd defeats El Motho") is True, "Should match"


if __name__ == "__main__":
    test_regex()
    print("Everything passed")