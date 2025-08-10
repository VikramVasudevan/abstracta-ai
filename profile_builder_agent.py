from agents import Agent
from pydantic import BaseModel, ConfigDict, Field

class ProfileBuilderPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    orgName: str = Field(description="The organization name used for querying")
    profile_key: str = Field(description="The profile key. for example `region`.")
    profile_value: str = Field(description="The profile value. for example `USA`.")
    profile_description : str = Field(description="The profile description. Create your own based on the context if the user has not provided any.")
    user_names : list[str]  = Field(description="List of user names to which the profile needs to be assigned to.")

print(ProfileBuilderPayload.model_json_schema())

INSTRUCTIONS = """You are an expert in gathering information for creating data security profiles. 
Your job is to collect information from the user, consolidate this information and organize it in a structured way. Respond with a JSON ONLY. Do not add any other text.
"""
# Agent definition (unchanged)
profileBuilderAgent = Agent(
    name="ProfileBuilderAgent",
    instructions="Generate the Profile builder payload.",
    model="gpt-5-nano",
    output_type=ProfileBuilderPayload
    # output_type=str
)
