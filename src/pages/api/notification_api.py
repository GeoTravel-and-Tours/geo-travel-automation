# src/pages/api/notification_api.py


from ...core.base_api import BaseAPI

class NotificationAPI(BaseAPI):
    def get_notifications(self):
        """GET /api/notifications"""
        return self.get("/api/notifications")
    
    def mark_as_read(self, notification_id):
        """PATCH /api/notifications/mark-as-read/{id}"""
        return self.patch(f"/api/notifications/mark-as-read/{notification_id}")
    
    def delete_notification(self, notification_id):
        """DELETE /api/notifications/{id}"""
        return self.delete(f"/api/notifications/{notification_id}")
    
    def delete_all_notifications(self):
        """DELETE /api/notifications"""
        return self.delete("/api/notifications")