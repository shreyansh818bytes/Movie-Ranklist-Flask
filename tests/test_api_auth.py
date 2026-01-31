"""Tests for authentication API endpoints."""

import json


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register."""

    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post(
            "/api/auth/register",
            data=json.dumps({"email": "new@example.com", "password": "password123"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["user"]["email"] == "new@example.com"
        assert "id" in data["user"]

    def test_register_invalid_json(self, client):
        """Test registration with invalid JSON returns 400."""
        response = client.post(
            "/api/auth/register",
            data="not json",
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_register_missing_email(self, client):
        """Test registration with missing email."""
        response = client.post(
            "/api/auth/register",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data

    def test_register_missing_password(self, client):
        """Test registration with missing password."""
        response = client.post(
            "/api/auth/register",
            data=json.dumps({"email": "user@example.com"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            data=json.dumps({"email": "invalid", "password": "password123"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Invalid email" in data["error"]

    def test_register_short_password(self, client):
        """Test registration with password too short."""
        response = client.post(
            "/api/auth/register",
            data=json.dumps({"email": "user@example.com", "password": "short"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "8 characters" in data["error"]

    def test_register_duplicate_email(self, client):
        """Test registration with already registered email."""
        client.post(
            "/api/auth/register",
            data=json.dumps({"email": "dupe@example.com", "password": "password123"}),
            content_type="application/json",
        )

        response = client.post(
            "/api/auth/register",
            data=json.dumps({"email": "dupe@example.com", "password": "different123"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "already registered" in data["error"]


class TestLoginEndpoint:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, client, sample_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": sample_user["email"], "password": sample_user["password"]}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["user"]["email"] == sample_user["email"]

    def test_login_invalid_json(self, client):
        """Test login with invalid JSON returns 400."""
        response = client.post(
            "/api/auth/login",
            data="not json",
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_login_wrong_password(self, client, sample_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_user["email"], "password": "wrongpass"}),
            content_type="application/json",
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Invalid email or password" in data["error"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": "nonexistent@example.com", "password": "password123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["success"] is False

    def test_login_missing_credentials(self, client):
        """Test login with empty JSON body returns 400."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps({}),
            content_type="application/json",
        )

        # Empty dict is falsy in Python, so returns 400 "Invalid request"
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout."""

    def test_logout_success(self, client, sample_user):
        """Test successful logout after login."""
        client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": sample_user["email"], "password": sample_user["password"]}
            ),
            content_type="application/json",
        )

        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_logout_without_login(self, client):
        """Test logout when not logged in."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True


class TestAuthStatusEndpoint:
    """Tests for GET /api/auth/status."""

    def test_status_not_authenticated(self, client):
        """Test status when not logged in."""
        response = client.get("/api/auth/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is False
        assert "user" not in data

    def test_status_authenticated(self, client, sample_user):
        """Test status when logged in."""
        client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": sample_user["email"], "password": sample_user["password"]}
            ),
            content_type="application/json",
        )

        response = client.get("/api/auth/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is True
        assert data["user"]["email"] == sample_user["email"]

    def test_status_after_logout(self, client, sample_user):
        """Test status after logging out."""
        client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": sample_user["email"], "password": sample_user["password"]}
            ),
            content_type="application/json",
        )
        client.post("/api/auth/logout")

        response = client.get("/api/auth/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["authenticated"] is False


class TestAuthPageRoutes:
    """Tests for authentication page routes."""

    def test_login_page(self, client):
        """Test login page renders."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_register_page(self, client):
        """Test register page renders."""
        response = client.get("/register")
        assert response.status_code == 200
        assert b"Create Account" in response.data

    def test_login_page_redirects_when_authenticated(self, client, sample_user):
        """Test login page redirects to index when already logged in."""
        client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": sample_user["email"], "password": sample_user["password"]}
            ),
            content_type="application/json",
        )

        response = client.get("/login")
        assert response.status_code == 302
        assert "/" in response.headers["Location"]

    def test_register_page_redirects_when_authenticated(self, client, sample_user):
        """Test register page redirects to index when already logged in."""
        client.post(
            "/api/auth/login",
            data=json.dumps(
                {"email": sample_user["email"], "password": sample_user["password"]}
            ),
            content_type="application/json",
        )

        response = client.get("/register")
        assert response.status_code == 302
        assert "/" in response.headers["Location"]
