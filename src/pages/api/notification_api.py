# src/pages/api/notification_api.py

"""API client for the retail ``/api/notifications`` endpoints.

Covers listing, marking as read, and deleting a logged-in user's
notifications.
"""

from ...core.base_api import BaseAPI

class NotificationAPI(BaseAPI):
    """Client for the ``/api/notifications`` resource.

    All methods are thin wrappers around the corresponding ``BaseAPI``
    HTTP verb and return the raw ``requests.Response`` for the caller to
    assert on.
    """

    def get_notifications(self):
        """Fetch the current user's notifications.

        GET /api/notifications

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/notifications")

    def mark_as_read(self, notification_id):
        """Mark a single notification as read.

        PATCH /api/notifications/mark-as-read/{id}

        Args:
            notification_id: ID of the notification to mark as read.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.patch(f"/api/notifications/mark-as-read/{notification_id}")

    def delete_notification(self, notification_id):
        """Delete a single notification.

        DELETE /api/notifications/{id}

        Args:
            notification_id: ID of the notification to delete.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.delete(f"/api/notifications/{notification_id}")

    def delete_all_notifications(self):
        """Delete all notifications for the current user.

        DELETE /api/notifications

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.delete("/api/notifications")