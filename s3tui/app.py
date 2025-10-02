"""Main S3 TUI application"""

import sys
from typing import List, Dict, Tuple
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Input, ListItem, Static
from textual.binding import Binding

from .libs import S3Client
from .ui import LoadingScreen, FileActionDialog, S3ListView
from .utils import copy_to_clipboard


class S3TUI(App):
    """Textual TUI application for S3 navigation"""

    CSS = """
    Screen {
        background: $surface;
    }

    #search-input {
        dock: top;
        height: 3;
        border: solid $primary;
    }

    #panes {
        height: 1fr;
    }

    .pane {
        width: 1fr;
        height: 1fr;
    }

    S3ListView {
        height: 1fr;
        border: solid $primary;
    }

    S3ListView:focus {
        border: solid $accent;
    }

    ListItem {
        padding: 0 2;
    }

    .folder {
        color: $accent;
        text-style: bold;
    }

    .file {
        color: $text;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("escape", "clear_search", "Clear Search"),
        Binding("/", "focus_search", "Search"),
        Binding("left,h", "go_left", "Go Left", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.dark = True  # Force dark mode
        self.s3_client = S3Client()
        self.search_query: str = ''

        # Track panes: List of (bucket, prefix, items)
        self.panes: List[Dict] = [
            {'bucket': None, 'prefix': '', 'items': []}
        ]
        self.current_pane = 0

        # Navigation history to track full depth beyond visible panes
        self.nav_history: List[Dict] = []

    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header()
        yield Input(placeholder="Search (press / to focus)...", id="search-input")
        yield Horizontal(id="panes")
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application"""
        self.title = "S3 TUI"
        self.update_status("Loading buckets...")
        self.create_pane(0)
        self.load_buckets_in_pane(0)
        self.focus_pane(0)

    def update_status(self, message: str) -> None:
        """Update the status bar"""
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(message)

    def get_max_panes(self) -> int:
        """Calculate max panes based on screen width"""
        width = self.size.width
        # Each pane needs at least 30 characters to be usable
        max_by_width = max(1, width // 30)
        # Hard limit of 4 panes
        return min(4, max_by_width)

    def create_pane(self, pane_index: int) -> int:
        """
        Create a new pane at the given index
        Returns: The actual pane index that was created (may differ due to max panes limit)
        """
        panes_container = self.query_one("#panes", Horizontal)

        # Remove all panes after this index
        existing = list(panes_container.query(S3ListView))
        for i, pane in enumerate(existing):
            if i >= pane_index:
                pane.remove()

        # Check if we've hit the max panes limit
        max_panes = self.get_max_panes()
        if pane_index >= max_panes:
            # Remove the leftmost pane and shift everything
            if existing:
                existing[0].remove()
                # Shift pane data
                self.panes = self.panes[1:]
                pane_index = max_panes - 1

        # Create new pane
        list_view = S3ListView(pane_id=f"pane-{pane_index}", classes="pane")
        panes_container.mount(list_view)

        return pane_index

    def focus_pane(self, pane_index: int) -> None:
        """Focus a specific pane"""
        panes = list(self.query(S3ListView))
        if pane_index < len(panes):
            panes[pane_index].focus()
            self.current_pane = pane_index

    def load_buckets_in_pane(self, pane_index: int) -> None:
        """Load and display S3 buckets in a pane"""
        try:
            buckets = self.s3_client.list_buckets()
            items = [(bucket, 'bucket') for bucket in buckets]

            # Update pane data
            while len(self.panes) <= pane_index:
                self.panes.append({'bucket': None, 'prefix': '', 'items': []})

            self.panes[pane_index] = {'bucket': None, 'prefix': '', 'items': items}
            self.render_pane(pane_index)
            self.update_status(f"📦 Buckets ({len(buckets)} total)")
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}")

    def load_objects_in_pane(self, pane_index: int, bucket: str, prefix: str = '', from_thread: bool = False) -> None:
        """Load and display objects in a bucket in a pane"""
        try:
            # Update status
            status_msg = f"🔄 Loading {bucket}/{prefix}..."
            if from_thread:
                self.call_from_thread(self.update_status, status_msg)
            else:
                self.update_status(status_msg)

            folders, files = self.s3_client.list_objects(bucket, prefix)
            items = [(f, 'folder') for f in folders] + [(f, 'file') for f in files]

            # Update pane data
            while len(self.panes) <= pane_index:
                self.panes.append({'bucket': None, 'prefix': '', 'items': []})

            self.panes[pane_index] = {'bucket': bucket, 'prefix': prefix, 'items': items}

            # Render pane
            if from_thread:
                self.call_from_thread(self.render_pane, pane_index)
            else:
                self.render_pane(pane_index)

            # Update status with current path
            path_display = f"{bucket}/"
            if prefix:
                path_display += prefix
            success_msg = f"📁 {path_display} ({len(folders)} folders, {len(files)} files)"
            if from_thread:
                self.call_from_thread(self.update_status, success_msg)
            else:
                self.update_status(success_msg)
        except Exception as e:
            error_msg = f"❌ Error loading {bucket}/{prefix}: {str(e)}"
            if from_thread:
                self.call_from_thread(self.update_status, error_msg)
            else:
                self.update_status(error_msg)
            # Log the full error for debugging
            import traceback
            print(f"Error details: {traceback.format_exc()}", file=sys.stderr)

    def render_pane(self, pane_index: int) -> None:
        """Render items in a specific pane based on search query"""
        import sys
        panes = list(self.query(S3ListView))
        print(f"render_pane({pane_index}): Found {len(panes)} panes via query, self.panes has {len(self.panes)} entries", file=sys.stderr)

        if pane_index >= len(panes):
            print(f"  -> pane_index {pane_index} >= len(panes) {len(panes)}, returning", file=sys.stderr)
            return

        list_view = panes[pane_index]
        list_view.clear()

        if pane_index >= len(self.panes):
            print(f"  -> pane_index {pane_index} >= len(self.panes) {len(self.panes)}, returning", file=sys.stderr)
            return

        items = self.panes[pane_index]['items']
        print(f"  -> Rendering {len(items)} items", file=sys.stderr)

        # Filter items based on search query
        if self.search_query:
            filtered_items = [
                (name, type_) for name, type_ in items
                if self.search_query.lower() in name.lower()
            ]
        else:
            filtered_items = items

        # Store items data in the list view
        list_view.items_data = filtered_items

        # Add items to list
        for name, type_ in filtered_items:
            if type_ == 'bucket':
                label = f"🪣 {name}"
                item = ListItem(Static(label, classes="folder"))
            elif type_ == 'folder':
                label = f"📁 {name}"
                item = ListItem(Static(label, classes="folder"))
            else:
                label = f"📄 {name}"
                item = ListItem(Static(label, classes="file"))
            list_view.append(item)

        if not filtered_items:
            list_view.append(ListItem(Static("(empty)", classes="file")))
        else:
            # Set cursor to first item
            list_view.index = 0

        # Force refresh of the list view
        list_view.refresh(layout=True)

    @on(S3ListView.ItemSelected)
    def handle_item_selected(self, message: S3ListView.ItemSelected) -> None:
        """Handle item selection from any pane"""
        sender = message._sender
        if not isinstance(sender, S3ListView):
            return

        # Find which pane sent the message
        panes = list(self.query(S3ListView))
        try:
            pane_index = panes.index(sender)
        except ValueError:
            # Sender pane no longer exists, ignore
            return

        # Update current pane immediately
        self.current_pane = pane_index

        item_name = message.item_name
        item_type = message.item_type

        if item_type == 'bucket':
            # We're navigating INTO a bucket
            # Store what we're navigating to (not where we are)
            self.nav_history.append({
                'bucket': item_name,
                'prefix': '',
                'type': 'bucket_contents',
                'name': item_name
            })
            # Create next pane and load bucket contents
            next_pane = pane_index + 1
            self.load_bucket_async(next_pane, item_name)
        elif item_type == 'folder':
            # We're navigating INTO a folder
            bucket = self.panes[pane_index]['bucket']
            current_prefix = self.panes[pane_index]['prefix']
            new_prefix = current_prefix + item_name + '/'

            # Store what we're navigating to
            self.nav_history.append({
                'bucket': bucket,
                'prefix': new_prefix,
                'type': 'folder_contents',
                'name': item_name
            })

            # Create next pane and load folder contents
            next_pane = pane_index + 1
            self.load_folder_async(next_pane, bucket, new_prefix)
        elif item_type == 'file':
            # Handle file selection - show file action dialog
            bucket = self.panes[pane_index]['bucket']
            current_prefix = self.panes[pane_index]['prefix']
            s3_key = current_prefix + item_name

            # Show file action dialog and handle result via callback
            self.show_file_dialog(item_name, bucket, s3_key)

    def show_file_dialog(self, file_name: str, bucket: str, s3_key: str) -> None:
        """Show file action dialog"""
        def handle_result(result) -> None:
            """Handle dialog result"""
            if result:
                action, value = result
                if action == "download" and value:
                    self.download_file_async(bucket, s3_key, value, file_name)
                elif action == "copy" and value:
                    success, message = copy_to_clipboard(value)
                    self.update_status(message)

        self.push_screen(FileActionDialog(file_name, bucket, s3_key), handle_result)

    def create_pane_sync(self, pane_index: int) -> None:
        """
        Synchronously create a pane and store the actual index created
        This is called from worker threads to handle the pane creation
        """
        actual_index = self.create_pane(pane_index)
        self._last_created_pane_index = actual_index

    @work(thread=True)
    def load_bucket_async(self, pane_index: int, bucket: str) -> None:
        """Load bucket contents asynchronously with loading indicator"""
        try:
            # Show loading indicator
            self.call_from_thread(self.push_screen, LoadingScreen())

            # Create pane in UI thread and get actual index
            self.call_from_thread(self.create_pane_sync, pane_index)
            # Get the actual pane index that was created
            actual_pane_index = getattr(self, '_last_created_pane_index', pane_index)

            # Load data in this worker thread
            self.load_objects_in_pane(actual_pane_index, bucket, '', from_thread=True)

            # Update current_pane before focusing
            self.current_pane = actual_pane_index
            # Focus and hide loading
            self.call_from_thread(self.focus_pane, actual_pane_index)
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.call_from_thread(self.update_status, error_msg)
            import traceback
            print(f"Load bucket error: {traceback.format_exc()}", file=sys.stderr)
        finally:
            self.call_from_thread(self.pop_screen)

    @work(thread=True)
    def load_folder_async(self, pane_index: int, bucket: str, prefix: str) -> None:
        """Load folder contents asynchronously with loading indicator"""
        try:
            # Show loading indicator
            self.call_from_thread(self.push_screen, LoadingScreen())

            # Create pane in UI thread and get actual index
            self.call_from_thread(self.create_pane_sync, pane_index)
            # Get the actual pane index that was created
            actual_pane_index = getattr(self, '_last_created_pane_index', pane_index)

            # Load data in this worker thread
            self.load_objects_in_pane(actual_pane_index, bucket, prefix, from_thread=True)

            # Update current_pane before focusing
            self.current_pane = actual_pane_index
            # Focus and hide loading
            self.call_from_thread(self.focus_pane, actual_pane_index)
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.call_from_thread(self.update_status, error_msg)
            import traceback
            print(f"Load folder error: {traceback.format_exc()}", file=sys.stderr)
        finally:
            self.call_from_thread(self.pop_screen)

    @work(thread=True)
    def download_file_async(self, bucket: str, s3_key: str, local_path: str, file_name: str) -> None:
        """Download file from S3 asynchronously"""
        try:
            # Show loading indicator
            self.call_from_thread(self.push_screen, LoadingScreen())
            self.call_from_thread(self.update_status, f"⬇️  Downloading {file_name}...")

            # Download the file
            self.s3_client.download_file(bucket, s3_key, local_path)

            # Success message
            self.call_from_thread(self.update_status, f"✅ Downloaded {file_name} to {local_path}")
        except Exception as e:
            error_msg = f"❌ Error downloading {file_name}: {str(e)}"
            self.call_from_thread(self.update_status, error_msg)
            import traceback
            print(f"Download error: {traceback.format_exc()}", file=sys.stderr)
        finally:
            self.call_from_thread(self.pop_screen)

    @on(Input.Changed, "#search-input")
    def handle_search(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        self.search_query = event.value

        # Re-render all panes with search filter
        panes = list(self.query(S3ListView))
        for i in range(len(panes)):
            self.render_pane(i)

        # If search is cleared, return focus to current pane
        if not event.value:
            self.focus_pane(self.current_pane)

    def rebuild_panes_from_history(self) -> None:
        """Rebuild visible panes from navigation history"""
        import sys
        print(f"\n=== REBUILD PANES ===", file=sys.stderr)
        print(f"History depth: {len(self.nav_history)}", file=sys.stderr)
        print(f"History: {self.nav_history}", file=sys.stderr)

        # Clear all existing panes
        panes_container = self.query_one("#panes", Horizontal)
        for pane in list(panes_container.query(S3ListView)):
            pane.remove()

        self.panes = []

        # Calculate how many panes we can show
        max_panes = self.get_max_panes()
        history_depth = len(self.nav_history)

        if history_depth == 0:
            # At root level, just show buckets
            print("Showing buckets at root", file=sys.stderr)
            list_view = S3ListView(pane_id=f"pane-0", classes="pane")
            panes_container.mount(list_view)
            # Refresh to ensure mount is complete before loading data
            self.refresh()

            # Defer loading to ensure widget is fully mounted
            def load_root():
                self.load_buckets_in_pane(0)
                self.focus_pane(0)

            self.call_later(load_root)
            return

        # Build the full path: each pane shows where you CAN navigate from
        # For history: [bucket1, folder1, folder2]
        # Panes should show: [buckets, bucket1_contents, folder1_contents, folder2_contents]
        # But we also need to show parent levels so you see what you clicked on

        # Determine which slice of history to show
        total_panes_needed = history_depth + 1  # +1 for the buckets or parent level

        if total_panes_needed <= max_panes:
            # Show all: buckets + all history levels
            visible_history = self.nav_history[:]
            show_buckets_pane = True
            print(f"Showing all history with buckets. Visible: {len(visible_history)}", file=sys.stderr)
        else:
            # Show only the most recent levels that fit
            # We want to show the parents of the last (max_panes - 1) history items
            visible_history = self.nav_history[-(max_panes - 1):]
            show_buckets_pane = False
            print(f"Showing recent history. Visible: {len(visible_history)}, show_buckets: {show_buckets_pane}", file=sys.stderr)

        # Mount all panes first
        pane_widgets = []
        pane_index = 0

        # Determine how many total panes to create
        # We need: parent/buckets pane + one pane for each history item showing its CONTENTS
        # So if visible_history has 3 items, we need 4 panes total (1 parent + 3 contents)
        total_panes = 1 + len(visible_history)  # parent/buckets + visible history items contents

        # But cap at max_panes
        total_panes = min(total_panes, max_panes)

        # Create all pane widgets
        for i in range(total_panes):
            list_view = S3ListView(pane_id=f"pane-{i}", classes="pane")
            panes_container.mount(list_view)
            pane_widgets.append(list_view)

        # Refresh to ensure all mounts are complete
        self.refresh()
        print(f"Mounted {total_panes} pane widgets", file=sys.stderr)

        # Defer loading data until next tick to ensure widgets are fully mounted
        def load_all_panes():
            print(f"\n=== LOADING DATA INTO PANES ===", file=sys.stderr)
            print(f"Total panes created: {total_panes}", file=sys.stderr)
            print(f"show_buckets_pane: {show_buckets_pane}", file=sys.stderr)
            print(f"visible_history length: {len(visible_history)}", file=sys.stderr)

            pane_index = 0

            # First pane: buckets list (if we have room and we're showing early history)
            if show_buckets_pane:
                print(f"Pane {pane_index}: Loading buckets", file=sys.stderr)
                self.load_buckets_in_pane(pane_index)
                pane_index += 1
            else:
                # We're deep in navigation, show the parent of the first visible history item
                # The parent level is one level up from the first visible item
                first_item = visible_history[0]
                print(f"Pane {pane_index}: Loading parent of {first_item}", file=sys.stderr)

                # Show the parent level
                if first_item['type'] == 'bucket_contents':
                    # Parent is buckets list
                    print(f"  -> Parent is buckets", file=sys.stderr)
                    self.load_buckets_in_pane(pane_index)
                elif first_item['type'] == 'folder_contents':
                    # Parent is the bucket or parent folder
                    # Get the parent prefix by removing the last folder
                    parent_prefix = '/'.join(first_item['prefix'].rstrip('/').split('/')[:-1])
                    if parent_prefix:
                        parent_prefix += '/'
                    print(f"  -> Parent is {first_item['bucket']}/{parent_prefix}", file=sys.stderr)
                    self.load_objects_in_pane(pane_index, first_item['bucket'], parent_prefix)
                pane_index += 1

            # Subsequent panes: show each level from visible history
            for i, hist_item in enumerate(visible_history):
                if pane_index >= total_panes:
                    print(f"Skipping history item {i}, pane_index {pane_index} >= total_panes {total_panes}", file=sys.stderr)
                    break

                print(f"Pane {pane_index}: Loading visible_history[{i}] = {hist_item}", file=sys.stderr)

                # Load the contents of this level
                if hist_item['type'] == 'bucket_contents':
                    # Show contents of the bucket
                    print(f"  -> Bucket contents: {hist_item['bucket']}", file=sys.stderr)
                    self.load_objects_in_pane(pane_index, hist_item['bucket'], '')
                elif hist_item['type'] == 'folder_contents':
                    # Show contents of the folder
                    print(f"  -> Folder contents: {hist_item['bucket']}/{hist_item['prefix']}", file=sys.stderr)
                    self.load_objects_in_pane(pane_index, hist_item['bucket'], hist_item['prefix'])

                pane_index += 1

            print(f"Total panes loaded with data: {pane_index}, total panes available: {total_panes}", file=sys.stderr)
            print(f"Focusing pane: {pane_index - 1}", file=sys.stderr)

            # Focus the rightmost pane
            self.focus_pane(pane_index - 1)

        # Use call_later to defer loading until widgets are in the DOM
        self.call_later(load_all_panes)

    def action_go_left(self) -> None:
        """Navigate to the left pane"""
        if len(self.nav_history) == 0:
            # Already at the top level
            return

        # Pop the last navigation state
        self.nav_history.pop()

        # Rebuild all panes from navigation history
        self.rebuild_panes_from_history()

    def action_focus_search(self) -> None:
        """Focus the search input"""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self) -> None:
        """Clear the search query"""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.search_query = ""

        # Re-render all panes
        panes = list(self.query(S3ListView))
        for i in range(len(panes)):
            self.render_pane(i)

        self.focus_pane(self.current_pane)
