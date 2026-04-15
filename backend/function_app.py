import azure.functions as func
import logging
import json
from sqlalchemy import func as sqlalchemy_func
from database import init_db, get_db
from models import CostRecord, Subscription
import cost_service

app = func.FunctionApp()

# Initialize DB on startup
init_db()

@app.timer_trigger(schedule="0 0 1 * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False) 
def sync_costs_timer(myTimer: func.TimerRequest) -> None:
    """
    Runs every day at 1 AM. Fetches costs for the last 6 months.
    """
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Executing sync_costs_timer...')
    db_gen = get_db()
    db = next(db_gen)
    try:
        cost_service.fetch_and_save_costs(db, months_back=6)
    finally:
        db.close()
    
    logging.info('sync_costs_timer finished execution.')

@app.route(route="costs", auth_level=func.AuthLevel.ANONYMOUS)
def get_dashboard_costs(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint to get data for the dashboard.
    Accepts query parameters:
    - subscriptionId (optional)
    """
    logging.info('Processing get_dashboard_costs request.')

    # Phase 3: Token validation stub
    auth_header = req.headers.get("Authorization")
    user_email = "Unknown/Anonymous User"
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        logging.info("Received Bearer token. (Verification logic to be implemented)")
        
        # In a real scenario, you would decode the JWT here using a library like PyJWT,
        # verifying it against the Entra ID JWKS endpoint.
        # e.g., jwt.decode(token, algorithms=["RS256"], options={"verify_signature": False})
        # user_email = decoded_token.get("upn", decoded_token.get("preferred_username", ""))
        
        user_email = "authenticated_user@example.com" # Stub
    else:
        logging.warning("No Authorization Bearer token provided.")
        # If strict auth is required, we should return 401 Unauthorized:
        # return func.HttpResponse("Unauthorized", status_code=401)
        
    # TODO: Once verified, query Azure ARM or Resource Graph:
    # "List subscriptions the user has read access to"
    # For now, we will just return everything in DB (or filter by query param as before)
    
    subscription_id = req.params.get('subscriptionId')
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        query = db.query(CostRecord)
        if subscription_id:
            query = query.filter(CostRecord.subscription_id == subscription_id)
            
        data = query.all()
        
        # Aggregate data for 4 charts
        monthly_costs = {}
        service_costs = {}
        rg_costs = {}
        location_costs = {}
        currency = "USD"
        
        for record in data:
            # 1. Monthly aggregation (YYYY-MM)
            month_key = record.date.strftime("%Y-%m") if hasattr(record.date, 'strftime') else str(record.date)[:7]
            monthly_costs[month_key] = monthly_costs.get(month_key, 0) + record.pretax_cost
            
            # 2. Service costs
            svc = record.service_name or "Unknown"
            service_costs[svc] = service_costs.get(svc, 0) + record.pretax_cost
            
            # 3. Resource Group costs (treat empty as "Unassigned")
            rg = record.resource_group.strip() if record.resource_group else ""
            rg = rg if rg else "Unassigned"
            rg_costs[rg] = rg_costs.get(rg, 0) + record.pretax_cost
            
            # 4. Location costs
            loc = record.location or "Unknown"
            location_costs[loc] = location_costs.get(loc, 0) + record.pretax_cost
            
            # Capture currency from any record
            if record.currency:
                currency = record.currency

        # Top 5 services, rest grouped as "Others"
        sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
        top_services = sorted_services[:5]
        others_cost = sum(v for _, v in sorted_services[5:])
        service_list = [{"service": k, "cost": round(v, 2)} for k, v in top_services]
        if others_cost > 0:
            service_list.append({"service": "Others", "cost": round(others_cost, 2)})

        # Top 5 resource groups
        sorted_rgs = sorted(rg_costs.items(), key=lambda x: x[1], reverse=True)
        top_rgs = sorted_rgs[:5]
        rg_others_cost = sum(v for _, v in sorted_rgs[5:])
        rg_list = [{"resourceGroup": k, "cost": round(v, 2)} for k, v in top_rgs]
        if rg_others_cost > 0:
            rg_list.append({"resourceGroup": "Others", "cost": round(rg_others_cost, 2)})

        response_data = {
            "currency": currency,
            "monthly": [{"month": k, "cost": round(v, 2)} for k, v in sorted(monthly_costs.items())],
            "service": service_list,
            "resourceGroup": rg_list,
            "location": [{"location": k, "cost": round(v, 2)} for k, v in sorted(location_costs.items(), key=lambda x: x[1], reverse=True)[:5]]
        }
        
        return func.HttpResponse(
            body=json.dumps(response_data),
            mimetype="application/json",
            status_code=200
        )

    finally:
        db.close()

@app.route(route="subscriptions", auth_level=func.AuthLevel.ANONYMOUS)
def get_subscriptions(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint to get the list of unique subscriptions available in the local DB.
    """
    logging.info('Processing get_subscriptions request.')
    db_gen = get_db()
    db = next(db_gen)
    try:
        subs = db.query(Subscription).all()
        sub_list = [{"id": s.subscription_id, "name": s.display_name or s.subscription_id} for s in subs]
        
        return func.HttpResponse(
            body=json.dumps(sub_list),
            mimetype="application/json",
            status_code=200
        )
    finally:
        db.close()
