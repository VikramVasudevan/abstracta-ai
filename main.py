from abstracta_client import AbstractaClient


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

if __name__ == "__main__":
    main()
