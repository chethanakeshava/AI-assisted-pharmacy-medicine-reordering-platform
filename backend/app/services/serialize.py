from ..models import Order


def order_out(o: Order, with_ai: bool = False) -> dict:
    out = {"id": o.id, "code": o.code, "status": o.status, "store_id": o.store_id,
           "prescription_id": o.prescription_id, "profile_id": o.profile_id,
           "invoice_no": o.invoice_no, "created_at": o.created_at.isoformat(),
           "items": [{"id": i.id, "product_id": i.product_id, "product_name": i.product.name, "pack": i.product.pack, "qty": i.qty, "schedule": i.schedule,
                      "unit_price": i.unit_price, "status": i.status, "reject_reason": i.reject_reason,
                      "approved_by": i.approved_by} for i in o.items]}
    out["total"] = round(sum(i.qty * i.unit_price for i in o.items if i.status != "REJECTED"), 2)
    return out
