"""
Backend tests for Mergington High School Activities API

Tests use the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the API call
- Assert: Verify response status, data, and side effects
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_success(self, client):
        """
        Arrange: Client is ready
        Act: Fetch all activities
        Assert: Status 200 and all activities returned
        """
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
    
    def test_activity_data_structure(self, client):
        """
        Arrange: Client is ready
        Act: Fetch all activities
        Assert: Each activity has required fields
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_details in data.items():
            assert isinstance(activity_details, dict)
            assert required_fields == set(activity_details.keys())
            assert isinstance(activity_details["participants"], list)
            assert isinstance(activity_details["max_participants"], int)


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """
        Arrange: Client is ready
        Act: Request root endpoint
        Assert: Redirects to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """
        Arrange: Valid activity and new email
        Act: Sign up for activity
        Assert: Status 200 and participant added
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants
    
    def test_signup_activity_not_found(self, client):
        """
        Arrange: Non-existent activity name
        Act: Try to sign up
        Assert: Status 404 with appropriate error
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email(self, client):
        """
        Arrange: Already registered participant
        Act: Try to sign up again
        Assert: Status 400 (duplicate signup prevented)
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_multiple_students(self, client):
        """
        Arrange: Two different students
        Act: Sign both up for same activity
        Assert: Both are added successfully
        """
        # Arrange
        activity_name = "Gym Class"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants
        assert len(participants) == 4  # 2 original + 2 new


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """
        Arrange: Existing participant
        Act: Unregister from activity
        Assert: Status 200 and participant removed
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email not in participants
    
    def test_unregister_activity_not_found(self, client):
        """
        Arrange: Non-existent activity
        Act: Try to unregister
        Assert: Status 404
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_participant_not_registered(self, client):
        """
        Arrange: Participant not signed up for activity
        Act: Try to unregister
        Assert: Status 404 with appropriate error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"].lower()
    
    def test_unregister_multiple_participants(self, client):
        """
        Arrange: Activity with multiple participants
        Act: Unregister one participant
        Assert: Only that participant removed
        """
        # Arrange
        activity_name = "Programming Class"
        email_to_remove = "emma@mergington.edu"
        email_to_keep = "sophia@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email_to_remove not in participants
        assert email_to_keep in participants
    
    def test_signup_and_unregister_flow(self, client):
        """
        Arrange: Sign up a new student, then unregister
        Act: Signup then unregister
        Assert: Participant added, then removed
        """
        # Arrange
        activity_name = "Gym Class"
        email = "flowtest@mergington.edu"
        
        # Act: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup worked
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants
        original_count = len(participants)
        
        # Act: Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert: Unregister succeeded
        assert unregister_response.status_code == 200
        
        # Verify unregister worked
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email not in participants
        assert len(participants) == original_count - 1
