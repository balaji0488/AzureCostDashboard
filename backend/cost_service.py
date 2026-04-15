import datetime
import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryTimePeriod, QueryDataset, QueryAggregation, QueryGrouping
from sqlalchemy.orm import Session
from models import CostRecord, Subscription

logger = logging.getLogger(__name__)

def fetch_and_save_costs(db: Session, months_back: int = 6):
    """
    Fetches costs for the subscriptions accessible by the credential
    and saves/updates them in the database.
    """
    try:
        credential = DefaultAzureCredential()
        client = CostManagementClient(credential)
        
        # NOTE: For a real deployment, we need a list of subscriptions or a billing account scope.
        # It's better to fetch subscriptions first, but query API requires a scope.
        # Let's assume we fetch for the tenant/default subscription the Identity has access to.
        # Or better, we should fetch subscriptions the identity has access to.
        from azure.mgmt.subscription import SubscriptionClient
        sub_client = SubscriptionClient(credential)
        subscriptions = list(sub_client.subscriptions.list())
        
        # Save subscription names to DB
        for sub in subscriptions:
            existing = db.query(Subscription).filter(Subscription.subscription_id == sub.subscription_id).first()
            if existing:
                existing.display_name = sub.display_name
            else:
                db.add(Subscription(subscription_id=sub.subscription_id, display_name=sub.display_name))
        db.commit()
        
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=30 * months_back)

        for sub in subscriptions:
            scope = f"/subscriptions/{sub.subscription_id}"
            logger.info(f"Fetching costs for scope {scope} ({sub.display_name})")
            
            # Grouping by multiple dimensions allows us to build all 4 charts
            # 1. ResourceGroup
            # 2. ServiceName
            # 3. Location (ResourceLocation)
            # Date is also a grouping (BillingMonth/ChargeType etc, or just daily timegrain)
            
            # The API might complain if we group by too many things at once. We group by Date, RG, Service, Location.
            dataset = QueryDataset(
                granularity="Daily",
                aggregation={
                    "totalCost": QueryAggregation(name="PreTaxCost", function="Sum")
                },
                grouping=[
                    QueryGrouping(type="Dimension", name="ResourceGroupName"),
                    QueryGrouping(type="Dimension", name="ServiceName")
                ]
            )
            
            time_period = QueryTimePeriod(from_property=start_date, to=end_date)
            query_definition = QueryDefinition(
                type="Usage",
                timeframe="Custom",
                time_period=time_period,
                dataset=dataset
            )
            
            try:
                response = client.query.usage(scope, query_definition)
                
                col_index = {col.name: i for i, col in enumerate(response.columns)}
                
                # Delete existing date range for this subscription
                db.query(CostRecord).filter(
                    CostRecord.subscription_id == sub.subscription_id,
                    CostRecord.date >= start_date,
                    CostRecord.date <= end_date
                ).delete()
                
                for row in response.rows:
                    cost_val = row[col_index.get("PreTaxCost", 0)] if "PreTaxCost" in col_index else 0
                    
                    if "UsageDate" in col_index:
                        date_val = row[col_index["UsageDate"]]
                    elif "BillingMonth" in col_index:
                        date_val = row[col_index["BillingMonth"]]
                    else:
                        date_val = end_date
                        
                    if isinstance(date_val, int):
                        date_str = str(date_val)
                        date_obj = datetime.date(int(date_str[0:4]), int(date_str[4:6]), int(date_str[6:8]))
                    elif isinstance(date_val, str):
                        try:
                            date_obj = datetime.datetime.fromisoformat(date_val.replace('Z', '+00:00')).date()
                        except ValueError:
                            date_obj = datetime.datetime.strptime(str(date_val)[:10], "%Y-%m-%d").date()
                    else:
                        date_obj = end_date.date() if hasattr(end_date, 'date') else end_date

                    sub_id_val = sub.subscription_id
                    rg_val = row[col_index["ResourceGroupName"]] if "ResourceGroupName" in col_index else "Unknown"
                    service_val = row[col_index["ServiceName"]] if "ServiceName" in col_index else "Unknown"
                    loc_val = row[col_index["ResourceLocation"]] if "ResourceLocation" in col_index else "Global"
                    currency_val = row[col_index["Currency"]] if "Currency" in col_index else "USD"
                    
                    new_record = CostRecord(
                        date=date_obj,
                        subscription_id=sub_id_val,
                        resource_group=rg_val,
                        service_name=service_val,
                        location=loc_val,
                        pretax_cost=float(cost_val) if cost_val else 0.0,
                        currency=currency_val
                    )
                    db.add(new_record)
                
                db.commit()
                logger.info(f"Successfully processed {len(response.rows)} rows for scope {scope}")
            except Exception as e:
                logger.error(f"Error querying cost for scope {scope}: {e}")
                db.rollback()

    except Exception as e:
        logger.error(f"Failed to fetch costs: {e}")
