from dotenv import load_dotenv
from abstracta_client import AbstractaClient, ABSTRACTA_API_URL
from api_builder_agent import apiBuilderAgent, APIBuilderPayload
from agents import Runner, trace
import gradio as gr
import os
import gradio.themes as themes


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
    yield "Generating API based on your requirements ... this may take a while", "", "", []
    print(requirements)
    with trace("abstracta-builder-agent"):
        payload_result = await Runner.run(apiBuilderAgent, requirements)
    yield "Constructed API Builder Payload successfully. Authenticating to Abstracta API ...", "", "", []
    access_token = AbstractaClient().perform_auth()
    yield "Authenticated to Abstracta API successfully. Creating API ...", "", "", []
    payload = payload_result.final_output
    print(payload)
    # if("sampleParameterValues" not in payload):
    #     payload["sampleParameterValues"] = {}
    apiCreationResponse = AbstractaClient().create_api(access_token, payload)
    yield "API created successfully. Granting service access ...", "", "", []
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
    yield "Service access granted successfully. Generating API URLs ...", "", "", []
    new_api_url = format_url_as_markdown("API URL", AbstractaClient().generate_api_url(
        payload.orgName,
        payload.appName,
        payload.datasourceName,
        payload.serviceName,
        newServiceVersion,
    ))
    new_web_url = format_url_as_markdown("Web URL", AbstractaClient().generate_web_url(
        payload.orgName,
        payload.appName,
        payload.datasourceName,
        payload.serviceName,
        newServiceVersion,
    ))
    yield "API URLs generated successfully. Fetching data from API ...", new_api_url, new_web_url, []
    data = AbstractaClient().get_data(
        access_token,
        payload.orgName,
        payload.appName,
        payload.datasourceName,
        payload.serviceName,
        newServiceVersion,
    )
    print(data)
    yield "Data fetched successfully. Returning results ...", new_api_url, new_web_url, data
    return


def render():
    with gr.Blocks(
        title="Abstracta AI-Driven API Builder",
        theme=themes.Default(primary_hue="blue"),
    ) as demo:
        gr.Markdown("# Abstracta AI-Driven API Builder")
        with gr.Row(equal_height=True):
            with gr.Column():
                requirements = gr.TextArea(
                    label="Your requirements",
                    placeholder="I want to build an API ... explain your requirements here",
                    value="""""",
                )

                example1 = gr.Text(label="Example-1", value="""
                I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. 
                The API name should be get_products_count. 
                The API is of type TABLE and uses the backend resource production.products. """)

                example2 = gr.Text(label="Example-2", value="""
                I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. 
                The API name should be get_products_count_custom. 
                The API is of type CUSTOMSQL and uses the SQL below 
                SELECT category_id, count(1) num_products FROM production.products group by category_id """)
            with gr.Column():
                status_message = gr.Text(label="Status Message")
                api_url = gr.Markdown(label="API URL")
                web_url = gr.Markdown(label="Web URL")
                api_response = gr.JSON(label="API Response", value=[])

        submitBtn = gr.Button("Generate API", scale=0, variant="primary")
        submitBtn.click(
            gatherInfo,
            inputs=[requirements],
            outputs=[status_message, api_url, web_url, api_response],
        )
    demo.launch()


if __name__ == "__main__":
    load_dotenv(override=True)
    render()
