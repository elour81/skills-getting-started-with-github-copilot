import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities database before each test"""
    # Store original activities
    original_activities = activities.copy()
    yield
    # Reset to original after test
    activities.clear()
    activities.update(original_activities)


def test_root_redirect(client):
    """Test that root endpoint redirects to static index"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Check structure
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)


def test_signup_successful(client):
    """Test successful signup for an activity"""
    response = client.post("/activities/Chess Club/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Signed up test@mergington.edu for Chess Club" in data["message"]
    # Check that participant was added
    get_response = client.get("/activities")
    activities_data = get_response.json()
    assert "test@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    response = client.post("/activities/NonExistent/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_signup_already_signed_up(client):
    """Test signup when already signed up"""
    # First signup
    client.post("/activities/Chess Club/signup", params={"email": "test@mergington.edu"})
    # Try again
    response = client.post("/activities/Chess Club/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Student already signed up" in data["detail"]


def test_unregister_successful(client):
    """Test successful unregister from an activity"""
    # First signup
    client.post("/activities/Chess Club/signup", json={"email": "test@mergington.edu"})
    # Then unregister
    response = client.delete("/activities/Chess Club/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Unregistered test@mergington.edu from Chess Club" in data["message"]
    # Check removed
    get_response = client.get("/activities")
    activities_data = get_response.json()
    assert "test@mergington.edu" not in activities_data["Chess Club"]["participants"]


def test_unregister_activity_not_found(client):
    """Test unregister from non-existent activity"""
    response = client.delete("/activities/NonExistent/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_unregister_not_signed_up(client):
    """Test unregister when not signed up"""
    response = client.delete("/activities/Chess Club/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Student not signed up for this activity" in data["detail"]