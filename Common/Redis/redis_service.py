import redis
import json
import os
from typing import Dict, Any, Optional, List

class RedisService:
    """Service for handling Redis operations"""
    
    def __init__(self):
        """Initialize Redis connection using environment variables"""
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True  # Automatically decode responses to Python strings
        )
        self.session_prefix = "session:"
        self.token_prefix = "token:"
        self.user_prefix = "user:"
        self.default_expiry = 3600  # 1 hour in seconds

    def create_session(self, session_id: str, user_data: Dict[str, Any], expiry: int = 900) -> None:
        """Create a new session in Redis with expiration"""
        try:
            # Store session data
            self.redis_client.setex(
                f"session:{session_id}",
                expiry,
                json.dumps(user_data)
            )
            print(f"Redis session created: {session_id}")
        except Exception as e:
            print(f"Error creating Redis session: {e}")
            raise

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Redis"""
        try:
            data = self.redis_client.get(f"session:{session_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error retrieving Redis session: {e}")
            return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session in Redis"""
        try:
            return bool(self.redis_client.delete(f"session:{session_id}"))
        except Exception as e:
            print(f"Error invalidating Redis session: {e}")
            return False

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        try:
            # Get all session keys
            session_keys = self.redis_client.keys("session:*")
            sessions = []
            
            for key in session_keys:
                data = self.redis_client.get(key)
                if data:
                    session_data = json.loads(data)
                    if session_data.get("emp_code") == user_id:
                        sessions.append(session_data)
            
            return sessions
        except Exception as e:
            print(f"Error retrieving user sessions: {e}")
            return []

    def link_token_to_session(self, jwt_token: str, session_id: str) -> None:
        """Link a JWT token to a session"""
        try:
            # Store the mapping both ways for quick lookup
            self.redis_client.set(f"token:{jwt_token}", session_id)
            self.redis_client.set(f"session_token:{session_id}", jwt_token)
        except Exception as e:
            print(f"Error linking token to session: {e}")
            raise

    def get_session_by_token(self, jwt_token: str) -> Optional[Dict[str, Any]]:
        """Get session data using JWT token"""
        try:
            session_id = self.redis_client.get(f"token:{jwt_token}")
            if session_id:
                return self.get_session(session_id)
            return None
        except Exception as e:
            print(f"Error retrieving session by token: {e}")
            return None

    def update_session_activity(self, session_id: str) -> bool:
        """Update last activity timestamp of a session"""
        try:
            session_data = self.get_session(session_id)
            if session_data:
                session_data['last_activity'] = datetime.utcnow().isoformat()
                session_key = f"{self.session_prefix}{session_id}"
                self.redis_client.setex(
                    session_key,
                    self.default_expiry,
                    json.dumps(session_data)
                )
                return True
            return False
        except Exception as e:
            print(f"Redis error in update_session_activity: {str(e)}")
            return False

    def get_user_sessions(self, emp_code: str) -> list:
        """Get all active sessions for a user"""
        try:
            user_sessions_key = f"{self.user_prefix}{emp_code}:sessions"
            sessions = self.redis_client.smembers(user_sessions_key)
            return [
                self.get_session(session_id)
                for session_id in sessions
                if self.get_session(session_id)
            ]
        except Exception as e:
            print(f"Redis error in get_user_sessions: {str(e)}")
            return []

    def validate_token(self, token: str) -> Optional[str]:
        """Validate a token and return its associated session ID"""
        try:
            token_key = f"{self.token_prefix}{token}"
            return self.redis_client.get(token_key)
        except Exception as e:
            print(f"Redis error in validate_token: {str(e)}")
            return None 