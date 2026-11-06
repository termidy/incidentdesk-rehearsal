import pytest

from incidentdesk.models import AlertSubscription, Service

pytestmark = pytest.mark.db


@pytest.fixture
def login(db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer")
    db.add(service)
    db.commit()
    return service


def test_create_subscription_returns_stored_fields_and_id(client, login):
    response = client.post(
        "/mobile/v1/subscriptions",
        json={"engineer": "a.reyes", "services": ["login-service"], "min_priority": "P2"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "engineer": "a.reyes",
        "services": ["login-service"],
        "min_priority": "P2",
    }


def test_list_subscriptions_is_scoped_to_engineer(client, login):
    for engineer in ("a.reyes", "b.chen"):
        response = client.post(
            "/mobile/v1/subscriptions",
            json={"engineer": engineer, "services": ["login-service"], "min_priority": "P2"},
        )
        assert response.status_code == 201

    response = client.get("/mobile/v1/subscriptions", params={"engineer": "a.reyes"})

    assert response.status_code == 200
    assert [item["engineer"] for item in response.json()] == ["a.reyes"]


def test_unknown_service_is_rejected_without_saving_subscription(client, db):
    response = client.post(
        "/mobile/v1/subscriptions",
        json={"engineer": "a.reyes", "services": ["missing-service"], "min_priority": "P2"},
    )

    assert response.status_code == 422
    assert db.query(AlertSubscription).count() == 0
