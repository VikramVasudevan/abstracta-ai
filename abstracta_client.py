import json
from nt import access
import requests
import os
from dotenv import load_dotenv
from api_builder_agent import APIBuilderPayload
from dq_rules_builder_agent import DQRulesBuilderPayload
from profile_builder_agent import ProfileBuilderPayload

load_dotenv(override=True)

ABSTRACTA_API_URL = "http://localhost:8080/rest/data/queryv2"
ABSTRACTA_METADATA_API_URL = "http://localhost:8080/rest/metadata"
ABSTRACTA_WEB_URL = "http://localhost/services"


class AbstractaClient:
    def __init__(self) -> None:
        self.organizations = []
        self.users = []

    def perform_auth(self):
        url = self.generate_auth_url()

        payload = f'grant_type=client_credentials&client_id={os.getenv("ABSTRACTA_CLIENT_ID")}&client_secret={os.getenv("ABSTRACTA_CLIENT_SECRET")}&audience={os.getenv("ABSTRACTA_AUDIENCE")}'
        print(payload)
        headers = {"content-type": "application/x-www-form-urlencoded"}

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.json()["access_token"]

    def generate_auth_url(self):
        return (
            "http://localhost:8180/auth/realms/abstracta/protocol/openid-connect/token"
        )

    def generate_web_url(
        self, org: str, app: str, datasource: str, service: str, version: str
    ):
        return f"{ABSTRACTA_WEB_URL}/{org}/{app}/{datasource}/{service}/{version}"

    def generate_api_url(
        self, org: str, app: str, datasource: str, service: str, version: str
    ):
        return f"{ABSTRACTA_API_URL}/{org}/{app}/{datasource}/{service}/{version}"

    def generate_system_api_url(self, service: str, version: str):
        return self.generate_api_url("ekahaa", "abstracta", "dq_repo", service, version)

    def get_data_from_api_url(self, access_token: str, api_url: str):
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": f"1 = 1",
            "from": 1,
            "to": 100,
            "columns": "*",
            "lean": True,
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Failed to get data: {response.status_code} {response.text}"
            )

    def get_data(
        self,
        access_token: str,
        org: str,
        app: str,
        datasource: str,
        service: str,
        version: str,
    ):
        url = self.generate_api_url(org, app, datasource, service, version)
        return self.get_data_from_api_url(access_token=access_token, api_url=url)

    def get_data_sources(self, access_token: str, org: str, app: str):
        request_url = self.generate_system_api_url("dq_databases", "0.0.0")

        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": f"dqdb_app_sys_no = (select app_sys_no from dq_apps where app_name = '{app}' and app_org_sys_no = (select org_sys_no from dq_org where org_name = '{org}'))",
            "from": 1,
            "to": 100,
            "columns": "dqdb_db_name",
            "lean": True,
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return [item["dqdb_db_name"] for item in data]
        else:
            raise Exception(
                f"Failed to get data sources: {response.status_code} {response.text}"
            )

    def get_organizations(self, access_token: str):
        print("Getting organizations")
        request_url = self.generate_system_api_url("dq_org", "0.0.0")

        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": "1 = 1",
            "from": 1,
            "to": 100,
            "columns": "*",
            "lean": True,
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.organizations = data
            return [item["org_name"] for item in data]
        else:
            raise Exception(
                f"Failed to get organizations: {response.status_code} {response.text}"
            )

    def get_applications(self, access_token: str, org: str):
        print(f"Getting applications for org: {org}")
        request_url = self.generate_system_api_url("dq_apps", "2.0.0")

        print(request_url)
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": f"app_org_sys_no = (select org_sys_no from dq_org where org_name = '{org}')",
            "from": 0,
            "to": 100,
            "columns": "app_name",
            "lean": True,
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        print(payload)

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return [item["app_name"] for item in data]
        else:
            raise Exception(
                f"Failed to get applications: {response.status_code} {response.text}"
            )

    def get_profiles(self, access_token: str, org: str):
        print(f"Getting profiles for org: {org}")
        request_url = self.generate_system_api_url("dq_profiles", "0.0.0")

        print(request_url)
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": f"prof_org_sys_no = (select org_sys_no from dq_org where org_name = '{org}')",
            "from": 0,
            "to": 100,
            "columns": "*",
            "lean": True,
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        print(payload)

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise Exception(
                f"Failed to get applications: {response.status_code} {response.text}"
            )

    def get_users(self, access_token: str):
        print(f"Getting users")
        request_url = self.generate_system_api_url("vw_users", "0.0.0")

        print(request_url)
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": f"",
            "from": 0,
            "to": 10000,
            "columns": "*",
            "lean": True,
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        print(payload)

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.users = data
            return data
        else:
            raise Exception(
                f"Failed to get users: {response.status_code} {response.text}"
            )

    def create_api(self, access_token: str, prmServiceInfo: APIBuilderPayload):
        print("Creating API ...", prmServiceInfo.model_dump())
        url = f"{ABSTRACTA_METADATA_API_URL}/{prmServiceInfo.orgName}/{prmServiceInfo.appName}/connectors/{prmServiceInfo.connectorType}/find/{prmServiceInfo.datasourceName}/services/add"
        print(url)

        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.post(url, headers=headers, json=prmServiceInfo.model_dump())

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Failed to create API: {response.status_code} {response.text}"
            )

    def grant_service_access(
        self,
        access_token: str,
        org: str,
        app: str,
        datasource: str,
        service: str,
        version: str,
        userId: list[str],
        roleName: list[str],
    ):
        url = f"{ABSTRACTA_METADATA_API_URL}/{org}/{app}/connectors/rdbms/find/{datasource}/services/find/{service}/{version}/grant"

        payload = {"userIdCsv": ",".join(userId), "roleNameCsv": ",".join(roleName)}

        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Failed to grant service access: {response.status_code} {response.text}"
            )

    def add_data_quality_rule(self, access_token: str, payload: DQRulesBuilderPayload):
        url = f"{ABSTRACTA_METADATA_API_URL}/{payload.orgName}/{payload.appName}/connectors/rdbms/find/{payload.datasourceName}/services/find/{payload.serviceName}/{payload.version}/fields/find/{payload.fieldName}/dqchecks/find/{payload.dqCheckName}"

        payload = json.loads(payload.dqRuleParametersPayloadJson)

        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            response_json = response.json()
            if response_json["StatusCode"] != 200:
                raise Exception(
                    f"Failed to add data quality rule: {response_json["StatusCode"]} {response_json["StatusMessage"]}"
                )
        else:
            raise Exception(
                f"Failed to add data quality rule: {response.status_code} {response.text}"
            )

    def add_profile(self, access_token: str, payload: ProfileBuilderPayload):
        if not self.organizations:
            self.get_organizations(access_token=access_token)
        try:
            org_id = [
                org["org_sys_no"]
                for org in self.organizations
                if org["org_name"] == payload.orgName
            ][0]
        except:
            raise Exception(f"unable to find a match for org {payload.orgName}")
        print("self.organizations = ", self.organizations)
        url = f"{ABSTRACTA_METADATA_API_URL}/admin/orgs/find/{org_id}/profiles/add"

        payload = {
            "name": f"{payload.profile_key}~{payload.profile_value}",
            "desc": payload.profile_description,
            "orgId": org_id,
        }
        print("payload = ", payload)
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            response_json = response.json()
            if response_json["statusCode"] != 200:
                raise Exception(
                    f"Failed to add profile: {response_json["statusCode"]} {response_json["statusMessage"]}"
                )
        else:
            raise Exception(
                f"Failed to add profile: {response.status_code} {response.text}"
            )

    def assign_profile_to_users(
        self, access_token: str, payload: ProfileBuilderPayload
    ):
        if not self.organizations:
            self.get_organizations(access_token=access_token)
        if not self.users:
            self.get_users(access_token=access_token)

        try:
            org_id = [
                org["org_sys_no"]
                for org in self.organizations
                if org["org_name"] == payload.orgName
            ][0]
        except:
            raise Exception(f"unable to find a match for org {payload.orgName}")

        try:
            profile_id = [
                profile["prof_sys_no"]
                for profile in self.get_profiles(
                    access_token=access_token, org=payload.orgName
                )
                if profile["prof_name"]
                == f"{payload.profile_key}~{payload.profile_value}"
            ][0]
        except:
            raise Exception(
                f"unable to find a match for profile {payload.profile_key}~{payload.profile_value}"
            )

        try:
            user_ids = [
                user["user_sys_no"]
                for user in self.users
                if user["user_id"] in payload.user_names
            ]
        except:
            raise Exception(f"unable to find a match for users {payload.user_names}")

        for user_id in user_ids:
            url = f"{ABSTRACTA_METADATA_API_URL}/admin/users/find/{user_id}/profileAttributes/manage"
            print("url = ", url)
            payload = {
                "id": None,
                "deleteAction": False,
                "userSysNo": user_id,
                "profileSysNo": profile_id,
            }

            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                response_json = response.json()
                if response_json["statusCode"] != 200:
                    raise Exception(
                        f"Failed to add profile: {response_json["statusCode"]} {response_json["statusMessage"]}"
                    )
            else:
                raise Exception(
                    f"Failed to add profile: {response.status_code} {response.text}"
                )

    def get_services(self, access_token: str, org: str, app: str, datasource: str):
        request_url = self.generate_system_api_url("vw_db_tables", "0.0.0")

        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": f" org_name = '{org}' AND app_name = '{app}' and dqdb_db_name='{datasource}'",
            "from": 1,
            "to": 100,
            "columns": "org_name, app_name, dqdb_db_name, dtbl_table_name, dtbl_version",
            "lean": True,
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise Exception(
                f"Failed to get services: {response.status_code} {response.text}"
            )

    def get_all_services(self, access_token: str):
        request_url = self.generate_system_api_url("vw_db_tables", "0.0.0")

        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "where": f" 1 = 1",
            "from": 1,
            "to": 1000,
            "columns": "org_name, app_name, dqdb_db_name, dtbl_table_name, dtbl_version",
            "lean": True,
            "orderby": "dtbl_when_created desc",
            "forUser": os.getenv("ABSTRACTA_FOR_USER"),
            "forUserSecret": os.getenv("ABSTRACTA_FOR_USER_SECRET"),
        }

        response = requests.post(request_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise Exception(
                f"Failed to get all services: {response.status_code} {response.text}"
            )
