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
                    access_token, org_name, app_name, datasource_name, service_name, service_version
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
        choices=AbstractaClient().get_applications(AbstractaClient().perform_auth(), org_name),
        value=None,
    )


def get_data_sources(org_name, app_name):
    """Return available datasources for a given organization and application."""
    return gr.update(
        choices=AbstractaClient().get_data_sources(AbstractaClient().perform_auth(), org_name, app_name),
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
    steps = [
        "Generating API based on your requirements",
        "Constructing API Builder Payload",
        "Authenticating to Abstracta API",
        "Creating API",
        "Granting service access",
        "Generating API URLs",
        "Fetching data from API",
        "Finalizing results"
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

    # Step 0
    yield build_progress(0, True), "", "", [], []

    with trace("abstracta-builder-agent"):
        payload_result = await Runner.run(apiBuilderAgent, requirements)

    # Step 1
    yield build_progress(2, True), "", "", [], []
    access_token = AbstractaClient().perform_auth()

    # Step 2
    yield build_progress(3, True), "", "", [], []
    payload = payload_result.final_output
    apiCreationResponse = AbstractaClient().create_api(access_token, payload)
    logging.info("API created successfully.")

    # Step 3
    yield build_progress(4, True), "", "", [], []
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

    # Step 4
    yield build_progress(5, True), "", "", [], []
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

    # Step 5
    yield build_progress(6, True), new_api_url, new_web_url, [], []
    data = AbstractaClient().get_data(
        access_token,
        payload.orgName,
        payload.appName,
        payload.datasourceName,
        payload.serviceName,
        newServiceVersion,
    )

    # Step 6 (final results)
    yield build_progress(7, True), new_api_url, new_web_url, data, pandas.DataFrame(data)
    logging.info("Process completed successfully.")

    # ✅ Step 7 - mark all done (progress bar 100% and all green)
    yield build_progress(total_steps), new_api_url, new_web_url, data, pandas.DataFrame(data)

# --------------------- RENDER UI ---------------------

def render():
    """
    Render the Gradio UI for the API Builder and Data Previewer.
    """
    theme = themes.Soft(primary_hue="blue", secondary_hue="slate")

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

    with gr.Blocks(theme=theme, title="Abstracta AI-Driven API Builder") as demo:
        with gr.Tab("🚀 API Builder"):
            gr.Markdown("## Abstracta AI-Driven API Builder\nDescribe your API requirements and let AI do the rest!")

            with gr.Row():
                with gr.Column(scale=1):
                    requirements = gr.TextArea(
                        placeholder="E.g. Build an API in org demo_org_001...",
                        lines=4,
                        label="Describe your API",
                    )

                    with gr.Row():
                        for ex in examples:
                            gr.Button("💡 Example", variant="secondary").click(
                                lambda e=ex: e, outputs=requirements
                            )

                    submitBtn = gr.Button("⚡ Build API", variant="primary", interactive=False)

                with gr.Column(scale=1):
                    status_message = gr.HTML(label="Progress")
                    api_url = gr.Markdown("", elem_classes="output-card")
                    web_url = gr.Markdown("", elem_classes="output-card")

                    with gr.Accordion("📦 API Response (JSON)", open=False):
                        api_response = gr.JSON(value=[])
                    with gr.Accordion("📊 Data Preview", open=False):
                        data_response = gr.Dataframe(value=[], show_search="filter")

            submitBtn.click(
                gatherInfo,
                inputs=[requirements],
                outputs=[status_message, api_url, web_url, api_response, data_response]
            )
            requirements.change(
                fn=requirements_on_change,
                outputs=[submitBtn],
                inputs=[requirements]
            )

        with gr.Tab("📂 Data Previewer"):
            gr.Markdown("### Browse and Preview Your Abstracta Data")

            with gr.Row():
                with gr.Column(scale=1):
                    orgDropDown = gr.Dropdown(label="Organization", choices=get_organizations())
                    appDropDown = gr.Dropdown(label="Application")
                    datasourceDropDown = gr.Dropdown(label="Datasource")
                    service_selector = gr.Radio(label="Available Services", elem_classes="radio-item", visible=False)

                with gr.Column(scale=2):
                    abstractaWebHyperLink = gr.Markdown("")
                    dataFrame = gr.DataFrame(value=[], show_search="filter", label="Preview")

            orgDropDown.change(get_applications, [orgDropDown], [appDropDown])
            appDropDown.change(get_data_sources, [orgDropDown, appDropDown], [datasourceDropDown])
            datasourceDropDown.change(
                lambda o, a, d: gr.update(
                    choices=[f"{s['dtbl_table_name']}/{s['dtbl_version']}" for s in get_services(o, a, d)],
                    visible=True
                ),
                [orgDropDown, appDropDown, datasourceDropDown],
                [service_selector]
            )
            service_selector.change(
                lambda s, o, a, d: get_data(o, a, d, s.split("/")[0], s.split("/")[1]),
                [service_selector, orgDropDown, appDropDown, datasourceDropDown],
                [abstractaWebHyperLink, dataFrame]
            )

    demo.launch()


if __name__ == "__main__":
    load_dotenv(override=True)
    render()
