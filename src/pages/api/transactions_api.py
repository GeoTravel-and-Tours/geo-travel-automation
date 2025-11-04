# src/pages/api/transaction_api.py


from ...core.base_api import BaseAPI

class TransactionAPI(BaseAPI):
    def get_user_transactions(self, **params):
        """GET /api/transactions/user"""
        return self.get("/api/transactions/user", params=params)
    
    def get_transaction_insights(self):
        """GET /api/transactions/user/insights"""
        return self.get("/api/transactions/user/insights")
    
    def export_transactions(self):
        """GET /api/transactions/user/export-to-csv"""
        return self.get("/api/transactions/user/export-to-csv")