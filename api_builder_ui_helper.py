import asyncio
import json
import os
import time
import logging
import pandas
import gradio as gr
import gradio.themes as themes
from dotenv import load_dotenv
from abstracta_client import AbstractaClient
from api_builder_agent import apiBuilderAgent
from agents import Runner, trace
from dq_rules_ui_helper import buildDataQualityRulesForExistingAPI
from markdown_formatter import format_url_as_markdown
from steps_executor import steps_executor, fn_report_build_progress


def remove_dq(obj):
    """Recursively remove any '_dq' keys from dicts/lists."""
    if isinstance(obj, dict):
        return {k: remove_dq(v) for k, v in obj.items() if k != "_dq"}
    elif isinstance(obj, list):
        return [remove_dq(item) for item in obj]
    else:
        return obj


async def buildAPI(requirements):
    """
    Main async function that runs the API building process.
    Yields status updates at each step for live progress display.
    """

    async def buildPayload(context):
        with trace("abstracta-api-builder-agent"):
            payload_result = await Runner.run(apiBuilderAgent, requirements)
            logging.info("payload_result = %s", payload_result.final_output)
            return payload_result.final_output

    async def performAuth(context):
        return AbstractaClient().perform_auth()

    async def createAPI(context):
        access_token = context.get("abstracta_auth")
        payload_result = context.get("construct_payload")
        logging.info("access_token = %s", access_token)
        logging.info("payload_result = %s", payload_result)
        return AbstractaClient().create_api(access_token, payload_result)

    async def grantAccess(context):
        apiCreationResponse = context["create_api"]
        access_token = context.get("abstracta_auth")
        payload = context.get("construct_payload")
        newServiceVersion = apiCreationResponse["service-info"]["tables"][0][
            "dtbl_version"
        ]
        AbstractaClient().grant_service_access(
            access_token,
            payload.orgName,
            payload.appName,
            payload.datasourceName,
            payload.serviceName,
            newServiceVersion,
            [os.getenv("ABSTRACTA_FOR_USER") or ""],
            ["VIEWER", "EDITOR", "CREATOR"],
        )

    async def generateApiUrl(context):
        payload = context.get("construct_payload")
        apiCreationResponse = context["create_api"]
        newServiceVersion = apiCreationResponse["service-info"]["tables"][0][
            "dtbl_version"
        ]

        return format_url_as_markdown(
            "API URL",
            AbstractaClient().generate_api_url(
                payload.orgName,
                payload.appName,
                payload.datasourceName,
                payload.serviceName,
                newServiceVersion,
            ),
        )

    async def generateWebUrl(context):
        payload = context.get("construct_payload")
        apiCreationResponse = context["create_api"]
        newServiceVersion = apiCreationResponse["service-info"]["tables"][0][
            "dtbl_version"
        ]

        return format_url_as_markdown(
            "Web URL",
            AbstractaClient().generate_web_url(
                payload.orgName,
                payload.appName,
                payload.datasourceName,
                payload.serviceName,
                newServiceVersion,
            ),
        )

    async def fetchData(context):
        access_token = context.get("abstracta_auth")
        payload = context.get("construct_payload")
        apiCreationResponse = context["create_api"]
        newServiceVersion = apiCreationResponse["service-info"]["tables"][0][
            "dtbl_version"
        ]
        data = AbstractaClient().get_data(
            access_token,
            payload.orgName,
            payload.appName,
            payload.datasourceName,
            payload.serviceName,
            newServiceVersion,
        )
        data = remove_dq(data)
        return data

    def makeComponentVisible(visible: bool = True):
        return gr.update(visible=visible)

    def updateComponentData(context: any, attribute: str, visible: bool = True, dataframe : bool = False):
        if not dataframe:
            return gr.update(value=context[attribute], visible=visible)
        else:
            return gr.update(value=pandas.DataFrame(context[attribute]), visible=visible)

    initial_outputs = (
        "Building API ... please wait.",  # status_message
        "",  # api_url
        "",  # web_url
        makeComponentVisible(visible=False),  # json_view
        makeComponentVisible(visible=False),  # dataframe_view
    )

    steps_info = [
        {
            "key": "construct_payload",
            "name": "Constructing API Builder Payload",
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
            "key": "create_api",
            "name": "Creating API",
            "func": createAPI,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        },
        {
            "key": "grant_api_access",
            "name": "Grant API Access",
            "func": grantAccess,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        },
        {
            "key": "gen_api_url",
            "name": "Generate API URL",
            "func": generateApiUrl,
            "yield": [
                lambda context: updateComponentData(
                    context := context, attribute="gen_api_url", visible=True
                ),
                lambda context: "",
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        },
        {
            "key": "gen_web_url",
            "name": "Generate Web URL",
            "func": generateWebUrl,
            "yield": [
                lambda context: updateComponentData(
                    context := context, attribute="gen_api_url", visible=True
                ),
                lambda context: updateComponentData(
                    context := context, attribute="gen_web_url", visible=True
                ),
                lambda context: makeComponentVisible(visible=False),
                lambda context: makeComponentVisible(visible=False),
            ],
        },
        {
            "key": "fetch_data",
            "name": "Fetching data from API",
            "func": fetchData,
            "yield": [
                lambda context: updateComponentData(
                    context := context, attribute="gen_api_url", visible=True
                ),
                lambda context: updateComponentData(
                    context := context, attribute="gen_web_url", visible=True
                ),
                lambda context: updateComponentData(
                    context := context, attribute="fetch_data", visible=False
                ),
                lambda context: updateComponentData(
                    context := context, attribute="fetch_data", visible=True, dataframe=True
                ),
            ],
        },
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
