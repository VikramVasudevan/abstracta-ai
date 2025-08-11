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
import logging
import re
import pandas
import gradio as gr
import gradio.themes as themes
from dotenv import load_dotenv
from abstracta_client import AbstractaClient
from api_builder_ui_helper import buildAPI
from dq_rules_ui_helper import buildDataQualityRulesForExistingAPI
from examples import examples
from profile_ui_helper import createProfile


# --------------------- LOGGING CONFIG ---------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)


def refreshData(api_url_markdown):
    print("api_url = ", api_url_markdown)
    # Regex pattern to capture the URL part of a Markdown link
    # It looks for text inside parentheses () after a closing square bracket ]
    url_pattern = r"\]\((.*?)\)"

    match = re.search(url_pattern, api_url_markdown)

    if match:
        url = match.group(1)
        print(url)
        abstractaClient = AbstractaClient()
        data = abstractaClient.get_data_from_api_url(
            access_token=abstractaClient.perform_auth(), api_url=url
        )
        return [
            gr.update(value=pandas.DataFrame(data), visible=True),
            gr.update(value=data, visible=False),
        ]
    else:
        raise Exception("No API url defined!")


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


def requirements_on_change(requirements):
    """Enable or disable build button based on text area content."""
    return (
        gr.update(interactive=bool(requirements.strip())),
        gr.update(interactive=bool(requirements.strip())),
        gr.update(interactive=bool(requirements.strip())),
    )


# --------------------- RENDER UI ---------------------


def render():
    """
    Render the Gradio UI for the API Builder and Data Previewer.
    """
    theme = themes.Soft(primary_hue="blue", secondary_hue="slate").set(
        body_background_fill_dark="#000000"
    )

    with gr.Blocks(
        theme=theme,
        title="Abstracta AI-Driven API Builder",
    ) as demo:
        with gr.Tab("🚀 Abstracta™ API Builder"):
            gr.Markdown(
                "## Abstracta™ AI-Driven API Builder\nDescribe your API requirements and let AI do the rest!"
            )

            with gr.Row():
                with gr.Column(scale=1):
                    requirements = gr.TextArea(
                        placeholder="E.g. Build an API in org demo_org_001...",
                        lines=4,
                        label="Describe your requirement",
                    )

                    for idx, category in enumerate(examples):
                        # Use partial application so we can pass args to an async generator
                        def make_handler(text):
                            async def handler():
                                async for val in typewriter_effect(text):
                                    yield val

                            return handler

                        with gr.Accordion(label=category["category"], open=False):
                            with gr.Row():
                                for ex in category["examples"]:
                                    gr.Button(
                                        f"💡 {ex['name']}", variant="secondary"
                                    ).click(
                                        fn=make_handler(ex["description"]),
                                        inputs=[],
                                        outputs=requirements,
                                    )

                    with gr.Row():
                        buildAPIBtn = gr.Button(
                            "⚡ Build API", variant="primary", interactive=False
                        )
                        buildDqRulesBtn = gr.Button(
                            "📊 Build DQ", variant="primary", interactive=False
                        )
                        createProfileBtn = gr.Button(
                            "🛡️ Build Data Security Profile",
                            variant="primary",
                            interactive=False,
                        )

                with gr.Column(scale=3):
                    with gr.Row():
                        btn_df = gr.Button(
                            "📊 DataFrame View", size="sm", variant="primary", scale=0
                        )
                        btn_json = gr.Button(
                            "📝 JSON View", size="sm", variant="secondary", scale=0
                        )
                        # Spacer that expands to push markdowns right
                        gr.Column(scale=1)  # Empty label as spacer
                        api_url = gr.Markdown("", elem_classes="output-card")
                        web_url = gr.Markdown("", elem_classes="output-card")
                        btn_refresh = gr.Button(
                            "⟳ Refresh", size="sm", variant="primary", scale=0
                        )
                    with gr.Row(scale=0):
                        gr.Column(scale=1)
                        status_message = gr.HTML(label="Progress", visible=False)
                        gr.Column(scale=1)
                    json_view = gr.JSON(value=[], visible=False)
                    dataframe_view = gr.Dataframe(
                        value=None, show_search="filter", visible=False
                    )

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
                    btn_refresh.click(
                        refreshData, [api_url], [dataframe_view, json_view]
                    )

            buildAPIBtn.click(
                buildAPI,
                inputs=[requirements],
                outputs=[status_message, api_url, web_url, json_view, dataframe_view],
            )
            buildDqRulesBtn.click(
                buildDataQualityRulesForExistingAPI,
                inputs=[requirements],
                outputs=[status_message, api_url, web_url, json_view, dataframe_view],
            )
            createProfileBtn.click(
                createProfile,
                inputs=[requirements],
                outputs=[status_message, api_url, web_url, json_view, dataframe_view],
            )

            requirements.change(
                fn=requirements_on_change,
                outputs=[buildAPIBtn, buildDqRulesBtn, createProfileBtn],
                inputs=[requirements],
            )

        with gr.Tab("📂 Abstracta™ Data Previewer"):
            gr.Markdown("### Your Data, Ready to Explore")

            with gr.Row():
                with gr.Column(scale=1):
                    orgDropDown = gr.Dropdown(
                        label="Organization", choices=[""] + get_organizations()
                    )
                    appDropDown = gr.Dropdown(label="Application")
                    datasourceDropDown = gr.Dropdown(label="Datasource")
                    service_selector = gr.Radio(
                        label="Available Services",
                        elem_classes="radio-item",
                        visible=False,
                    )

                with gr.Column(scale=4):
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
