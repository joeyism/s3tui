"""Custom ListView for S3 navigation"""

from typing import List, Tuple
from textual.widgets import ListView
from textual.message import Message


class S3ListView(ListView):
    """Custom ListView with navigation support"""

    class ItemSelected(Message):
        """Message sent when an item is selected for preview"""
        def __init__(self, item_name: str, item_type: str) -> None:
            self.item_name = item_name
            self.item_type = item_type
            super().__init__()

    def __init__(self, pane_id: str, **kwargs):
        super().__init__(**kwargs)
        self.pane_id = pane_id
        self.items_data: List[Tuple[str, str]] = []

    def on_key(self, event) -> None:
        """Handle key events for navigation"""
        if event.key == "right" or event.key == "l" or event.key == "enter":
            if self.index is not None and self.index < len(self.items_data):
                item_name, item_type = self.items_data[self.index]
                event.prevent_default()
                event.stop()
                self.post_message(self.ItemSelected(item_name, item_type))
        elif event.key == "left" or event.key == "h":
            event.prevent_default()
            event.stop()
            self.app.action_go_left()
