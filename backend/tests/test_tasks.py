def test_create_and_get_tasks(client, auth_headers):
    # Create task
    create_res = client.post(
        "/api/v1/tasks",
        json={
            "title": "Prepare PostgreSQL Interview Questions",
            "priority": "HIGH",
            "estimated_minutes": 120,
            "category": "Technical"
        },
        headers=auth_headers
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    # Get task list
    list_res = client.get("/api/v1/tasks", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert list_res.json()[0]["title"] == "Prepare PostgreSQL Interview Questions"

    # Complete task
    comp_res = client.post(f"/api/v1/tasks/{task_id}/complete", headers=auth_headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"


def test_task_breakdown(client, auth_headers):
    create_res = client.post(
        "/api/v1/tasks",
        json={"title": "Prepare for AI Interview", "priority": "HIGH"},
        headers=auth_headers
    )
    task_id = create_res.json()["id"]

    breakdown_res = client.post(f"/api/v1/tasks/{task_id}/breakdown", headers=auth_headers)
    assert breakdown_res.status_code == 200
    data = breakdown_res.json()
    assert len(data["subtasks"]) >= 4
