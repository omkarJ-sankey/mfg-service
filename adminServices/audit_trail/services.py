from django.utils import timezone
from sharedServices.common import json_load, safe_json_load
from sharedServices.constants import YES
from sharedServices.model_files.audit_models import AuditTrail


def get_audit_trail_list(validated_data):
    """
    Fetch and filter AuditTrail data based on validated query params.
    Handles optional filters and pagination internally.
    """
    user_role = validated_data.get("user_role")
    reviewed = validated_data.get("reviewed")
    action = validated_data.get("action")
    module = validated_data.get("module")
    start_date = validated_data.get("start_date")
    end_date = validated_data.get("end_date")
    order_by_id = validated_data.get("order_by_id")
    order_by_date = validated_data.get("order_by_date")

    audit_records = AuditTrail.objects.all()

    if user_role and user_role != "All":
        audit_records = audit_records.filter(user_role__icontains=user_role)
    if reviewed and reviewed != "All":
        audit_records = audit_records.filter(review_status__iexact=reviewed)
    if module and module != "All":
        audit_records = audit_records.filter(module__iexact=module)
    if action and action != "All":
        audit_records = audit_records.filter(action__icontains=action)
    if start_date and end_date:
        audit_records = audit_records.filter(created_date__range=[start_date, end_date])

    if order_by_id:
        if order_by_id == "Ascending":
            audit_records = audit_records.order_by("id")
        elif order_by_id == "Descending":
            audit_records = audit_records.order_by("-id")

    elif order_by_date:
        if order_by_date == "Ascending":
            audit_records = audit_records.order_by("created_date")
        elif order_by_date == "Descending":
            audit_records = audit_records.order_by("-created_date")

    else:
        
        audit_records = audit_records.order_by("created_date")


    return audit_records

def get_offers_details(new_data, old_data):
    """Return offer audit trail details"""

    loyalty_products_new = new_data.get("loyalty_products", [])
    loyalty_products_old = old_data.get("loyalty_products", [])
    loyalty_products_resp = []

    for idx in range(max(len(loyalty_products_new), len(loyalty_products_old))):
        new_p = loyalty_products_new[idx] if idx < len(loyalty_products_new) else {}
        old_p = loyalty_products_old[idx] if idx < len(loyalty_products_old) else {}
        loyalty_products_resp.append({
            "id": new_p.get("id") or old_p.get("id"),
            "product_plu_new": new_p.get("Product PLU"),
            "product_code_new": new_p.get("Product code"),
            "product_new": new_p.get("Product"),
            "price_new": new_p.get("Price"),
            "price_after_promotion_new": new_p.get("Price After Promotion"),
            "status_new": new_p.get("Status"),
            "product_plu_old": old_p.get("Product PLU"),
            "product_code_old": old_p.get("Product code"),
            "product_old": old_p.get("Product"),
            "price_old": old_p.get("Price"),
            "price_after_promotion_old": old_p.get("Price After Promotion"),
            "status_old": old_p.get("Status"),
        })

    occurrences_new = new_data.get("loyalty_occurrences", [])
    occurrences_old = old_data.get("loyalty_occurrences", [])
    loyalty_occurrences_resp = []

    for idx in range(max(len(occurrences_new), len(occurrences_old))):
        new_o = occurrences_new[idx] if idx < len(occurrences_new) else {}
        old_o = occurrences_old[idx] if idx < len(occurrences_old) else {}
        loyalty_occurrences_resp.append({
            "id": new_o.get("id") or old_o.get("id"),
            "start_time_new": new_o.get("Start Time"),
            "end_time_new": new_o.get("End Time"),
            "date_new": new_o.get("Date"),
            "start_time_old": old_o.get("Start Time"),
            "end_time_old": old_o.get("End Time"),
            "date_old": old_o.get("Date"),
        })

    def map_main_data(data):
        return {
            "category": data.get("Category"),
            "loyalty_title": data.get("Loyalty Title"),
            "loyalty_type": data.get("Loyalty Type"),
            "offer_type": data.get("Offer Type"),
            "occurance_status": data.get("Occurance Status"),
            "status": data.get("Status"),
            "start_date": data.get("Start Date"),
            "end_date": data.get("End Date"),
            "number_of_purchases": data.get("Number Of Purchases"),
            "number_of_issuances": data.get("Number Of Issuances"),
            "bar_code_std": data.get("Bar Code Std"),
            "product_code": data.get("Product Code"),
            "product": data.get("Product"),
            "promotional_qr_code": data.get("Promotional QR code"),
            "qr_code_expiry_in_mins": data.get("QR Code Expiry (In mins.)"),
            "user_cycle_duration_days": data.get("User Cycle Duration (In Days)"),
            "redeem_type": data.get("Redeem Type"),
            "loyalty_unique_code": data.get("Loyalty Unique Code"),
            "offer_details": data.get("Offer Details"),
            "terms_and_conditions": data.get("Terms And Conditions"),
            "steps_to_redeem": data.get("Steps to Redeem"),
            "cooldown_expiry_days": data.get("Cooldown / Expiry (In Days)"),
            "shop": data.get("Shop"),
            "operation_regions": data.get("Operation Regions"),
            "regions": data.get("Regions"),
            "areas": data.get("Areas"),
            "stations": data.get("Stations"),
            "image": data.get("Image"),
            "reward_image": data.get("Reward Image"),
        }

    return {
            "new_data": map_main_data(new_data),
            "old_data": map_main_data(old_data),
            "loyalty_products": loyalty_products_resp,
            "loyalty_occurrences": loyalty_occurrences_resp,
    }


def get_sites_details(new_data, old_data):
    """Return site audit trail details."""
    # new_data = json_load(new_data)
    # old_data = json_load(old_data)

    new_station_images = new_data.get("station_images", [])
    old_station_images = old_data.get("station_images", [])
    station_images_resp = []

    for idx in range(max(len(new_station_images), len(old_station_images))):
        new_i = new_station_images[idx] if idx < len(new_station_images) else {}
        old_i = old_station_images[idx] if idx < len(old_station_images) else {}
        station_images_resp.append({
            "id": new_i.get("id") or old_i.get("id"),
            "image_path_new": new_i.get("image_path"),
            "image_path_old": old_i.get("image_path"),
        })

    new_amenities = new_data.get("amenities", [])
    old_amenities = old_data.get("amenities", [])
    amenities_resp = []

    for idx in range(max(len(new_amenities), len(old_amenities))):
        new_a = new_amenities[idx] if idx < len(new_amenities) else {}
        old_a = old_amenities[idx] if idx < len(old_amenities) else {}
        amenities_resp.append({
            "id": new_a.get("id") or old_a.get("id"),
            "service_name_new": new_a.get("service_name"),
            "service_name_old": old_a.get("service_name"),
            "image_path_new": new_a.get("image_path"),
            "image_path_old": old_a.get("image_path"),
            "service_type_new": new_a.get("service_type"),
            "service_type_old": old_a.get("service_type"),
        })

    new_retails = new_data.get("retails", [])
    old_retails = old_data.get("retails", [])
    retails_resp = []

    for idx in range(max(len(new_retails), len(old_retails))):
        new_r = new_retails[idx] if idx < len(new_retails) else {}
        old_r = old_retails[idx] if idx < len(old_retails) else {}
        retails_resp.append({
            "id": new_r.get("id") or old_r.get("id"),
            "service_name_new": new_r.get("service_name"),
            "service_name_old": old_r.get("service_name"),
            "image_path_new": new_r.get("image_path"),
            "image_path_old": old_r.get("image_path"),
            "service_type_new": new_r.get("service_type"),
            "service_type_old": old_r.get("service_type"),
        })

    new_food = new_data.get("food_to_go", [])
    old_food = old_data.get("food_to_go", [])
    food_to_go_resp = []

    for idx in range(max(len(new_food), len(old_food))):
        new_f = new_food[idx] if idx < len(new_food) else {}
        old_f = old_food[idx] if idx < len(old_food) else {}
        food_to_go_resp.append({
            "id": new_f.get("id") or old_f.get("id"),
            "service_name_new": new_f.get("service_name"),
            "service_name_old": old_f.get("service_name"),
            "image_path_new": new_f.get("image_path"),
            "image_path_old": old_f.get("image_path"),
            "service_type_new": new_f.get("service_type"),
            "service_type_old": old_f.get("service_type"),
        })

    def map_main_data(data):
        return {
            "station_id": data.get("Station ID"),
            "station_name": data.get("Station Name"),
            "station_address_1": data.get("Station Address 1"),
            "station_address_2": data.get("Station Address 2"),
            "station_address_3": data.get("Station Address 3"),
            "town": data.get("Town"),
            "post_code": data.get("Post Code"),
            "country": data.get("Country"),
            "brand": data.get("Brand"),
            "owner": data.get("Owner"),
            "latitude": data.get("Latitude"),
            "longitude": data.get("Longitude"),
            "email": data.get("Email"),
            "phone": data.get("Phone"),
            "status": data.get("Status"),
            "station_type": data.get("Station Type"),
            "site_title": data.get("Site Title"),
            "operation_region": data.get("Operation Region"),
            "region": data.get("Region"),
            "regional_manager": data.get("Regional Manager"),
            "area": data.get("Area"),
            "area_retail_manager": data.get("Area Retail Manager"),
            "working_hours": data.get("working_hours", {}),
        }

    return {
            "new_data": map_main_data(new_data),
            "old_data": map_main_data(old_data),
            "station_images": station_images_resp,
            "amenities": amenities_resp,
            "retails": retails_resp,
            "food_to_go": food_to_go_resp,
    }


def get_audit_trail_detail(validated_data):
    """
    Fetch detailed audit trail record with old/new data and metadata.
    """
    audit_entry : AuditTrail = validated_data.get("audit_instance")
    new_data_raw = safe_json_load(audit_entry.new_data)
    old_data_raw = safe_json_load(audit_entry.previous_data)

    new_data = new_data_raw[0] if isinstance(new_data_raw, list) and new_data_raw else (new_data_raw or {})
    old_data = old_data_raw[0] if isinstance(old_data_raw, list) and old_data_raw else (old_data_raw or {})

    module_type = validated_data.get("module_type")

    if module_type.lower() == "sites":
        module_details = {"sites_details": get_sites_details(new_data, old_data)}

    elif module_type.lower() == "offers":
        module_details = {"offers_details": get_offers_details(new_data, old_data)}

    else:
        module_details = {}

    response_data = {
        "id": audit_entry.id,
        "user_name": audit_entry.user_name,
        "action": audit_entry.action,
        "created_date": audit_entry.created_date,
        "updated_date": audit_entry.updated_date,
        "review_details": {
            "reviewed_by": audit_entry.reviewd_by,
            "reviewed_date": audit_entry.review_date,
            "reviewed_status": audit_entry.review_status,
        },
        **module_details
    }

    return {
        "status": True,
        "message": "Audit details fetched successfully.",
        "data": response_data
    }


def marked_as_reviewed(validated_data):

    audit_id = validated_data.get("id")
    AuditTrail.objects.filter(
                id__exact=int(audit_id)
            ).update(
                review_status=YES,
                reviewd_by="Test User",
                review_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
            )
    return True