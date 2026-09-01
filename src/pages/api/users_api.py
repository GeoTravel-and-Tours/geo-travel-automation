# src/pages/api/users_api.py

"""API client for the retail ``/api/users/me`` endpoints.

Covers reading and updating the currently authenticated user's profile.
"""

from ...core.base_api import BaseAPI

class UserAPI(BaseAPI):
    """Client for the ``/api/users/me`` resource (the logged-in user's own profile).

    Both methods are thin wrappers around ``BaseAPI`` and return the raw
    ``requests.Response``.
    """

    def get_user_profile(self):
        """Fetch the current user's profile.

        GET /api/users/me

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/users/me")

    def update_user_profile(self, profile_data):
        """Update the current user's profile.

        PATCH /api/users/me

        Args:
            profile_data (dict): Fields to update on the user's profile.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.patch("/api/users/me", json=profile_data)