from django.utils import timezone
from sharedServices.common import safe_json_load
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


    if user_role:
        audit_records = audit_records.filter(user_role__icontains=user_role)
    if reviewed:
        audit_records = audit_records.filter(reviewed__iexact=reviewed)
    if module:
        audit_records = audit_records.filter(module__iexact=module)
    if action:
        audit_records = audit_records.filter(action__icontains=action)
    if start_date and end_date:
        audit_records = audit_records.filter(created_at__range=[start_date, end_date])

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

def get_audit_trail_detail(validated_data):
    """
    Fetch detailed audit trail record with old/new data and metadata.
    Includes loyalty_products and loyalty_occurrences comparison.
    """
    audit_entry = AuditTrail.objects.filter(id=validated_data.get("id")).first()
    if not audit_entry:
        return {
            "status": False,
            "message": "Audit entry not found.",
            "data": {}
        }

    new_data_raw = safe_json_load(audit_entry.new_data)
    old_data_raw = safe_json_load(audit_entry.previous_data)


    new_data = new_data_raw[0] if isinstance(new_data_raw, list) and new_data_raw else (new_data_raw or {})
    old_data = old_data_raw[0] if isinstance(old_data_raw, list) and old_data_raw else (old_data_raw or {})

    loyalty_products_new = new_data.get("loyalty_products", []) or []
    loyalty_products_old = old_data.get("loyalty_products", []) or []
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

    occurrences_new = new_data.get("loyalty_occurrences", []) or []
    occurrences_old = old_data.get("loyalty_occurrences", []) or []
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

    result = {
            "id": audit_entry.id,
            "user_name": audit_entry.user_name,
            "action":audit_entry.action,
            "created_date": audit_entry.created_date.strftime("%Y-%m-%dT%H:%M:%SZ") if audit_entry.created_date else None,
            "new_data": map_main_data(new_data),
            "old_data": map_main_data(old_data),
            "loyalty_products": loyalty_products_resp,
    }

    return result

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