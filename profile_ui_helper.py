import logging
import gradio as gr
from dotenv import load_dotenv
import pandas
from abstracta_client import AbstractaClient
from agents import Runner, trace
from markdown_formatter import format_url_as_markdown
from profile_builder_agent import profileBuilderAgent
from steps_executor import steps_executor, fn_report_build_progress

async def createProfile(requirements):

    """
    Main async function that runs the data quality rules building process.
    Yields status updates at each step for live progress display.
    """

    async def buildPayload(context):
        with trace("abstracta-profile-builder-agent"):
            payload_result = await Runner.run(profileBuilderAgent, requirements)
            logging.info("payload_result = %s", payload_result.final_output)
            return payload_result.final_output

    async def performAuth(context):
        return AbstractaClient().perform_auth()

    async def createProfile(context):
        access_token = context.get("abstracta_auth")
        payload_result = context.get("construct_payload")
        logging.info("access_token = %s", access_token)
        logging.info("payload_result = %s", payload_result)
        return AbstractaClient().add_profile(access_token, payload_result)

    async def assignProfileToUsers(context):
        access_token = context.get("abstracta_auth")
        payload_result = context.get("construct_payload")
        logging.info("access_token = %s", access_token)
        logging.info("payload_result = %s", payload_result)
        return AbstractaClient().assign_profile_to_users(access_token, payload_result)

    def makeComponentVisible(visible: bool = True):
        return gr.update(visible=visible)

    def updateComponentData(
        context: any, attribute: str, visible: bool = True, dataframe: bool = False
    ):
        if not dataframe:
            return gr.update(value=context[attribute], visible=visible)
        else:
            df = pandas.DataFrame(context[attribute])
            dq_df = pandas.json_normalize(df["_dq"])
            dq_df.columns = [f"_dq.{subcol}" for subcol in dq_df.columns]
            df_flat = pandas.concat([df.drop(columns=["_dq"]), dq_df], axis=1)

            return gr.update(value=df_flat, visible=visible)

    initial_outputs = (
        gr.update(
            value="Building Data Quality Rules ... please wait.", visible=True
        ),  # status_message
        "",  # api_url
        "",  # web_url
        makeComponentVisible(visible=False),  # json_view
        makeComponentVisible(visible=False),  # dataframe_view
    )

    steps_info = [
        {
            "key": "construct_payload",
            "name": "Constructing Profiles Builder Payload",
            "func": buildPayload,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        },
        {
            "key": "abstracta_auth",
            "name": "Authenticating to Abstracta API",
            "func": performAuth,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        },
        {
            "key": "create_profile",
            "name": "Creating Profile",
            "func": createProfile,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        },
        {
            "key": "assign_profile",
            "name": "Assigning Profile to users",
            "func": assignProfileToUsers,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        }
        # Add more steps
    ]

    # final_outputs = ("Final API URL", "Final Web URL", data, pd.DataFrame(data))

    async for step in steps_executor(
        steps_info=steps_info,
        initial_outputs=initial_outputs,
        build_progress_fn=fn_report_build_progress,
        final_message="✅ All done!",
        final_outputs=None,
    ):
        logging.debug("results = %s", step)
        yield step
