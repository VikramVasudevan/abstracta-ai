examples = [
    {
        "category": "Examples: Build API",
        "examples": [
            {
                "name": "API using direct datasource",
                "description": (
                    "I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001."
                    "The API name should be get_products_count."
                    "The API is of type TABLE and uses the backend resource production.products."
                ),
            },
            {
                "name": "API using custom SQL",
                "description": (
                    "I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. "
                    "The API name should be get_products_count_custom. "
                    "The API is of type CUSTOMSQL and uses the SQL below:\n"
                    "SELECT category_id, count(1) num_products FROM production.products group by category_id "
                ),
            },
            {
                "name": "API using direct datasource - simple",
                "description": (
                    "I want to build an API called ai_driven_api_001 which connects to the backend resource production.products in the datasource demo_ds_001"
                    "and store it under application demo_app_001 in organization demo_org_001. "
                ),
            },
            {
                "name": "API using customsql - 2",
                "description": (
                    "I want to build an API located in `demo_org_001` under the app `demo_app_001` for the datasource `demo_ds_001`. "
                    "The API name should be `get_sales_orders_for_ny`. "
                    "The API is of type `CUSTOMSQL` and uses the SQL below:\n"
                    """select orders.*, stores.store_name, stores.state, stores.city 
from [sales].[orders] inner join [sales].[stores] on (stores.store_id = orders.store_id) 
where stores.state = 'NY'"""
                ),
            },
            {
                "name": "API using customsql - 3",
                "description": (
                    "- I want to build an API located in `demo_org_001` under the app `demo_app_001` for the datasource `demo_ds_001`. \n"
                    "- You must name the API as `get_sales_orders_for_my_region`. \n"
                    "- Ensure data security filter must be set to:\n state in ( %(PROFILE:region)% ) \n"
                    "- The API is of type `CUSTOMSQL` and uses the SQL below:\n"
                    """select orders.*, stores.store_name, stores.state, stores.city 
from [sales].[orders] inner join [sales].[stores] on (stores.store_id = orders.store_id)"""
                ),
            },
            {
                "name": "API using customsql autogen",
                "description": (
                    "- I want to build an API located in `demo_org_001` under the app `demo_app_001` for the datasource `demo_ds_001`. \n"
                    "- You must name the API as `get_sales_orders_for_my_region`. \n"
                    "- The API is of type `CUSTOMSQL` created using the requirement as below:\n"
                    "Get me all [sales].[orders] along with the store name. Stores are available in [sales].[stores] table. do not add a semicolon at the end of the customsql."
                ),
            },
            {
                "name": "API using profile-driven data security",
                "description": (
                    "- I want to build an API located in `demo_org_001` under the app `demo_app_001` for the datasource `demo_ds_001`. \n"
                    "- You must name the API as `get_sales_orders_for_my_region`. \n"
                    "- set datasecurityfilter to state in ( %(PROFILE:region)% )"
                    "- The API is of type `CUSTOMSQL` created using the requirement as below:\n"
                    "Get me all [sales].[orders] along with the store name and state (field `state`) from the stores table. \n"
                    "Stores are available in [sales].[stores] table with primary key as `store_id`. \n"
                    "do not add a semicolon at the end of the customsql.\n"
                    "do not add the data security filter in the customsql.\n"
                ),
            },
        ],
    },
    {
        "category": "Examples: Data Quality Rules",
        "examples": [
            {
                "name": "Build DQ Rules - 1",
                "description": (
                    "For my API `demo_org_001/demo_app_001/demo_ds_001/salesorderitems/0.0.0`, "
                    "add a dq rule for the field `list_price` to ensure it  remains in range 300-500"
                ),
            },
        ],
    },
    {
        "category": "Examples: Build Data Security Profile",
        "examples": [
            {
                "name": "Build Data Security Profile",
                "description": (
                    "In my org demo_org_001, I want to create a profile with key region and value Asia. \n"
                    "Assign this profile to the following users: vikram.vasudevan@ekahaa.com, test_user@ekahaa.com"
                ),
            },
        ],
    },
]
