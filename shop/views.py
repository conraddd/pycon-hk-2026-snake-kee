"""JSON API for the QR ordering app, plus the view that serves the built React app."""
import json
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Customer, MenuItem, Order, OrderItem, Shop
from .menu_data import ICE, SWEETNESS

POINTS_PER_DOLLAR = 1

# Menu pictures live in frontend/public/menu: a photo (<slug>.jpg) if we have one, else the illustration (<slug>.svg).
MENU_DIR = settings.BASE_DIR / "frontend" / "public" / "menu"
_PICTURES = {p.name for p in MENU_DIR.glob("*.*")} if MENU_DIR.exists() else set()


def _picture(name: str) -> str | None:
    for ext in ("jpg", "svg"):
        if f"{name}.{ext}" in _PICTURES:
            return f"/menu/{name}.{ext}"
    return None


def _pictures(m: MenuItem) -> tuple[str, dict | None]:
    """Default picture, plus hot/iced pictures for drinks that come both ways (same style as the default)."""
    default = _picture(m.slug) or f"/menu/{m.slug}.svg"
    if not (m.is_drink and m.iced_surcharge is not None and not m.iced_only):
        return default, None
    ext = default.rsplit(".", 1)[1]
    hot, iced = f"{m.slug}-hot.{ext}", f"{m.slug}-iced.{ext}"
    if hot in _PICTURES and iced in _PICTURES:
        return default, {"hot": f"/menu/{hot}", "iced": f"/menu/{iced}"}
    return default, None


def _item_json(m: MenuItem) -> dict:
    image, images = _pictures(m)
    return {
        "id": m.id, "slug": m.slug, "category": m.category,
        "name": {"en": m.name_en, "zh": m.name_zh},
        "description": {"en": m.description_en, "zh": m.description_zh},
        "price": str(m.price),
        "icedSurcharge": None if m.iced_surcharge is None else str(m.iced_surcharge),
        "icedOnly": m.iced_only,
        "image": image,
        "images": images,
    }


def _shop_or_404(raw) -> Shop:
    try:
        return get_object_or_404(Shop, pk=int(raw))
    except (TypeError, ValueError):
        raise Http404("unknown shop")


@require_GET
def menu(request):
    """The menu (the same in every shop) plus the shop's name for the header."""
    shop = _shop_or_404(request.GET.get("shop", 1))
    items = MenuItem.objects.filter(is_available=True)
    return JsonResponse({
        "shop": {"id": shop.id, "name": {"en": shop.name_en, "zh": shop.name_zh}},
        "categories": [{"id": c.value, "label": c.label} for c in MenuItem.Category],
        "items": [_item_json(m) for m in items],
        "options": {"sweetness": SWEETNESS, "ice": ICE},
    })


def find_or_join_member(email: str, name: str = "") -> Customer:
    """蛇記 Rewards: look up a member by email, or sign them up."""
    email = email.strip().lower()
    member = Customer.objects.filter(email__iexact=email).order_by("id").first()
    if member is None:
        try:
            with transaction.atomic():
                member = Customer.objects.create(email=email, name=name or email.split("@")[0])
        except IntegrityError:  # someone signed up with this email at the same moment
            member = Customer.objects.get(email__iexact=email)
    return member


def _parse_order(body: dict) -> tuple[Shop, list[tuple[MenuItem, dict, int]]]:
    """Validate the whole order before writing anything. Raises ValueError with a readable message."""
    lines = body.get("items")
    if not isinstance(lines, list) or not lines:
        raise ValueError("an order needs at least one item")
    try:
        shop = Shop.objects.get(pk=int(body.get("shopId", 1)))
        item_ids = [int(line["itemId"]) for line in lines]
        quantities = [max(1, int(line.get("qty", 1))) for line in lines]
    except (Shop.DoesNotExist, KeyError, TypeError, ValueError) as e:
        raise ValueError(f"invalid order: {e}") from e
    menu_items = MenuItem.objects.in_bulk(item_ids)
    if missing := sorted(set(item_ids) - set(menu_items)):
        raise ValueError(f"unknown items: {missing}")
    return shop, [(menu_items[i], line, qty) for i, line, qty in zip(item_ids, lines, quantities)]


@csrf_exempt  # demo app: the API is called by our own SPA; add CSRF/auth before real use
@require_POST
def place_order(request):
    try:
        body = json.loads(request.body)
        shop, lines = _parse_order(body)
    except ValueError as e:  # includes invalid JSON
        return JsonResponse({"error": str(e)}, status=400)

    with transaction.atomic():
        member = find_or_join_member(body["memberEmail"]) if body.get("memberEmail") else None
        order = Order.objects.create(shop=shop, customer=member, table_no=body.get("tableNo"),
                                     channel=body.get("channel", Order.Channel.DINE_IN))
        total = Decimal(0)
        for m, line, qty in lines:
            iced = m.is_drink and (m.iced_only or line.get("temperature") == "iced")
            price = m.price + ((m.iced_surcharge or 0) if iced else 0)
            OrderItem.objects.create(
                order=order, item=m, qty=qty, unit_price=price,
                temperature=("iced" if iced else "hot") if m.is_drink else "",
                sweetness=line.get("sweetness", "正常") if m.is_drink else "",
                ice=line.get("ice", "正常冰") if iced else "",
            )
            total += price * qty
        order.total = total
        order.save(update_fields=["total"])
        points = None
        if member:  # F(): add in the database, so two orders at once don't lose points
            Customer.objects.filter(pk=member.pk).update(points=F("points") + int(total) * POINTS_PER_DOLLAR)
            points = Customer.objects.values_list("points", flat=True).get(pk=member.pk)
    return JsonResponse({"orderId": order.id, "total": str(total), "points": points}, status=201)


@require_GET
def order_detail(request, order_id: int):
    order = get_object_or_404(Order.objects.select_related("shop"), pk=order_id)
    return JsonResponse({
        "orderId": order.id, "status": order.status, "tableNo": order.table_no,
        "total": str(order.total),
        "items": [{"name": {"en": oi.item.name_en, "zh": oi.item.name_zh}, "qty": oi.qty,
                   "unitPrice": str(oi.unit_price), "temperature": oi.temperature,
                   "sweetness": oi.sweetness, "ice": oi.ice}
                  for oi in order.items.select_related("item")],
    })


@require_GET
def health(request):
    return JsonResponse({"ok": True})


def spa(request):
    index = settings.BASE_DIR / "frontend" / "dist" / "index.html"
    if not index.exists():
        return HttpResponse("Frontend not built yet. Run `npm run build` in frontend/, "
                            "or use the Vite dev server on http://localhost:5173.", status=503)
    return HttpResponse(index.read_text(), content_type="text/html")
