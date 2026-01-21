"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    # Reset participants for each activity
    for activity_name in activities:
        if activity_name == "Chess Club":
            activities[activity_name]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
        elif activity_name == "Programming Class":
            activities[activity_name]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
        elif activity_name == "Gym Class":
            activities[activity_name]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]
        else:
            activities[activity_name]["participants"] = []
    yield


class TestGetActivities:
    """Test cases for getting activities"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Soccer Club" in data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data


class TestSignupForActivity:
    """Test cases for signing up for activities"""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        response = client.post(
            "/activities/Soccer Club/signup",
            params={"email": "newtudent@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert "newtudent@mergington.edu" in data["Soccer Club"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_email(self, client):
        """Test that a student cannot signup twice for the same activity"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()
    
    def test_signup_already_registered_student(self, client):
        """Test signup for a student already in an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregisterFromActivity:
    """Test cases for unregistering from activities"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        response = client.post(
            "/activities/Programming Class/unregister",
            params={"email": "emma@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert "emma@mergington.edu" not in data["Programming Class"]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistration from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_not_registered_student(self, client):
        """Test unregister for a student not in the activity"""
        response = client.post(
            "/activities/Art Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()
    
    def test_unregister_already_unregistered_student(self, client):
        """Test that you can't unregister someone already unregistered"""
        email = "temp@mergington.edu"
        
        # First signup
        client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        
        # First unregister should work
        response1 = client.post(
            "/activities/Drama Club/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.post(
            "/activities/Drama Club/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400


class TestRootEndpoint:
    """Test cases for the root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 307, 308]
        assert "/static/index.html" in response.headers.get("location", "")
