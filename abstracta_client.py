import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)

ABSTRACTA_API_URL="http://localhost:8080/rest/data/queryv2"

class AbstractaClient:
    def perform_auth(self):
        url = self.generate_auth_url()

        payload = f'grant_type=client_credentials&client_id={os.getenv("ABSTRACTA_CLIENT_ID")}&client_secret={os.getenv("ABSTRACTA_CLIENT_SECRET")}&audience={os.getenv("ABSTRACTA_AUDIENCE")}'
        print(payload)
        headers = {
        'content-type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.json()["access_token"]

    def generate_auth_url(self):
        return "http://localhost:8180/auth/realms/abstracta/protocol/openid-connect/token"

    def generate_api_url(self, org : str, app : str, datasource : str, service : str, version : str):
        return f"{ABSTRACTA_API_URL}/{org}/{app}/{datasource}/{service}/{version}"

    def generate_system_api_url(self, service:str, version: str):
        return self.generate_api_url("ekahaa", "abstracta", "dq_repo", service, version)

    def get_data_sources(self, access_token: str, org: str, app: str):
        request_url = self.generate_system_api_url("dq_databases", "0.0.0")

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        payload = {
            "where": f"dqdb_app_sys_no = (select app_sys_no from dq_app where app_name = '{app}' and org_sys_no = (select org_sys_no from dq_org where org_name = '{org}'))",
            "from" : 1,
            "to" : 100,
            "columns" : "dqdb_db_name",
            "lean" : True
        }

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return [item["dqdb_db_name"] for item in data]
        else:
            raise Exception(f"Failed to get data sources: {response.status_code} {response.text}")

    def get_organizations(self, access_token: str):
        request_url = self.generate_system_api_url("dq_org", "0.0.0")

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        payload = {
            "where": "1 = 1",
            "from" : 1,
            "to" : 100,
            "columns" : "org_name",
            "lean" : True
        }

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return [item["org_name"] for item in data]
        else:
            raise Exception(f"Failed to get organizations: {response.status_code} {response.text}")
    
    def get_applications(self, access_token: str, org: str):
        print(f"Getting applications for org: {org}")
        request_url = self.generate_system_api_url("dq_apps", "0.0.0")

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        payload = {
            "where": f"app_org_sys_no = (select org_sys_no from dq_org where org_name = '{org}')",
            "from" : 1,
            "to" : 100,
            "columns" : "app_name",
            "lean" : True
        }

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return [item["app_name"] for item in data]
        else:
            raise Exception(f"Failed to get applications: {response.status_code} {response.text}")