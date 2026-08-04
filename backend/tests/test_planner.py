def test_daily_planner(client, auth_headers):
    # Connect calendar integration
    client.post("/api/v1/calendar/connect-mock", headers=auth_headers)

    # Add high priority task
    client.post(
        "/api/v1/tasks",
        json={"title": "Finish Project Documentation", "priority": "HIGH", "estimated_minutes": 180},
        headers=auth_headers
    )

    plan_res = client.get("/api/v1/planner/today", headers=auth_headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert "schedule" in plan
    assert "available_hours" in plan
    assert plan["available_hours"] == 7.0
    assert "recommendation" in plan

    # Verify calendar events 10:00-11:00 and 16:00-17:00 exist without overlap
    events = [s for s in plan["schedule"] if s["item_type"] == "EVENT"]
    event_times = [s["time"] for s in events]
    assert "10:00–11:00" in event_times
    assert "16:00–17:00" in event_times

    # Verify no task overlaps with 10:00-11:00 or 16:00-17:00
    for s in plan["schedule"]:
        if s["item_type"] == "TASK":
            assert not (s["time"].startswith("10:") and not s["time"].startswith("10:00"))
            assert not (s["time"].startswith("16:"))


def test_task_deduplication(client, auth_headers):
    # Add near-duplicate tasks
    t1 = client.post(
        "/api/v1/tasks",
        json={"title": "prepare for my AI interview - It will take 2 hours", "priority": "HIGH", "estimated_minutes": 120},
        headers=auth_headers
    )
    t2 = client.post(
        "/api/v1/tasks",
        json={"title": "Create a task to prepare for my AI interview - It will take 2 hours", "priority": "HIGH", "estimated_minutes": 120},
        headers=auth_headers
    )

    plan_res = client.get("/api/v1/planner/today", headers=auth_headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()

    # Filter task slots from daily plan schedule
    task_slots = [s for s in plan["schedule"] if s["item_type"] == "TASK"]
    ai_prep_slots = [s for s in task_slots if "ai interview" in s["title"].lower()]

    # Verify that the near-duplicate task appears ONLY ONCE in the daily plan schedule
    assert len(ai_prep_slots) == 1


def test_ai_response_and_daily_plan_consistency(client, auth_headers):
    client.post("/api/v1/calendar/connect-mock", headers=auth_headers)
    # Ask agent "What should I work on today?"
    agent_res = client.post(
        "/api/v1/agent/chat",
        json={"message": "What should I work on today?"},
        headers=auth_headers
    )
    assert agent_res.status_code == 200
    chat_text = agent_res.json()["response"]

    # Get daily plan from endpoint
    plan_res = client.get("/api/v1/planner/today", headers=auth_headers)
    assert plan_res.status_code == 200
    schedule = plan_res.json()["schedule"]

    # Verify every schedule slot's time string appears identically in chat_text
    for slot in schedule:
        assert slot["time"] in chat_text, f"Time string {slot['time']} missing from AI response"

