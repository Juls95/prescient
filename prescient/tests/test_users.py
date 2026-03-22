"""Tests for user database and auth."""

import os
import tempfile

from agent.users.database import UserDB
from agent.users.auth import create_token, verify_token


class TestUserDB:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = UserDB(self.tmp.name)
        self.db.connect()

    def teardown_method(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_create_user(self):
        user = self.db.create_user("alice", "alice@test.com", "password123")
        assert user["username"] == "alice"
        assert user["email"] == "alice@test.com"
        assert "password_hash" not in user

    def test_duplicate_user_raises(self):
        self.db.create_user("bob", "bob@test.com", "pass")
        try:
            self.db.create_user("bob", "bob2@test.com", "pass")
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_authenticate_valid(self):
        self.db.create_user("carol", "carol@test.com", "secret")
        user = self.db.authenticate("carol", "secret")
        assert user is not None
        assert user["username"] == "carol"

    def test_authenticate_invalid(self):
        self.db.create_user("dave", "dave@test.com", "correct")
        user = self.db.authenticate("dave", "wrong")
        assert user is None

    def test_preferences_default(self):
        self.db.create_user("eve", "eve@test.com", "pass")
        user = self.db.get_user_by_username("eve")
        prefs = self.db.get_preferences(user["id"])
        assert prefs["risk_tolerance"] == "medium"
        assert prefs["theme"] == "light"

    def test_update_preferences(self):
        self.db.create_user("frank", "frank@test.com", "pass")
        user = self.db.get_user_by_username("frank")
        prefs = self.db.update_preferences(user["id"], theme="dark", risk_tolerance="high")
        assert prefs["theme"] == "dark"
        assert prefs["risk_tolerance"] == "high"

    def test_cast_vote(self):
        self.db.create_user("grace", "grace@test.com", "pass")
        user = self.db.get_user_by_username("grace")
        result = self.db.cast_vote(user["id"], "mkt001", "YES", 0.8)
        assert result["YES"] == 1
        assert result["total_votes"] == 1

    def test_change_vote(self):
        self.db.create_user("heidi", "heidi@test.com", "pass")
        user = self.db.get_user_by_username("heidi")
        self.db.cast_vote(user["id"], "mkt001", "YES")
        result = self.db.cast_vote(user["id"], "mkt001", "NO")
        assert result["NO"] == 1
        assert result["YES"] == 0

    def test_join_market(self):
        self.db.create_user("ivan", "ivan@test.com", "pass")
        user = self.db.get_user_by_username("ivan")
        result = self.db.join_market(user["id"], "mkt001", "YES", 100.0)
        assert result["count"] == 1

    def test_activity_log(self):
        self.db.create_user("judy", "judy@test.com", "pass")
        user = self.db.get_user_by_username("judy")
        self.db.cast_vote(user["id"], "mkt001", "YES")
        activity = self.db.get_activity(user["id"])
        assert len(activity) >= 1
        assert activity[0]["action"] == "vote"


class TestAuth:
    def test_create_and_verify_token(self):
        os.environ["JWT_SECRET"] = "test-secret-key"
        token = create_token(1, "testuser")
        payload = verify_token(token)
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"

    def test_invalid_token_returns_none(self):
        os.environ["JWT_SECRET"] = "test-secret-key"
        result = verify_token("invalid.token.here")
        assert result is None
