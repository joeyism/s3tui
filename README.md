# S3 TUI

A Terminal User Interface (TUI) for AWS S3 with ranger-style navigation.

## Features

- 📦 **Browse S3 Buckets** - View all your S3 buckets at a glance
- 📁 **Multi-pane Navigation** - Ranger-style interface with up to 4 panes
- 📥 **File Downloads** - Download files from S3 with a simple dialog
- 📋 **Copy S3 Paths** - Copy S3 URIs to clipboard
- 🔍 **Real-time Search** - Filter items as you type
- ⚡ **Fast Navigation** - Keyboard-driven interface
- 🌙 **Dark Mode** - Easy on the eyes
- 🔄 **Async Loading** - Non-blocking UI with loading indicators

## Installation

### From PyPI (once published)

```bash
pip install s3tui
```

### From Source

```bash
git clone https://github.com/joeyism/s3tui.git
cd s3tui
pip install -e .
```

## Prerequisites

You need AWS credentials configured. S3 TUI will use credentials from:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS credentials file (`~/.aws/credentials`)
- IAM role (if running on EC2)

## Usage

Simply run:

```bash
s3tui
```

## Keybindings

| Key | Action |
|-----|--------|
| `↑/↓` or `j/k` | Navigate items up/down |
| `→` or `Enter` | Open bucket/folder, or show file actions |
| `←` or `h` | Go back to previous pane |
| `/` | Focus search bar |
| `Esc` | Clear search / Cancel dialog |
| `q` or `Ctrl+C` | Quit |

## Features in Detail

### Multi-Pane Navigation
Navigate through S3 buckets and folders with up to 4 side-by-side panes. The number of panes adapts to your terminal width (minimum 30 characters per pane).

### File Actions
When you select a file (press `→` or `Enter`), a dialog appears with options to:
- **Download**: Save the file to your local filesystem (specify path or use current directory)
- **Copy S3 Path**: Copy the S3 URI (e.g., `s3://bucket/path/to/file`) to clipboard
- **Cancel**: Return to the pane view

### Search/Filter
Press `/` to focus the search bar and filter items in real-time. Press `Esc` to clear the search and return focus to the file list.

### Loading Indicators
When navigating into folders or buckets, or downloading files, a loading popup appears while fetching data from S3.

## Requirements

- Python 3.8+
- boto3
- textual

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
