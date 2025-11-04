# src/pages/api/blog_api.py

from ...core.base_api import BaseAPI

class BlogAPI(BaseAPI):
    def get_all_blogs(self, **params):
        """GET /api/blog/all"""
        return self.get("/api/blog/all", params=params)
    
    def get_single_blog(self, blog_id):
        """GET /api/blog/{id}"""
        return self.get(f"/api/blog/{blog_id}")
    
    def get_blog_comments(self, blog_id):
        """GET /api/blog/comment/blog/{blogId}"""
        return self.get(f"/api/blog/comment/blog/{blog_id}")
    
    def create_comment(self, comment_data):
        """POST /api/blog/comment/create"""
        return self.post("/api/blog/comment/create", json=comment_data)