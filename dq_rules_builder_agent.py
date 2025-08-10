import json
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal, Dict
from agents import Agent

allowed_checks = [
    {
        "id": "ISNOTNULL",
        "description": "Check if value is not null",
        "class": "AbstractaDataQualityIsNotNullCheck",
        "parameters": [],
    },
    {
        "id": "ISNULL",
        "description": "Check if value is null",
        "class": "AbstractaDataQualityIsNullCheck",
        "parameters": [],
    },
    {
        "id": "IS_DATE",
        "description": "Check if value is a date",
        "class": "AbstractaDataQualityIsDateCheck",
        "parameters": [],
    },
    {
        "id": "IS_NUMERIC",
        "description": "Check if value is a number",
        "class": "AbstractaDataQualityIsNumericCheck",
        "parameters": [],
    },
    {
        "id": "IS_NOT_NUMERIC",
        "description": "Check if value is NOT a number",
        "class": "AbstractaDataQualityIsNotNumericCheck",
        "parameters": [],
    },
    {
        "id": "IS_REGEX_MATCH",
        "description": "Check if value matches a given regex pattern",
        "class": "AbstractaDataQualityMatchesRegexCheck",
        "parameters": [{"name": "pattern", "label": "Regex Pattern", "type": "string"}],
    },
    {
        "id": "NUMERIC_RANGE_BETWEEN",
        "description": "Check if value is within a numeric range",
        "class": "AbstractaDataQualityNumericRangeCheck",
        "parameters": [
            {"name": "min", "label": "Minimum Value", "type": "number"},
            {"name": "max", "label": "Maximum Value", "type": "number"},
        ],
    },
    {
        "id": "STRING_LENGTH_RANGE_BETWEEN",
        "description": "Check if length of string is within a numeric range",
        "class": "AbstractaDataQualityStringLengthCheck",
        "parameters": [
            {"name": "min", "label": "Minimum Value", "type": "number"},
            {"name": "max", "label": "Maximum Value", "type": "number"},
        ],
    },
]


class DQRulesBuilderPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    orgName: str = Field(description="The organization name used for querying")
    appName: str = Field(description="The application name inside the organization")
    connectorType: Literal["rdbms"] = Field(
        description="The connector type, always 'rdbms'", default="rdbms"
    )
    datasourceName: str = Field(description="The data source name inside the app")
    serviceName: str = Field(
        description="The name of the service used to query the data source"
    )
    version: str = Field(
        description="Service version in the format {major}.{minor}.{revision}. For e.g. 1.4.10"
    )
    dqCheckName: Literal[*[check["id"] for check in allowed_checks]] = Field(
        description=f"Name of the data quality check. Uppercase only. No special characters."
    )
    fieldName: str = Field(description="Name of the field to apply the rule to.")
    dqRuleParametersPayloadJson: str = Field(
        description=f"A string containing a dict of parameter name and value for the given dqCheckName. Refer to this configuration to get the supported parameters for a specific dq check. \n {json.dumps(allowed_checks,indent=1)}"
    )


print(DQRulesBuilderPayload.model_json_schema())

INSTRUCTIONS = """You are an expert  in configuring data quality rules for a given data set. 
Your job is to collect information from the user about the API for which they want to configure DQ checks. 
The org, app, datasource, service and version, field and dq check name need to be taken literally as provided by the user. DO NOT transform or manipulate the information provided by the user - use it as it is.
APIs are hiearchically stored in Abstracta. The first level is the organization, the second level is the application, the third level is the data source, and the fourth level is the API.
APIs can have multiple versions as they undergo changes.
Your job is to consolidate this information and organize it in a structured way. Respond with a JSON ONLY. Do not add any other text.
"""
# Agent definition (unchanged)
dqRulesBuilderAgent = Agent(
    name="DQRulesBuilderAgent",
    instructions="Generate the Data Quality Rules builder payload.",
    model="gpt-5-nano",
    output_type=DQRulesBuilderPayload,
    # output_type=str
)
