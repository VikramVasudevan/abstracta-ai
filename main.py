"""
Abstracta AI-Driven API Builder
--------------------------------
This app allows users to describe API requirements in natural language and
automatically builds the API using Abstracta's services. It includes:
- Multiple ready-made example prompts
- Animated progress tracker
- Data previewer
- Logging with timestamps
"""

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


# --------------------- LOGGING CONFIG ---------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)


def remove_dq(obj):
    """Recursively remove any '_dq' keys from dicts/lists."""
    if isinstance(obj, dict):
        return {k: remove_dq(v) for k, v in obj.items() if k != "_dq"}
    elif isinstance(obj, list):
        return [remove_dq(item) for item in obj]
    else:
        return obj

async def typewriter_effect(example_text):
    """Yields text one character at a time to simulate typing."""
    typed_text = ""
    for char in example_text:
        typed_text += char
        yield typed_text
        await asyncio.sleep(0.02)  # typing speed


# --------------------- DATA FETCHING HELPERS ---------------------


def get_data(org_name, app_name, datasource_name, service_name, service_version):
    """
    Fetch data from Abstracta API and return it as a DataFrame.
    """
    logging.info(
        f"Fetching data: {org_name}/{app_name}/{datasource_name}/{service_name}/{service_version}"
    )
    access_token = AbstractaClient().perform_auth()
    return (
        f"[Open in Abstracta]({AbstractaClient().generate_web_url(org_name, app_name, datasource_name, service_name, service_version)})",
        gr.update(
            label=f"{org_name}/{app_name}/{datasource_name}/{service_name}/{service_version}",
            value=pandas.DataFrame(
                AbstractaClient().get_data(
                    access_token,
                    org_name,
                    app_name,
                    datasource_name,
                    service_name,
                    service_version,
                )
            ),
        ),
    )


def get_all_services():
    """Return all available services from Abstracta."""
    return AbstractaClient().get_all_services(AbstractaClient().perform_auth())


def get_services(org_name, app_name, datasource_name):
    """Return services for a given organization, application, and datasource."""
    return AbstractaClient().get_services(
        AbstractaClient().perform_auth(), org_name, app_name, datasource_name
    )


def get_organizations():
    """Return all available organizations."""
    return AbstractaClient().get_organizations(AbstractaClient().perform_auth())


def get_applications(org_name):
    """Return available applications for a given organization."""
    return gr.update(
        choices=AbstractaClient().get_applications(
            AbstractaClient().perform_auth(), org_name
        ),
        value=None,
    )


def get_data_sources(org_name, app_name):
    """Return available datasources for a given organization and application."""
    return gr.update(
        choices=AbstractaClient().get_data_sources(
            AbstractaClient().perform_auth(), org_name, app_name
        ),
        value=None,
    )


# --------------------- UTILS ---------------------


def format_url_as_markdown(label, url):
    """Format a clickable markdown link."""
    return f"### {label}\n[{label}]({url})"


def requirements_on_change(requirements):
    """Enable or disable build button based on text area content."""
    return gr.update(interactive=bool(requirements.strip()))


# --------------------- MAIN API BUILD PROCESS ---------------------


async def gatherInfo(requirements):
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
        gr.update(visible=False)   # dataframe_view
    )

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
    total_steps = len(steps)

    def build_progress(current_step, animate=False):
        """Return HTML showing step progress with optional animation."""
        html = "<ul style='list-style:none;padding:0'>"
        for i, step in enumerate(steps):
            if i < current_step:
                html += f"<li>✅ <b>{step}</b></li>"
            elif i == current_step:
                dots = "." * ((int(time.time() * 2) % 3) + 1) if animate else ""
                html += f"<li>⏳ <b>{step}{dots}</b></li>"
            else:
                html += f"<li>⬜ {step}</li>"
        html += "</ul>"

        percent = int((current_step / total_steps) * 100)
        html += (
            f"<div style='background:#eee;border-radius:8px;height:12px;overflow:hidden;margin-top:8px'>"
            f"<div style='background:#2563eb;height:100%;width:{percent}%;transition:width 0.3s'></div>"
            f"</div>"
        )
        return html

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
            gr.update(value=pandas.DataFrame(data), visible=True)
        )    
    # yield build_progress(
    #     total_steps, False
    # ), new_api_url, new_web_url, data, pandas.DataFrame(data)
    await asyncio.sleep(0.5)


# --------------------- RENDER UI ---------------------


def render():
    """
    Render the Gradio UI for the API Builder and Data Previewer.
    """
    theme = themes.Soft(primary_hue="blue", secondary_hue="slate").set(
        body_background_fill_dark="#000000"
    )

    examples = [
        """I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. 
                        The API name should be get_products_count. 
                        The API is of type TABLE and uses the backend resource production.products. """,
        """I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. 
                    The API name should be get_products_count_custom. 
                    The API is of type CUSTOMSQL and uses the SQL below 
                    SELECT category_id, count(1) num_products FROM production.products group by category_id """,
        """I want to build an API called ai_driven_api_001 which connects to the backend resource production.products in the datasource demo_ds_001 
                    and store it under application demo_app_001 in organization demo_org_001. """,
    ]

    with gr.Blocks(
        theme=theme,
        title="Abstracta AI-Driven API Builder",
    ) as demo:
        with gr.Tab("🚀 API Builder"):
            gr.Markdown(
                "## Abstracta AI-Driven API Builder\nDescribe your API requirements and let AI do the rest!"
            )

            with gr.Row():
                with gr.Column(scale=1):
                    requirements = gr.TextArea(
                        placeholder="E.g. Build an API in org demo_org_001...",
                        lines=4,
                        label="Describe your API",
                    )

                    with gr.Row():
                        for idx, ex in enumerate(examples):
                            # Use partial application so we can pass args to an async generator
                            def make_handler(text):
                                async def handler():
                                    async for val in typewriter_effect(text):
                                        yield val

                                return handler

                            gr.Button(f"💡 Example#{idx+1}", variant="secondary").click(
                                fn=make_handler(ex), inputs=[], outputs=requirements
                            )

                    submitBtn = gr.Button(
                        "⚡ Build API", variant="primary", interactive=False
                    )
                    status_message = gr.HTML(label="Progress")
                    api_url = gr.Markdown("", elem_classes="output-card")
                    web_url = gr.Markdown("", elem_classes="output-card")

                with gr.Column(scale=3):
                    with gr.Row():
                        btn_df = gr.Button("📊 DataFrame", size="sm", variant="primary")
                        btn_json = gr.Button("📝 JSON", size="sm", variant="secondary")
                    json_view = gr.JSON(value=[], visible=False)
                    dataframe_view = gr.Dataframe(value=None, show_search="filter", visible=False)

                    def toggle_view(view_type):
                        """Toggle between DataFrame and JSON view with highlighted button."""
                        if view_type == "DataFrame":
                            return (
                                gr.update(visible=True),  # dataframe visible
                                gr.update(visible=False),  # json hidden
                                gr.update(
                                    variant="primary"
                                ),  # dataframe button highlighted
                                gr.update(variant="secondary"),  # json button normal
                            )
                        else:
                            return (
                                gr.update(visible=False),
                                gr.update(visible=True),
                                gr.update(variant="secondary"),
                                gr.update(variant="primary"),
                            )

                    btn_df.click(
                        lambda: toggle_view("DataFrame"),
                        None,
                        [dataframe_view, json_view, btn_df, btn_json],
                    )
                    btn_json.click(
                        lambda: toggle_view("JSON"),
                        None,
                        [dataframe_view, json_view, btn_df, btn_json],
                    )

            submitBtn.click(
                gatherInfo,
                inputs=[requirements],
                outputs=[status_message, api_url, web_url, json_view, dataframe_view],
            )
            requirements.change(
                fn=requirements_on_change, outputs=[submitBtn], inputs=[requirements]
            )

        with gr.Tab("📂 Data Previewer"):
            gr.Markdown("### Browse and Preview Your Abstracta Data")

            with gr.Row():
                with gr.Column(scale=1):
                    orgDropDown = gr.Dropdown(
                        label="Organization", choices=get_organizations()
                    )
                    appDropDown = gr.Dropdown(label="Application")
                    datasourceDropDown = gr.Dropdown(label="Datasource")
                    service_selector = gr.Radio(
                        label="Available Services",
                        elem_classes="radio-item",
                        visible=False,
                    )

                with gr.Column(scale=2):
                    abstractaWebHyperLink = gr.Markdown("")
                    dataFrame = gr.DataFrame(
                        value=[], show_search="filter", label="Preview"
                    )

            orgDropDown.change(get_applications, [orgDropDown], [appDropDown])
            appDropDown.change(
                get_data_sources, [orgDropDown, appDropDown], [datasourceDropDown]
            )
            datasourceDropDown.change(
                lambda o, a, d: gr.update(
                    choices=[
                        f"{s['dtbl_table_name']}/{s['dtbl_version']}"
                        for s in get_services(o, a, d)
                    ],
                    visible=True,
                ),
                [orgDropDown, appDropDown, datasourceDropDown],
                [service_selector],
            )
            service_selector.change(
                lambda s, o, a, d: get_data(o, a, d, s.split("/")[0], s.split("/")[1]),
                [service_selector, orgDropDown, appDropDown, datasourceDropDown],
                [abstractaWebHyperLink, dataFrame],
            )

    demo.launch()


if __name__ == "__main__":
    load_dotenv(override=True)
    render()
