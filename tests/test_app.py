import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Store initial state for resetting
initial_activities = copy.deepcopy(activities)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    global activities
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))

# Create test client
client = TestClient(app)

def test_get_activities():
    """Test GET /activities returns all activities with correct structure"""
    # Arrange
    expected_activities = [
        "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
        "Tennis Club", "Art Club", "Music Ensemble", "Debate Team", "Science Club"
    ]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9
    for activity in expected_activities:
        assert activity in data
        assert "description" in data[activity]
        assert "schedule" in data[activity]
        assert "max_participants" in data[activity]
        assert "participants" in data[activity]
        assert isinstance(data[activity]["participants"], list)

def test_signup_success():
    """Test successful signup for an activity"""
    # Arrange
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    initial_participants = len(activities[activity]["participants"])

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities[activity]["participants"]
    assert len(activities[activity]["participants"]) == initial_participants + 1

def test_signup_duplicate():
    """Test signup fails when student is already signed up"""
    # Arrange
    email = "existing@mergington.edu"
    activity = "Programming Class"
    # First signup
    client.post(f"/activities/{activity}/signup", params={"email": email})

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}

def test_signup_nonexistent_activity():
    """Test signup fails for non-existent activity"""
    # Arrange
    email = "student@mergington.edu"
    activity = "Nonexistent Activity"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}

def test_signup_over_capacity_allowed():
    """Test that signup succeeds even when exceeding max_participants (current behavior)"""
    # Arrange
    email = "newstudent@mergington.edu"
    activity = "Basketball Team"  # max_participants: 15, currently 1 participant
    # Fill to capacity
    for i in range(14):  # Add 14 more to reach 15
        client.post(f"/activities/{activity}/signup", params={"email": f"student{i}@mergington.edu"})

    # Act - Try to add one more
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert - Currently allows over capacity
    assert response.status_code == 200
    assert len(activities[activity]["participants"]) == 16  # Over max of 15