from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal, Dict
from agents import Agent, ModelSettings

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
    dataSecurityFilter: str = Field(description="The data security filter only if provided by the user. Do not derive this yourself. Default to empty string ''.", default="")


print(APIBuilderPayload.model_json_schema())

INSTRUCTIONS = """
🚫 ABSOLUTE SQL RULES 🚫
1. NEVER use parameters or placeholders in SQL:
   - Examples of banned syntax: `@region`, `${region}`, `:region`, `{region}`, `?`, `$1`
2. NEVER insert profile filter syntax or literal values directly into SQL.
3. NEVER use \\n in SQL — must be a single continuous line.
4. If the user specifies any profile-based filtering condition (e.g., by region, state, date), store it in `dataSecurityFilter` only.
5. Literal filters may be kept part of the serviceCustomSQL
6. NEVER add a semicolon(;) at the end of the generated custom SQL

✅ Example of correct filter handling:
- dataSecurityFilter: "s.state IN (%(PROFILE:my_allowed_states)%)"
- serviceCustomSQL: "SELECT o.* FROM sales.orders AS o JOIN sales.stores AS s ON o.store_id = s.store_id"

✅ Example without filter:
- dataSecurityFilter: ""
- serviceCustomSQL: "SELECT o.* FROM sales.orders AS o JOIN sales.stores AS s ON o.store_id = s.store_id"

---

Your job:
1. Collect all required API details.
2. APIs are stored hierarchically: organization → application → data source → API.
3. Always hardcode `sampleParameterValues` to `{}`.
4. The `dataSecurityFilter` field must exactly match the filtering clause (without the `WHERE` keyword).
5. The `serviceCustomSQL` must not include the `{dataSecurityFilter}`. and it should not include a semicolon at the end.
6. Respond in JSON ONLY, following APIBuilderPayload schema.
7. Do not add commentary, markdown, or explanations.

REPEAT: No variables in SQL. No profile syntax in SQL. All profile based filters go in `dataSecurityFilter`..
"""



# Agent definition (unchanged)
model_settings = ModelSettings(temperature=0.7)  #

apiBuilderAgent = Agent(
    name="APIBuilderAgent",
    instructions="Generate the API builder payload.",
    model="gpt-4o-mini",
    output_type=APIBuilderPayload,
    # output_type=str
    model_settings=model_settings
)
