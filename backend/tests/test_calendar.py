def test_create_calendar_event(client, auth_headers):
    # 1. Connect mock calendar
    client.post("/api/v1/calendar/connect-mock", headers=auth_headers)

    # 2. Create a new event: "Project Review Meeting" 17:00 – 18:00
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    create_res = client.post(
        "/api/v1/calendar/events",
        json={
            "summary": "Project Review Meeting",
            "description": "Sprint retrospective and demo review",
            "start": f"{today_str}T17:00:00",
            "end": f"{today_str}T18:00:00",
            "location": "Conference Room A"
        },
        headers=auth_headers
    )
    assert create_res.status_code == 200
    event_data = create_res.json()
    assert event_data["summary"] == "Project Review Meeting"
    assert "17:00" in event_data["start"]

    # 3. Retrieve events and verify Project Review Meeting is present
    events_res = client.get("/api/v1/calendar/events", headers=auth_headers)
    assert events_res.status_code == 200
    events = events_res.json()
    summaries = [e["summary"] for e in events]
    assert "Project Review Meeting" in summaries

    # 4. Verify AI Planner recognizes 17:00–18:00 as unavailable time
    plan_res = client.get("/api/v1/planner/today", headers=auth_headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()

    # Available focus hours: 09:00-18:00 window (9h) minus 17:00-18:00 (1h) = 8.0 hours
    assert plan["available_hours"] == 8.0

    # Ensure no task is scheduled in 17:00-18:00 window
    for slot in plan["schedule"]:
        if slot["item_type"] == "TASK":
            assert slot["time"] != "17:00–18:00"
            assert not slot["time"].startswith("17:")
