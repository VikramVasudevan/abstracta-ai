from dotenv import load_dotenv
from abstracta_client import AbstractaClient, ABSTRACTA_API_URL
from api_builder_agent import apiBuilderAgent, APIBuilderPayload
from agents import Runner, trace
import gradio as gr
import json

def main():
    print("Hello from abstracta-ai!")

    access_token = AbstractaClient().perform_auth()
    print(access_token)
    # use this access token to make a request to the abstracta api
    organizations = AbstractaClient().get_organizations(access_token)
    print(organizations)
    if(len(organizations) > 0):
        applications = AbstractaClient().get_applications(access_token, organizations[0])
        print(applications)
        if(len(applications) > 0):
            data_sources = AbstractaClient().get_data_sources(access_token, organizations[0], applications[0])
            print(data_sources)
        else:
            print("No applications found")
    else:
        print("No organizations found")

async def gatherInfo(requirements):
    print(requirements)
    with trace("abstracta-builder-agent"):
        payload_result = await Runner.run(apiBuilderAgent, requirements)
    access_token = AbstractaClient().perform_auth()
    payload =  payload_result.final_output
    print(payload)
    # if("sampleParameterValues" not in payload):
    #     payload["sampleParameterValues"] = {}
    apiCreationResponse = AbstractaClient().create_api(access_token, payload)
    print(apiCreationResponse)
    new_api_url = AbstractaClient().generate_api_url(payload.orgName, payload.appName, payload.datasourceName, payload.serviceName, apiCreationResponse["service-info"]["tables"][0]["dtbl_version"])
    new_web_url = AbstractaClient().generate_web_url(payload.orgName, payload.appName, payload.datasourceName, payload.serviceName, apiCreationResponse["service-info"]["tables"][0]["dtbl_version"])
    data = AbstractaClient().get_data(access_token, payload.orgName, payload.appName, payload.datasourceName, payload.serviceName, apiCreationResponse["service-info"]["tables"][0]["dtbl_version"])
    print(data)
    return new_api_url, new_web_url, data

def render():
    with gr.Blocks() as demo:
        gr.Markdown("# Abstracta AI-Driven API Builder")
        with gr.Row(equal_height=True): 
            with gr.Column():
                requirements = gr.TextArea(label="Your requirements", placeholder="Enter your requirements here", 
                value="""I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. 
                The API name should be get_products_count. 
                The API is of type TABLE and uses the backend resource production.products. """)
            with gr.Column():
                api_url = gr.Markdown(label="API URL")
                web_url = gr.Markdown(label="Web URL")
                api_response = gr.JSON(label="API Response", value=[])

        submitBtn = gr.Button("Generate API", scale=0, variant="primary")
        submitBtn.click(gatherInfo, inputs=[requirements], outputs=[api_url, web_url, api_response])
    demo.launch()

if __name__ == "__main__":
    load_dotenv(override=True)
    render()
