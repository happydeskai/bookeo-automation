#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Date: 02/21/2024
    Author: Joshua David Golafshan
"""

import platform
import time
import pyautogui

from src.application_constants import INTERMEDIATE_WAIT_TIME


def copy_to_clipboard():
    """Copies text to clipboard using the correct OS-specific hotkeys."""
    try:
        if platform.system() == "Darwin":
            pyautogui.hotkey('command', 'a')
            pyautogui.hotkey('command', 'c')
        else:  # Windows & Linux
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'c')

        print("✅ Text copied to clipboard successfully.")
    except Exception as e:
        print(f"❌ Error copying text: {e}")
        quit()


def clean_sheet():
    """Select all cells"""
    try:
        if platform.system() == "Darwin":
            pyautogui.hotkey('command', 'a')
            time.sleep(0.2)
            pyautogui.hotkey('command', 'a')
        else:  # Windows & Linux
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.hotkey("delete")

        print("✅ Sheet Cleaned")
    except Exception as e:
        print(f"❌ Error Cleaning sheet: {e}")
        quit()


def paste_from_clipboard():
    """Pastes clipboard data using OS-specific hotkeys."""
    try:
        if platform.system() == "Darwin":
            pyautogui.hotkey('command', 'V')
        else:  # Windows/Linux
            pyautogui.hotkey('ctrl', 'v')
            print("I am windows")

        time.sleep(INTERMEDIATE_WAIT_TIME)
        pyautogui.press("enter")  # Confirm paste
        print("✅ Data pasted into Google Sheets successfully.")
    except Exception as e:
        print(f"❌ Error pasting data: {e}")
        quit()
