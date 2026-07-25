from fastapi import status

def test_list_planning_goals(client):
    response = client.get("/planning/goals")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
