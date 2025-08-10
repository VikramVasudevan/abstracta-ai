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
    Main async function that runs the API build process.
    Yields status updates at each step for live progress display.
    """
    # Step 0 — Hide outputs immediately
    yield (
        "Building API... please wait.",  # status_message
        "",  # api_url
        "",  # web_url
        gr.update(visible=False),  # json_view
        gr.update(visible=False),  # dataframe_view
    )
    await asyncio.sleep(0.5)

    steps = [
        "Generating API based on your requirements",
        "Constructing API Builder Payload",
        "Authenticating to Abstracta API",
        "Creating API",
        "Granting service access",
        "Generating API URLs",
        "Fetching data from API",
        "Finalizing results",
    ]

    def build_progress(current_step, animate=False):
        """Return HTML showing step progress with optional animation."""
        return fn_report_build_progress(steps, current_step, animate)

    logging.info(f"User request: {requirements}")

    # Step 0 - start
    yield build_progress(0, True), "", "", [], []
    with trace("abstracta-builder-agent"):
        payload_result = await Runner.run(apiBuilderAgent, requirements)
    # Step 0 - done
    yield build_progress(0, False), "", "", [], []
    await asyncio.sleep(0.5)

    # Step 1 - start
    yield build_progress(1, True), "", "", [], []
    access_token = AbstractaClient().perform_auth()
    # Step 1 - done
    yield build_progress(1, False), "", "", [], []
    await asyncio.sleep(0.5)

    # Step 2 - start
    yield build_progress(2, True), "", "", [], []
    payload = payload_result.final_output
    apiCreationResponse = AbstractaClient().create_api(access_token, payload)
    logging.info("API created successfully.")
    # Step 2 - done
    yield build_progress(2, False), "", "", [], []
    await asyncio.sleep(0.5)

    # Step 3 - start
    yield build_progress(3, True), "", "", [], []
    newServiceVersion = apiCreationResponse["service-info"]["tables"][0]["dtbl_version"]
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
    logging.info("Service access granted.")
    # Step 3 - done
    yield build_progress(3, False), "", "", [], []
    await asyncio.sleep(0.5)

    # Step 4 - start
    yield build_progress(4, True), "", "", [], []
    new_api_url = format_url_as_markdown(
        "API URL",
        AbstractaClient().generate_api_url(
            payload.orgName,
            payload.appName,
            payload.datasourceName,
            payload.serviceName,
            newServiceVersion,
        ),
    )
    new_web_url = format_url_as_markdown(
        "Web URL",
        AbstractaClient().generate_web_url(
            payload.orgName,
            payload.appName,
            payload.datasourceName,
            payload.serviceName,
            newServiceVersion,
        ),
    )
    # Step 4 - done
    yield build_progress(4, False), new_api_url, new_web_url, [], []
    await asyncio.sleep(0.5)

    # Step 5 - start
    yield build_progress(5, True), new_api_url, new_web_url, [], []
    data = AbstractaClient().get_data(
        access_token,
        payload.orgName,
        payload.appName,
        payload.datasourceName,
        payload.serviceName,
        newServiceVersion,
    )
    data = remove_dq(data)

    # Step 5 - done
    yield build_progress(5, False), new_api_url, new_web_url, data, pandas.DataFrame(
        data
    )
    await asyncio.sleep(0.5)

    # Step 6 - start (finalizing)
    yield build_progress(6, True), new_api_url, new_web_url, data, pandas.DataFrame(
        data
    )
    logging.info("Process completed successfully.")
    # Step 6 - done
    yield (
        "✅ API built successfully!",
        new_api_url,
        new_web_url,
        gr.update(value=data, visible=False),
        gr.update(value=pandas.DataFrame(data), visible=True),
    )
    # yield build_progress(
    #     total_steps, False
    # ), new_api_url, new_web_url, data, pandas.DataFrame(data)
    await asyncio.sleep(0.5)
