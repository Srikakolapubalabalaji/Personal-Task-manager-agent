def test_agent_queries(client, auth_headers):
    # 1. "What should I work on today?"
    res1 = client.post("/api/v1/agent/chat", json={"message": "What should I work on today?"}, headers=auth_headers)
    assert res1.status_code == 200
    assert "Daily Plan" in res1.json()["response"]
    assert len(res1.json()["tool_calls"]) >= 1

    # 2. "Create a high-priority task to prepare for my AI interview by Friday."
    res2 = client.post(
        "/api/v1/agent/chat",
        json={"message": "Create a high-priority task to prepare for my AI interview by Friday."},
        headers=auth_headers
    )
    assert res2.status_code == 200
    assert "Task Created Successfully" in res2.json()["response"]

    # 3. "Do I have enough time to finish my tasks today?"
    res3 = client.post(
        "/api/v1/agent/chat",
        json={"message": "Do I have enough time to finish my tasks today?"},
        headers=auth_headers
    )
    assert res3.status_code == 200
    assert "Focus Time" in res3.json()["response"]

    # 4. "Move my task to tomorrow."
    res4 = client.post("/api/v1/agent/chat", json={"message": "Move my task to tomorrow."}, headers=auth_headers)
    assert res4.status_code == 200
    assert "Rescheduled" in res4.json()["response"]

    # 5. "What tasks are overdue?"
    res5 = client.post("/api/v1/agent/chat", json={"message": "What tasks are overdue?"}, headers=auth_headers)
    assert res5.status_code == 200
    assert "overdue" in res5.json()["response"].lower()
