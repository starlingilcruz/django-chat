"""
Tests for authentication
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAuthentication:
    """Test user authentication endpoints"""

    def setup_method(self):
        self.client = APIClient()

    def test_signup_success(self):
        """Test successful user registration"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

        response = self.client.post("/api/v1/auth/signup", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert "tokens" in response.data
        assert response.data["user"]["email"] == "test@example.com"

    def test_signup_password_mismatch(self):
        """Test signup with mismatched passwords"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass123!",
        }

        response = self.client.post("/api/v1/auth/signup", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self):
        """Test successful login"""
        # Create user
        User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="SecurePass123!",
        )

        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
        }

        response = self.client.post("/api/v1/auth/login", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data
        assert "tokens" in response.data

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            "email": "test@example.com",
            "password": "WrongPassword",
        }

        response = self.client.post("/api/v1/auth/login", data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
