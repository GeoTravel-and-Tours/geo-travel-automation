# src/pages/api/Partners_api/organization_api.py

import os
from src.core.partners_base_api import PartnersBaseAPI

class PartnersOrganizationAPI(PartnersBaseAPI):
    def __init__(self, auth_token=None):
        super().__init__()
        self.auth_token = auth_token
        if auth_token:
            self.set_auth_token(auth_token)
        self.endpoints = {
            'profile': '/api/org/profile',
            'reset_api_keys': '/api/org/reset-api-keys',
            'usage': '/api/org/usage',
            'daily_usage': '/api/org/usage/daily',
            'usage_range': '/api/org/usage/range'
        }
    
    def get_profile(self):
        return self.get(self.endpoints['profile'])
    
    def reset_api_keys(self):
        return self.get(self.endpoints['reset_api_keys'])
    
    def get_usage(self, mode='test', limit=None, page=None):
        params = {'mode': mode}
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['usage'], params=params)
    
    def get_daily_usage(self, mode='test', date=None):
        params = {'mode': mode}
        if date: params['date'] = date
        return self.get(self.endpoints['daily_usage'], params=params)
    
    def get_usage_range(self, mode='test', start_date=None, end_date=None):
        params = {'mode': mode}
        if start_date: params['startDate'] = start_date
        if end_date: params['endDate'] = end_date
        return self.get(self.endpoints['usage_range'], params=params)