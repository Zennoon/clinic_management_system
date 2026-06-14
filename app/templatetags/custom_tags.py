from decimal import Decimal

from django import template
from django.utils.html import format_html

register = template.Library()


def get_variant_styles(variant):
    styles = ""
    match variant:
        case "brand":
            styles = "bg-indigo-600 hover:bg-indigo-500"
        case "success":
            styles = "bg-emerald-600 hover:bg-emerald-500"
        case "info":
            styles = "bg-blue-600 hover:bg-blue-500"
        case "error":
            styles = "bg-red-600 hover:bg-red-500"
        case _:
            styles = "bg-indigo-600 hover:bg-indigo-500"
    return styles


@register.simple_tag
def define(val):
    return val


@register.simple_block_tag
def wrapped_button(
    content,
    text=None,
    variant="brand",
    disabled=False,
    tip=None,
    hx_get=None,
    hx_target=None,
    hx_swap=None,
    hx_push=False,
):
    styles = get_variant_styles(variant)
    attrs = [f'class="btn flex gap-2 items-center text-white {styles}"']
    if disabled:
        attrs.append("disabled")
    if hx_get and not disabled:
        attrs.append(f'hx-get="{hx_get}"')
    if hx_target and not disabled:
        attrs.append(f'hx-target="{hx_target}"')
    if hx_swap and not disabled:
        attrs.append(f'hx-swap="{hx_swap}"')
    if hx_push and not disabled:
        attrs.append(f'hx-push-url="{hx_push}"')

    output = f"""
        <div {f'class="tooltip" data-tip="{tip}"' if tip else ''}>
            <button {" ".join(attrs)}>
                {content}
                {text or ""}
            </button>
        </div>

    """

    return format_html(output, kwargs={})


@register.simple_tag
def div(num1, num2):
    try:
        return Decimal(num1) / Decimal(num2)
    except (ZeroDivisionError, TypeError, ValueError):
        return num1
