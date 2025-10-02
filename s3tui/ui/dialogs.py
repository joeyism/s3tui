"""Modal dialog screens"""

import os
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, LoadingIndicator, Button, Label, Input
from textual.screen import ModalScreen


class LoadingScreen(ModalScreen):
    """Loading modal screen"""

    CSS = """
    LoadingScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0);
    }

    #loading-container {
        width: 40;
        height: 7;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #loading-text {
        text-align: center;
        margin-top: 1;
    }
    """

    ALLOW_IN_MAXIMIZED_VIEW = True

    def compose(self) -> ComposeResult:
        with Container(id="loading-container"):
            yield LoadingIndicator()
            yield Static("Loading...", id="loading-text")


class FileActionDialog(ModalScreen):
    """Dialog for file actions: download or copy S3 path"""

    CSS = """
    FileActionDialog {
        align: center middle;
    }

    #file-dialog {
        width: 70;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #file-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #file-name {
        text-align: center;
        margin-bottom: 1;
    }

    #s3-path {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    #file-path-input {
        margin: 1 0;
        width: 100%;
    }

    .path-label {
        margin-top: 1;
    }

    #file-buttons {
        align: center middle;
        height: auto;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, file_name: str, bucket: str, s3_key: str):
        super().__init__()
        self.file_name = file_name
        self.bucket = bucket
        self.s3_key = s3_key
        self.s3_uri = f"s3://{bucket}/{s3_key}"
        self.download_path = os.getcwd()

    def compose(self) -> ComposeResult:
        with Container(id="file-dialog"):
            yield Label("File Actions", id="file-title")
            yield Label(f"📄 {self.file_name}", id="file-name")
            yield Label(self.s3_uri, id="s3-path")
            yield Label("Download to:", classes="path-label")
            yield Input(
                value=self.download_path,
                placeholder="Enter download directory path",
                id="file-path-input"
            )
            with Horizontal(id="file-buttons"):
                yield Button("Download", variant="primary", id="download-btn")
                yield Button("Copy S3 Path", variant="default", id="copy-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#download-btn")
    def handle_download(self) -> None:
        """Handle download button press"""
        path_input = self.query_one("#file-path-input", Input)
        download_dir = path_input.value.strip()

        if not download_dir:
            download_dir = self.download_path

        # Expand ~ to home directory
        download_dir = os.path.expanduser(download_dir)

        # Create full path
        if os.path.isdir(download_dir):
            full_path = os.path.join(download_dir, self.file_name)
        else:
            # Treat as full file path
            full_path = download_dir

        self.dismiss(("download", full_path))

    @on(Button.Pressed, "#copy-btn")
    def handle_copy(self) -> None:
        """Handle copy S3 path button press"""
        self.dismiss(("copy", self.s3_uri))

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        """Handle cancel button press"""
        self.dismiss(("cancel", None))

    def on_key(self, event) -> None:
        """Handle escape key"""
        if event.key == "escape":
            self.dismiss(("cancel", None))
