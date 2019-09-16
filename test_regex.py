from graps import not_one_off, apply_translations


def test_one_off_regex():
    assert not_one_off("El Motho", "El Motho (Martina) & Martin Steers") is False, "Should not match"
    assert not_one_off("El Motho", "El Motho (c) defeats Gabriel Kidd") is True, "Should match"
    assert not_one_off("El Motho", "El Motho (Charlie Carter, Oisin Delaney & The OJMO)") is False, "Should not match"
    assert not_one_off("El Motho", "El Motho (w/Jinny)") is True, "Should match"
    assert not_one_off("El Motho", "El Motho defeats Gabriel Kidd") is True, "Should match"
    assert not_one_off("El Motho", "Gabriel Kidd defeats El Motho") is True, "Should match"
    assert not_one_off("El Motho", "The Knucklelockers (Darrell Allen & El Motho) defeat The NIC (Charlie Carter & Oisin Delaney)") is True, "Should match"
    assert not_one_off("El Motho", "The Knucklelockers (Darrell Allen & Jordon Breaks) defeat The NIC (Charlie Carter & El Motho)") is True, "Should match"


def test_translation():
    assert apply_translations("NJPW G1 Climax 2019 - Tag 12") == "NJPW G1 Climax 2019 - Day 12"
    assert apply_translations("ZERO1 Genki Soul Niigata Cheerful & Bullying Eradication Movement ZERO1 x Panchinko Tamasaburo Charity Pro-Wrestling 2017 Spring Camp - Tag 1") == "ZERO1 Genki Soul Niigata Cheerful & Bullying Eradication Movement ZERO1 x Panchinko Tamasaburo Charity Pro-Wrestling 2017 Spring Camp - Day 1"
    assert apply_translations("RCW @ Japan Weekend Madrid 2019 - Tag 2 - Morning Show") == "RCW @ Japan Weekend Madrid 2019 - Day 2 - Morning Show"
    assert apply_translations("BJW Ueno Wrestling Festival 2017 - Tag 4 Teil 2") == "BJW Ueno Wrestling Festival 2017 - Day 4 Teil 2"
    assert apply_translations("BJW Ueno Wrestling Festival 2017 - Tag 4: Show #3") == "BJW Ueno Wrestling Festival 2017 - Day 4: Show #3"
    assert apply_translations("FCP Dream Tag Team Invitational 2019 - Tag 1") == "FCP Dream Tag Team Invitational 2019 - Day 1"
    assert apply_translations("BJW Dai Nippon Pro-Wrestling Ueno Convention - Day 3 Part 1 BJW Shuffle Tag Tournament") == "BJW Dai Nippon Pro-Wrestling Ueno Convention - Day 3 Part 1 BJW Shuffle Tag Tournament"


if __name__ == "__main__":
    test_one_off_regex()
    test_translation()
    print("Everything passed")
