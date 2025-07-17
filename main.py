from dotenv import load_dotenv
from gradio.components import component
from abstracta_client import AbstractaClient, ABSTRACTA_API_URL
from api_builder_agent import apiBuilderAgent, APIBuilderPayload
from agents import Runner, trace
import gradio as gr
import os
import gradio.themes as themes
import pandas


def get_data(org_name, app_name, datasource_name, service_name, service_version):
    print(
        f"Getting data from {org_name}, {app_name}, {datasource_name}, {service_name}, {service_version}"
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
    access_token = AbstractaClient().perform_auth()
    return AbstractaClient().get_all_services(access_token)


def get_services(org_name, app_name, datasource_name):
    access_token = AbstractaClient().perform_auth()
    return AbstractaClient().get_services(
        access_token, org_name, app_name, datasource_name
    )


def get_organizations():
    access_token = AbstractaClient().perform_auth()
    return AbstractaClient().get_organizations(access_token)


def get_applications(org_name):
    access_token = AbstractaClient().perform_auth()
    return gr.update(
        choices=AbstractaClient().get_applications(access_token, org_name), value=None
    )


def get_data_sources(org_name, app_name):
    access_token = AbstractaClient().perform_auth()
    return gr.update(
        choices=AbstractaClient().get_data_sources(access_token, org_name, app_name),
        value=None,
    )


def main():
    print("Hello from abstracta-ai!")

    access_token = AbstractaClient().perform_auth()
    print(access_token)
    # use this access token to make a request to the abstracta api
    organizations = AbstractaClient().get_organizations(access_token)
    print(organizations)
    if len(organizations) > 0:
        applications = AbstractaClient().get_applications(
            access_token, organizations[0]
        )
        print(applications)
        if len(applications) > 0:
            data_sources = AbstractaClient().get_data_sources(
                access_token, organizations[0], applications[0]
            )
            print(data_sources)
        else:
            print("No applications found")
    else:
        print("No organizations found")


def format_url_as_markdown(label, url):
    return f"""
    ### Wanna access the {label}?
    [Click here for {label}]({url})"""


async def gatherInfo(requirements):
    yield "Generating API based on your requirements ... this may take a while", "", "", [], []
    print(requirements)
    with trace("abstracta-builder-agent"):
        payload_result = await Runner.run(apiBuilderAgent, requirements)
    yield "Constructed API Builder Payload successfully. Authenticating to Abstracta API ...", "", "", [], []
    access_token = AbstractaClient().perform_auth()
    yield "Authenticated to Abstracta API successfully. Creating API ...", "", "", [], []
    payload = payload_result.final_output
    print(payload)
    # if("sampleParameterValues" not in payload):
    #     payload["sampleParameterValues"] = {}
    apiCreationResponse = AbstractaClient().create_api(access_token, payload)
    yield "API created successfully. Granting service access ...", "", "", [], []
    print(apiCreationResponse)
    newServiceVersion = apiCreationResponse["service-info"]["tables"][0]["dtbl_version"]
    serviceAccessResponse = AbstractaClient().grant_service_access(
        access_token,
        payload.orgName,
        payload.appName,
        payload.datasourceName,
        payload.serviceName,
        newServiceVersion,
        [os.getenv("ABSTRACTA_FOR_USER") or ""],
        ["VIEWER", "EDITOR", "CREATOR"],
    )
    print(serviceAccessResponse)
    yield "Service access granted successfully. Generating API URLs ...", "", "", [], []
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
    yield "API URLs generated successfully. Fetching data from API ...", new_api_url, new_web_url, [], []
    data = AbstractaClient().get_data(
        access_token,
        payload.orgName,
        payload.appName,
        payload.datasourceName,
        payload.serviceName,
        newServiceVersion,
    )
    print(data)
    yield "Data fetched successfully. Returning results ...", new_api_url, new_web_url, data, pandas.DataFrame(
        data
    )
    return


def requirements_on_change(requirements):
    return gr.update(interactive=bool(requirements.strip()))


def render():
    with gr.Blocks(
        css="""
/* Hide default radio circle */
input[type="radio"] {
    display: none;
}

/* Style all radio labels */
.radio-item label {
    padding: 10px;
    border-radius: 6px;
    cursor: pointer;
    display: block;
    margin-bottom: 4px;
    border: 1px solid #ccc;
    transition: background 0.2s, border-color 0.2s;
}

/* Gradio adds .selected to the label of selected radio */
.radio-item label.selected {
    background-color: #d0ebff;
    border-color: #339af0;
    font-weight: bold;
    color: #084298;
}
""",
        title="Abstracta AI-Driven API Builder",
        theme=themes.Default(primary_hue="blue"),
    ) as demo:
        with gr.Tab("API Builder"):
            gr.Markdown("# Abstracta AI-Driven API Builder")
            with gr.Row(equal_height=True):
                with gr.Column():
                    requirements = gr.TextArea(
                        placeholder="I want to build an API ... explain your requirements here",
                        value="""""",
                        show_label=False,
                        lines=3,
                    )

                    submitBtn = gr.Button(
                        "Build API", scale=0, variant="primary", interactive=False
                    )

                    with gr.Row():
                        example1 = gr.Text(
                            label="Example 1",
                            info="For instance you could ask me ...",
                            value="""I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. 
                        The API name should be get_products_count. 
                        The API is of type TABLE and uses the backend resource production.products. """,
                            lines=3,
                            show_copy_button=True,
                        )

                    with gr.Row():
                        example2 = gr.Text(
                            label="Example 2",
                            info="or this ...",
                            value="""I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. 
                    The API name should be get_products_count_custom. 
                    The API is of type CUSTOMSQL and uses the SQL below 
                    SELECT category_id, count(1) num_products FROM production.products group by category_id """,
                            lines=3,
                            show_copy_button=True,
                        )

                    with gr.Row():
                        example3 = gr.Text(
                            label="Example 3",
                            info="or quite simply, this ...",
                            value="""I want to build an API called ai_driven_api_001 which connects to the backend resource production.products in the datasource demo_ds_001 
                    and store it under application demo_app_001 in organization demo_org_001. """,
                            lines=3,
                            show_copy_button=True,
                        )

                with gr.Column():
                    status_message = gr.Text(label="Status", scale=0)
                    api_url = gr.Markdown(
                        label="API URL",
                        value="### Generated API URL",
                        show_copy_button=True,
                    )
                    web_url = gr.Markdown(
                        label="Web URL",
                        value="### Generated Web URL",
                        show_copy_button=True,
                    )
                    with gr.Tab("JSON"):
                        api_response = gr.JSON(label="API Response", value=[])
                    with gr.Tab("Data"):
                        data_response = gr.Dataframe(
                            label="Data Response", value=[], show_search="filter"
                        )

            submitBtn.click(
                gatherInfo,
                inputs=[requirements],
                outputs=[status_message, api_url, web_url, api_response, data_response],
            )

            # Enable button only when there is input
            requirements.change(
                fn=requirements_on_change,
                outputs=[submitBtn],
                inputs=[requirements],
            )
        with gr.Tab("Data Previewer"):
            gr.Markdown("# Data Previewer")
            abstractaWebHyperLink = gr.Markdown("")
            dataFrame = gr.DataFrame(
                value=[], show_search="filter", label="None selected"
            )
            with gr.Sidebar():
                gr.Markdown("## APIs")
                organizations = get_organizations()
                orgDropDown = gr.Dropdown(
                    label="Organization", choices=organizations, value=None
                )
                appDropDown = gr.Dropdown(label="Application", choices=[], value="")
                datasourceDropDown = gr.Dropdown(
                    label="Datasource", choices=[], value=""
                )
                orgDropDown.change(
                    fn=get_applications,
                    outputs=[appDropDown],
                    inputs=[orgDropDown],
                )
                appDropDown.change(
                    fn=get_data_sources,
                    outputs=[datasourceDropDown],
                    inputs=[orgDropDown, appDropDown],
                )

                def on_datasource_change(org_name, app_name, datasource_name):
                    services = get_services(org_name, app_name, datasource_name)
                    return gr.update(
                        choices=[
                            f"{service['dtbl_table_name']}/{service['dtbl_version']}"
                            for service in services
                        ],
                        visible=True if services else False,
                    )

                service_selector = gr.Radio(
                    label="Available Services",
                    choices=[],
                    visible=False,
                    elem_classes="radio-item",
                )
                datasourceDropDown.change(
                    fn=on_datasource_change,
                    inputs=[orgDropDown, appDropDown, datasourceDropDown],
                    outputs=[service_selector],
                )

                service_selector.change(
                    fn=lambda service_with_version, org_name, app_name, datasource_name: get_data(
                        org_name,
                        app_name,
                        datasource_name,
                        service_with_version.split("/")[0],
                        service_with_version.split("/")[1],
                    ),
                    inputs=[
                        service_selector,
                        orgDropDown,
                        appDropDown,
                        datasourceDropDown,
                    ],
                    outputs=[abstractaWebHyperLink, dataFrame],
                )

                # all_services = get_all_services()
                # for service in all_services:
                #     org_name = service["org_name"]
                #     app_name = service["app_name"]
                #     datasource_name = service["dqdb_db_name"]
                #     service_name = service["dtbl_table_name"]
                #     service_version = service["dtbl_version"]
                #     api_url = AbstractaClient().generate_api_url(
                #         org_name,
                #         app_name,
                #         datasource_name,
                #         service_name,
                #         service_version,
                #     )
                #     button = gr.Button(
                #         value=f"{service_name}_{service_version}",
                #         scale=0,
                #         variant="primary",
                #     )
                #     button.click(
                #         lambda o=org_name, a=app_name, d=datasource_name, s=service_name, v=service_version: get_data(
                #             o, a, d, s, v
                #         ),
                #         inputs=[],
                #         outputs=[abstractaWebHyperLink, dataFrame],
                #     )

    demo.launch()


if __name__ == "__main__":
    load_dotenv(override=True)
    render()
