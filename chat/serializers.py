"""Plain-dict shapes for the chat JSON endpoints.

Kept in one place so the visitor widget and the agent inbox always describe a
message the same way.
"""


def agent_display_name(user):
    if user is None:
        return ''
    return user.first_name or user.get_short_name() or user.username


def product_card(product):
    if product is None:
        return None
    image = product.list_image
    return {
        'id': product.pk,
        'name': product.name,
        'sku': product.sku,
        'brand': product.brand.name if product.brand_id else '',
        'category': product.category.name if product.category_id else '',
        'image': image.url if image else '',
        'url': product.get_absolute_url(),
        'stock': product.stock_quantity,
    }


def message_dict(message):
    return {
        'id': message.pk,
        'sender': message.sender,
        'body': message.body,
        'agent': agent_display_name(message.agent),
        'product': product_card(message.product),
        'at': message.created_at.isoformat(),
    }


def conversation_dict(conversation, for_agent=False):
    data = {
        'id': conversation.pk,
        'channel': conversation.channel,
        'channel_label': conversation.get_channel_display(),
        'status': conversation.status,
        'agent': agent_display_name(conversation.assigned_to),
        'name': conversation.customer_name,
    }
    if for_agent:
        data.update({
            'phone': conversation.phone,
            'email': conversation.email,
            'is_member': conversation.customer_id is not None,
            'assigned_id': conversation.assigned_to_id,
            'created_at': conversation.created_at.isoformat(),
            'last_message_at': conversation.last_message_at.isoformat(),
            'quote': (
                {'id': conversation.quote.pk, 'reference': conversation.quote.reference}
                if conversation.quote_id else None
            ),
        })
    return data
