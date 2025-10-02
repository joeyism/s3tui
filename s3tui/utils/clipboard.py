"""Clipboard utilities"""

import sys
import subprocess


def copy_to_clipboard(text: str) -> tuple[bool, str]:
    """
    Copy text to clipboard

    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        # Try using pyperclip first
        try:
            import pyperclip
            pyperclip.copy(text)
            return True, f"📋 Copied to clipboard: {text}"
        except ImportError:
            pass

        # Fallback to platform-specific commands
        if sys.platform == "darwin":  # macOS
            process = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            process.communicate(text.encode('utf-8'))
            return True, f"📋 Copied to clipboard: {text}"
        elif sys.platform == "linux":
            try:
                # Try xclip first
                process = subprocess.Popen(
                    ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )
                process.communicate(text.encode('utf-8'))
                return True, f"📋 Copied to clipboard: {text}"
            except FileNotFoundError:
                # Try xsel as fallback
                try:
                    process = subprocess.Popen(
                        ['xsel', '--clipboard', '--input'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE
                    )
                    process.communicate(text.encode('utf-8'))
                    return True, f"📋 Copied to clipboard: {text}"
                except FileNotFoundError:
                    return False, f"⚠️  Clipboard not available. S3 path: {text}"
        else:
            return False, f"⚠️  Clipboard not supported. S3 path: {text}"
    except Exception as e:
        return False, f"❌ Error copying to clipboard: {str(e)}"
