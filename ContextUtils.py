from typing import Optional


def get_fixed_size(context):
    return context.get("fixed_size", 0)


def get_text(context):
    return context.get("text", "")


def move_menu_left(context):
    selected_index = context.get("selected_index", 0)

    context["selected_index"] = (selected_index - 1) % len(context["items"])


def move_menu_right(context):
    selected_index = context.get("selected_index", 0)

    context["selected_index"] = (selected_index + 1) % len(context["items"])


def get_cursor_index(context):
    return context.get("cursor_index", 0)


def get_text_length(context):
    if "text" in context:
        return len(context["text"])
    else:
        return -1


def get_x(context):
    return context.get("x", 0)


def scroll_up(context):
    selected_item = context["selected"]
    items = context["items"]
    item, index = get_selected(selected_item, items)

    try:
        new_selected_item = items[max(0, index - 1)]
    except IndexError:
        new_selected_item = None

    context["selected"] = new_selected_item


def scroll_down(context):
    selected_item = context["selected"]
    items = context["items"]
    item, index = get_selected(selected_item, items)

    try:
        new_selected_index = min(len(items) - 1, index + 1)
        new_selected_item = items[new_selected_index]
    except IndexError:
        new_selected_item = None

    context["selected"] = new_selected_item


def is_hidden(context):
    return context.get("hidden", False)


# Sanitizes index to make sure it's in a list
def get_selected(item, items) -> (Optional[object], int):
    if item is None:
        if len(items) > 0:
            return items[0], 0
        else:
            return None, 0

    if item in items:
        return item, items.index(item)
    else:
        return None, 0
