from pydantic import BaseModel, Field
from typing import Literal, Dict
from agents import Agent

INSTRUCTIONS = """You are an expert API builder agent. 
Your job is to collect information from the user about the API they want to build. 
APIs are hiearchically stored in Abstracta. The first level is the organization, the second level is the application, the third level is the data source, and the fourth level is the API.
APIs can have multiple versions as they undergo changes.
Your job is to consolidate this information and organize it in a structured way. Respond with a JSON. Do not add any other text.  
"""

class APIBuilderPayload(BaseModel):
    serviceName: str = Field(description="The name of the service used to query the data source")
    serviceDisplayName: str = Field(description="The display name of the service")
    serviceDesc: str = Field(description="The description of the service")
    orgName: str = Field(description="The organization name used for querying")
    appName: str = Field(description="The application name inside the organization")
    datasourceName: str = Field(description="The data source name inside the app")
    originalResourceName: str = Field(description="The backend resource name")
    serviceType: Literal["DIRECT", "CUSTOMSQL"] = Field(description="Service type: DIRECT or CUSTOMSQL")
    serviceCustomSQL: str = Field(description="Custom SQL query (for CUSTOMSQL only)")
    connectorType: Literal["rdbms"] = Field(description="The connector type, always 'rdbms'")
    # sampleParameterValues: Dict[str, str] = Field(description="Parameter name/value pairs")
    versionComments: str = Field(description="Comments for this version")
    versionType: Literal["MAJOR", "MINOR", "REVISION"] = Field(description="Version type: MAJOR, MINOR, or REVISION")
    dataSecurityFilter: str = Field(description="The data security filter")

# Agent definition (unchanged)
apiBuilderAgent = Agent(
    name="APIBuilderAgent",
    instructions="Generate the API builder payload.",
    model="gpt-4o-mini",
    output_type=APIBuilderPayload  # strict schema enabled by default
)

# class MyOutputModel(BaseModel):
#     foo: str = Field(description="Foo is a string value")
#     bar: Literal["A", "B"] = Field(description="Bar can be A or B")
#     data: Dict[str, str] = Field(description="A mapping of keys to string values")

# print(MyOutputModel.model_json_schema())

# apiBuilderAgent = Agent(
#     name="TestAgent",
#     instructions="You are a helpful assistant.",
#     model="gpt-4o-mini",
#     output_type=MyOutputModel
# )