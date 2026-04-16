"""API dependencies for dependency injection."""

from app.api.websocket import ConnectionManager

# Singleton instance managed by dependency injection
_manager_instance: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton ConnectionManager instance.

    This function provides a single instance of ConnectionManager
    for the entire application, allowing for proper dependency injection
    and testability.

    Returns:
        ConnectionManager: The singleton connection manager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ConnectionManager()
    return _manager_instance
