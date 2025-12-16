import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

from types import SimpleNamespace

def test_get_questions_no_llm_call(authed_client, monkeypatch):
    # fake LLM result shaped like your real code expects
    fake = {
        "__interrupt__": [SimpleNamespace(value="mock interrupt")],
        "thread_id": "11111111-1111-1111-1111-111111111111"
    }

    def fake_invoke_researcher(*, thread_id, name, one_liner, resume_val):
        return fake

    # IMPORTANT: patch where it's USED (your routes module)
    monkeypatch.setattr("main.invoke_researcher", fake_invoke_researcher)

    resp = authed_client.post("/api/get-questions", json={"name": "X", "desc": "Y"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["interrupt"] == "mock interrupt"
    assert "thread_id" in body


def test_validate_no_llm_call(authed_client, monkeypatch):
    fake = {"question_generator": "mock questions"}

    def fake_invoke_researcher(*, thread_id, resume_val):
        return fake

    monkeypatch.setattr("main.invoke_researcher", fake_invoke_researcher)

    resp = authed_client.post("/api/validate", json={
        "is_valid": True,
        "additional_info": "",
        "thread_id": "11111111-1111-1111-1111-111111111111"
    })
    assert resp.status_code == 200
    assert resp.json()["response"] == "mock questions"


def test_conversation_no_llm_call(authed_client, monkeypatch):
    class Msg:
        def __init__(self, content): self.content = content

    fake = {"messages": [Msg("earlier"), Msg("final mock reply")]}

    def fake_invoke_conversation(*, thread_id, message):
        return fake

    monkeypatch.setattr("main.invoke_conversation", fake_invoke_conversation)

    resp = authed_client.post("/api/conversation", json={
        "thread_id": "11111111-1111-1111-1111-111111111111",
        "message": "hello"
    })
    assert resp.status_code == 200
    assert resp.json()["response"] == "final mock reply"
