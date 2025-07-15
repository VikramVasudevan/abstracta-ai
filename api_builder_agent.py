from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal, Dict
from agents import Agent

apiBuilderPayloadSchema = {
    "name": "APIBuilderPayload",
    "schema": {
        "type": "object",
        "properties": {
            "serviceName": {
                "type": "string",
                "description": "The name of the service used to query the data source",
            },
            "serviceDisplayName": {
                "type": "string",
                "description": "The display name of the service",
            },
            "serviceDesc": {
                "type": "string",
                "description": "The description of the service",
            },
            "orgName": {
                "type": "string",
                "description": "The organization name used for querying",
            },
            "appName": {
                "type": "string",
                "description": "The application name inside the organization",
            },
            "datasourceName": {
                "type": "string",
                "description": "The data source name inside the app",
            },
            "originalResourceName": {
                "type": "string",
                "description": "The backend resource name",
            },
            "serviceType": {
                "type": "string",
                "enum": ["DIRECT", "CUSTOMSQL"],
                "description": "Service type: DIRECT or CUSTOMSQL",
            },
            "serviceCustomSQL": {
                "type": "string",
                "description": "Custom SQL query (for CUSTOMSQL only)",
            },
            "connectorType": {
                "type": "string",
                "enum": ["rdbms"],
                "description": "The connector type, always 'rdbms'",
            },
            "sampleParameterValues": {
                "type": "object",
                "description": "Parameter name/value pairs",
                "properties": {
                    "Placeholder1": {
                        "type": "string",
                        "description": "Placeholder - replace with the strict field you want",
                    }
                },
                "required": ["Placeholder1"],
                "additionalProperties": False,
            },
            "versionComments": {
                "type": "string",
                "description": "Comments for this version",
            },
            "versionType": {
                "type": "string",
                "enum": ["MAJOR", "MINOR", "REVISION"],
                "description": "Version type: MAJOR, MINOR, or REVISION",
            },
            "dataSecurityFilter": {
                "type": "string",
                "description": "The data security filter",
            },
        },
        "required": [
            "serviceName",
            "serviceDisplayName",
            "serviceDesc",
            "orgName",
            "appName",
            "datasourceName",
            "originalResourceName",
            "serviceType",
            "serviceCustomSQL",
            "connectorType",
            "sampleParameterValues",
            "versionComments",
            "versionType",
            "dataSecurityFilter",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


class SampleParameterValues(BaseModel):
    id: str = Field(description="Sample parameter name and value")  # dummy key


class APIBuilderPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    serviceName: str = Field(
        description="The name of the service used to query the data source"
    )
    serviceDisplayName: str = Field(
        description="The display name of the service", default="my default service"
    )
    serviceDesc: str = Field(
        description="The description of the service",
        default="my default service description",
    )
    orgName: str = Field(description="The organization name used for querying")
    appName: str = Field(description="The application name inside the organization")
    datasourceName: str = Field(description="The data source name inside the app")
    originalResourceName: str = Field(description="The backend resource name")
    serviceType: Literal["TABLE", "CUSTOMSQL"] = Field(
        description="Service type: TABLE or CUSTOMSQL", default="TABLE"
    )
    serviceCustomSQL: str = Field(
        description="Custom SQL query (for CUSTOMSQL only)", default=""
    )
    connectorType: Literal["rdbms"] = Field(
        description="The connector type, always 'rdbms'", default="rdbms"
    )
    sampleParameterValues: SampleParameterValues = Field(
        description="Parameter name/value pairs",
    )
    versionComments: str = Field(
        description="Comments for this version", default="my default version comments"
    )
    versionType: Literal["MAJOR", "MINOR", "REVISION"] = Field(
        description="Version type: MAJOR, MINOR, or REVISION", default="MAJOR"
    )
    dataSecurityFilter: str = Field(description="The data security filter", default="")


print(APIBuilderPayload.model_json_schema())

INSTRUCTIONS = """You are an expert API builder agent. 
Your job is to collect information from the user about the API they want to build. 
APIs are hiearchically stored in Abstracta. The first level is the organization, the second level is the application, the third level is the data source, and the fourth level is the API.
APIs can have multiple versions as they undergo changes. hardcode sampleParameterValues to {}.
Your job is to consolidate this information and organize it in a structured way. Respond with a JSON ONLY. Do not add any other text.  JSON has to be structured as below:
{APIBuilderPayload.model_json_schema()}
"""
# Agent definition (unchanged)
apiBuilderAgent = Agent(
    name="APIBuilderAgent",
    instructions="Generate the API builder payload.",
    model="gpt-4o-mini",
    output_type=APIBuilderPayload,
    # output_type=str
)
