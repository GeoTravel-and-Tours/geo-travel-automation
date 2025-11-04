# src/pages/api/user_api.py


from ...core.base_api import BaseAPI

class UserAPI(BaseAPI):
    def get_user_profile(self):
        """GET /api/users/me"""
        return self.get("/api/users/me")
    
    def update_user_profile(self, profile_data):
        """PATCH /api/users/me"""
        return self.patch("/api/users/me", json=profile_data)