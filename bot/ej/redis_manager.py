import redis
import os


class RedisManager:
    """
    Manages the Redis connection and operations.
    """

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=os.getenv("REDIS_PORT", 6379),
            db=os.getenv("REDIS_DB", 0),
            decode_responses=True,  # Decodes responses to strings
        )

    def get(self, key):
        """
        Get the value of a key from Redis.
        """
        return self.redis.get(key)

    def set(self, key, value):
        """
        Set the value of a key in Redis.
        """
        self.redis.set(key, value)

    def delete(self, key):
        """
        Delete a key from Redis.
        """
        self.redis.delete(key)

    def set_user_conversation(self, user_id, conversation_id):
        """
        Set the conversation ID for a specific user in Redis.
        """
        key = f"conversation_id:{user_id}"
        self.set(key, conversation_id)

    def get_user_conversation(self, user_id):
        """
        Get the conversation ID for a specific user from Redis.
        """
        key = f"conversation_id:{user_id}"
        return self.get(key)
