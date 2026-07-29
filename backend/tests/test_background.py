from fastapi import status


def test_list_background_jobs(client):
    response = client.get("/background/jobs")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_list_notifications(client):
    response = client.get("/background/notifications")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
