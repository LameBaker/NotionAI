from app.query_rewriter import expand_abbreviations


def test_expand_known_abbreviation():
    abbrs = {"ДМС": "добровольное медицинское страхование", "HR": "Human Resources"}
    result = expand_abbreviations("Как оформить ДМС?", abbrs)
    assert "добровольное медицинское страхование" in result
    assert "ДМС" in result  # original preserved


def test_expand_case_insensitive():
    abbrs = {"hr": "Human Resources"}
    result = expand_abbreviations("Вопрос про HR отдел", abbrs)
    assert "Human Resources" in result


def test_no_expansion_for_unknown():
    abbrs = {"ДМС": "добровольное медицинское страхование"}
    result = expand_abbreviations("Как взять отпуск?", abbrs)
    assert result == "Как взять отпуск?"


def test_empty_abbreviations():
    result = expand_abbreviations("test query", {})
    assert result == "test query"
