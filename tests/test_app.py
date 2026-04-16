"""
Tests for the Mergington High School Activities API
Using AAA (Arrange-Act-Assert) pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 2,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Verify root path redirects to /static/index.html"""
        # Arrange
        # (No arrangement needed for redirect test)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_dict(self, client):
        """Verify GET /activities returns all activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 3
        for activity_name in expected_activities:
            assert activity_name in data

    def test_get_activities_includes_activity_details(self, client):
        """Verify each activity includes required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_details in data.items():
            for field in required_fields:
                assert field in activity_details

    def test_get_activities_shows_current_participants(self, client):
        """Verify activities show correct participant list"""
        # Arrange
        # (Activities fixture sets Chess Club with one participant)

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 1


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client):
        """Verify student can sign up for an activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "alice@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
        data = response.json()
        assert "Signed up" in data["message"]

    def test_signup_invalid_activity(self, client):
        """Verify signup fails for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "alice@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self, client):
        """Verify student cannot sign up twice for same activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        # michael@mergington.edu is already in Chess Club (from fixture)

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_adds_participant_to_list(self, client):
        """Verify participant is added to the activity's participant list"""
        # Arrange
        activity_name = "Gym Class"
        email = "new_student@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert email in activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_successful_unregister(self, client):
        """Verify student can unregister from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_invalid_activity(self, client):
        """Verify unregister fails for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "alice@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_signed_up_student(self, client):
        """Verify unregister fails for student not in activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "not_signed_up@mergington.edu"
        # Programming Class has no participants (from fixture)

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_removes_participant_from_list(self, client):
        """Verify participant is removed from the activity's participant list"""
        # Arrange
        activity_name = "Gym Class"
        email = "john@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert email not in activities[activity_name]["participants"]


class TestIntegrationScenarios:
    """Integration tests for multi-step workflows"""

    def test_signup_then_unregister_workflow(self, client):
        """Verify complete signup and unregister workflow"""
        # Arrange
        activity_name = "Programming Class"
        email = "bob@mergington.edu"

        # Act - Sign up
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert signup
        assert response1.status_code == 200
        assert email in activities[activity_name]["participants"]

        # Act - Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert unregister
        assert response2.status_code == 200
        assert email not in activities[activity_name]["participants"]

    def test_multiple_students_signup_same_activity(self, client):
        """Verify multiple different students can sign up for same activity"""
        # Arrange
        activity_name = "Programming Class"
        students = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]

        # Act
        for student in students:
            response = client.post(
                f"/activities/{activity_name}/signup?email={student}"
            )
            assert response.status_code == 200

        # Assert
        assert len(activities[activity_name]["participants"]) == len(students)
        for student in students:
            assert student in activities[activity_name]["participants"]
