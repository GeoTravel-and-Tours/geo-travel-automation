"""
src/pages/api/blogs_api.py

API client for the /api/blog endpoints of the Geo Travel backend:
listing/fetching blog posts and reading/creating blog comments.
"""

from ...core.base_api import BaseAPI

class BlogAPI(BaseAPI):
    """API client for the /api/blog resource (blog posts and comments).

    All methods hit endpoints under the ``/api/blog/*`` prefix.
    """

    def get_all_blogs(self, **params):
        """List blog posts.

        GET /api/blog/all

        Args:
            **params: Arbitrary query parameters (e.g. pagination,
                filters) forwarded as-is to the request's query string.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/blog/all", params=params)

    def get_single_blog(self, blog_id):
        """Fetch a single blog post by id.

        GET /api/blog/{id}

        Args:
            blog_id: Identifier of the blog post to fetch.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get(f"/api/blog/{blog_id}")

    def get_blog_comments(self, blog_id):
        """List comments for a blog post.

        GET /api/blog/comment/blog/{blogId}

        Args:
            blog_id: Identifier of the blog post whose comments are
                being fetched.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get(f"/api/blog/comment/blog/{blog_id}")

    def create_comment(self, comment_data):
        """Create a new comment on a blog post.

        POST /api/blog/comment/create

        Args:
            comment_data (dict): Comment payload (e.g. blog id, author,
                text) sent as the JSON request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/blog/comment/create", json=comment_data)
