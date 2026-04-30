"""
Comprehensive tests for the Mergington High School Activities API.
Tests follow the AAA (Arrange-Act-Assert) pattern.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities."""
        # Arrange - no setup needed, activities are pre-populated
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 3
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
    
    def test_get_activities_has_correct_structure(self, client, reset_activities):
        """Test that each activity has all required fields."""
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict)
            assert set(activity_data.keys()) == expected_keys
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestPostSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful registration for an activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert email in chess_club["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup fails when activity doesn't exist."""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test signup fails when email is already registered."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test student can register for multiple different activities."""
        # Arrange
        email = "multistudent@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class"]
        
        # Act & Assert for each activity
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify both registrations
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for activity_name in activities_to_join:
            assert email in activities_data[activity_name]["participants"]


class TestDeleteParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""
    
    def test_delete_participant_successful(self, client, reset_activities):
        """Test successful unregistration of a participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert email not in chess_club["participants"]
    
    def test_delete_participant_not_found(self, client, reset_activities):
        """Test delete fails when participant not registered."""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_delete_activity_not_found(self, client, reset_activities):
        """Test delete fails when activity doesn't exist."""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_full_signup_and_unregister_flow(self, client, reset_activities):
        """Test complete workflow: signup → verify → unregister → verify."""
        # Arrange
        activity_name = "Programming Class"
        email = "flowtest@mergington.edu"
        
        # Act 1: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert 1: Signup successful
        assert signup_response.status_code == 200
        
        # Act 2: Verify participant in list
        activities_response = client.get("/activities")
        programming = activities_response.json()["Programming Class"]
        
        # Assert 2: Participant added
        assert email in programming["participants"]
        original_count = len(programming["participants"])
        
        # Act 3: Unregister
        delete_response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert 3: Unregister successful
        assert delete_response.status_code == 200
        
        # Act 4: Verify participant removed
        activities_response = client.get("/activities")
        programming = activities_response.json()["Programming Class"]
        
        # Assert 4: Participant removed
        assert email not in programming["participants"]
        assert len(programming["participants"]) == original_count - 1
    
    def test_signup_verify_delete_multiple_activities(self, client, reset_activities):
        """Test participant registration across multiple activities."""
        # Arrange
        email = "multitest@mergington.edu"
        activities_list = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act 1: Sign up for all activities
        for activity_name in activities_list:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Assert 1: Verify in all
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for activity_name in activities_list:
            assert email in activities_data[activity_name]["participants"]
        
        # Act 2: Unregister from one activity
        unregister_activity = "Chess Club"
        delete_response = client.delete(
            f"/activities/{unregister_activity}/participants/{email}"
        )
        
        # Assert 2: Still in other activities
        assert delete_response.status_code == 200
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[unregister_activity]["participants"]
        assert email in activities_data["Programming Class"]["participants"]
        assert email in activities_data["Gym Class"]["participants"]
