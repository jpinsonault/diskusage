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
    index = get_selected_index(context)
    set_selected_index(context, new_index=index - 1)


def scroll_down(context):
    index = get_selected_index(context)
    set_selected_index(context, new_index=index + 1)


def scroll_to_top(context):
    set_selected_index(context, new_index=0)


def scroll_to_bottom(context):
    set_selected_index(context, new_index=len(context["items"]))


def is_hidden(context):
    return context.get("hidden", False)


def set_selected_index(context, new_index) -> int:
    selected_index = max(0, new_index)
    selected_index = min(len(context["items"]) - 1, selected_index)

    context["selected_index"] = selected_index
    return selected_index


def get_selected_index(context) -> int:
    selected_index = context.get("selected_index", 0)

    selected_index = max(0, selected_index)
    selected_index = min(len(context["items"]) - 1, selected_index)

    return selected_index


def get_items_len(context) -> int:
    items = context.get("items", None)

    if items is None:
        return None
    else:
        return len(items)