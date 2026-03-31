from app.llm import build_prompt


def test_build_prompt_includes_context_and_question():
    prompt = build_prompt(question="Как взять отпуск?", context="Отпуск оформляется через Zoho.")
    assert "Как взять отпуск?" in prompt
    assert "Отпуск оформляется через Zoho." in prompt
    assert "<context>" in prompt
    assert "<user_question>" in prompt


def test_build_prompt_handles_empty_context():
    prompt = build_prompt(question="Вопрос?", context="")
    assert "Вопрос?" in prompt
    assert "нет релевантных данных" in prompt


def test_build_prompt_uses_xml_fencing():
    prompt = build_prompt(question="test", context="data")
    assert prompt.startswith("<context>")
    assert "</context>" in prompt
    assert "<user_question>" in prompt
    assert "</user_question>" in prompt
