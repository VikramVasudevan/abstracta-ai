import logging
import gradio as gr
from dotenv import load_dotenv
import pandas
from abstracta_client import AbstractaClient
from api_builder_agent import apiBuilderAgent
from agents import Runner, trace
from markdown_formatter import format_url_as_markdown
from steps_executor import steps_executor, fn_report_build_progress
from dq_rules_builder_agent import dqRulesBuilderAgent


async def buildDataQualityRulesForExistingAPI(requirements):
    """
    Main async function that runs the data quality rules building process.
    Yields status updates at each step for live progress display.
    """

    async def buildPayload(context):
        with trace("abstracta-dq-rules-builder-agent"):
            payload_result = await Runner.run(dqRulesBuilderAgent, requirements)
            logging.info("payload_result = %s", payload_result.final_output)
            return payload_result.final_output

    async def performAuth(context):
        return AbstractaClient().perform_auth()

    async def createDataQualityRule(context):
        access_token = context.get("abstracta_auth")
        payload_result = context.get("construct_payload")
        logging.info("access_token = %s", access_token)
        logging.info("payload_result = %s", payload_result)
        return AbstractaClient().add_data_quality_rule(access_token, payload_result)

    async def generateApiUrl(context):
        payload = context.get("construct_payload")
        return format_url_as_markdown(
            "API URL",
            AbstractaClient().generate_api_url(
                payload.orgName,
                payload.appName,
                payload.datasourceName,
                payload.serviceName,
                payload.version,
            ),
        )

    async def generateWebUrl(context):
        payload = context.get("construct_payload")
        return format_url_as_markdown(
            "Web URL",
            AbstractaClient().generate_web_url(
                payload.orgName,
                payload.appName,
                payload.datasourceName,
                payload.serviceName,
                payload.version,
            ),
        )

    async def fetchData(context):
        access_token = context.get("abstracta_auth")
        payload = context.get("construct_payload")
        return AbstractaClient().get_data(
            access_token,
            payload.orgName,
            payload.appName,
            payload.datasourceName,
            payload.serviceName,
            payload.version,
        )

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
        "Building Data Quality Rules ... please wait.",  # status_message
        "",  # api_url
        "",  # web_url
        gr.update(visible=False),  # json_view
        gr.update(visible=False),  # dataframe_view
    )

    steps_info = [
        {
            "key": "construct_payload",
            "name": "Constructing Data Quality Rule Builder Payload",
            "func": buildPayload,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: gr.update(visible=False),
                lambda context: gr.update(visible=False),
            ],
        },
        {
            "key": "abstracta_auth",
            "name": "Authenticating to Abstracta API",
            "func": performAuth,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: gr.update(visible=False),
                lambda context: gr.update(visible=False),
            ],
        },
        {
            "key": "create_dq_rule",
            "name": "Creating Data Quality Rule",
            "func": createDataQualityRule,
            "yield": [
                lambda context: "",
                lambda context: "",
                lambda context: gr.update(visible=False),
                lambda context: gr.update(visible=False),
            ],
        },
        {
            "key": "gen_api_url",
            "name": "Generate API URL",
            "func": generateApiUrl,
            "yield": [
                lambda context: gr.update(value=context["gen_api_url"], visible=True),
                lambda context: "",
                lambda context: gr.update(visible=False),
                lambda context: gr.update(visible=False),
            ],
        },
        {
            "key": "gen_web_url",
            "name": "Generate Web URL",
            "func": generateWebUrl,
            "yield": [
                lambda context: gr.update(value=context["gen_api_url"], visible=True),
                lambda context: gr.update(value=context["gen_web_url"], visible=True),
                lambda context: gr.update(visible=False),
                lambda context: gr.update(visible=False),
            ],
        },
        {
            "key": "fetch_data",
            "name": "Fetching data from API",
            "func": fetchData,
            "yield": [
                lambda context: gr.update(value=context["gen_api_url"], visible=True),
                lambda context: gr.update(value=context["gen_web_url"], visible=True),
                lambda context: gr.update(value=context["fetch_data"], visible=False),
                lambda context: updateComponentData(
                    context := context,
                    attribute="fetch_data",
                    visible=True,
                    dataframe=True,
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
