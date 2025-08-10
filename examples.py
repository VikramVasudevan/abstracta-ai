examples = [
    (
        "I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001."
        "The API name should be get_products_count."
        "The API is of type TABLE and uses the backend resource production.products."
    ),
    (
        "I want to build an API located in demo_org_001 under the app demo_app_001 for the datasource demo_ds_001. "
        "The API name should be get_products_count_custom. "
        "The API is of type CUSTOMSQL and uses the SQL below:\n"
        "SELECT category_id, count(1) num_products FROM production.products group by category_id "
    ),
    (
        "I want to build an API called ai_driven_api_001 which connects to the backend resource production.products in the datasource demo_ds_001"
        "and store it under application demo_app_001 in organization demo_org_001. "
    ),
    (
        "For my API `demo_org_001/demo_app_001/demo_ds_001/salesorderitems/0.0.0`, "
        "add a dq rule for the field `list_price` to ensure it  remains in range 300-500"
    ),
    (
        "In my org demo_org_001, I want to create a profile with key region and value Asia. Assign this profile to the following users: vikram.vasudevan@ekahaa.com, test_user@ekahaa.com"
    ),
    (
        """
select orders.*, stores.store_name, stores.state, stores.city 
from [sales].[orders] inner join [sales].[stores] on (stores.store_id = orders.store_id) 
where stores.state = 'NY'"""
    ),
]
