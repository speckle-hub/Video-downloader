#!/usr/bin/env python3
import sys
import os


def main():
    print("=" * 50)
    print("  Video Downloader")
    print("  Supports YouTube, Twitter, TikTok, Instagram,")
    print("  Facebook, Reddit, and 1000+ other sites")
    print("=" * 50)
    print()
    print("Choose a mode:")
    print("  1) Desktop App (GUI)")
    print("  2) Web App (works on mobile too)")
    print()
    print("  Or: python desktop_app.py")
    print("  Or: python web_app.py")
    print()

    while True:
        choice = input("Enter 1 or 2 (or q to quit): ").strip()
        if choice == '1':
            from desktop_app import main as desktop_main
            desktop_main()
            break
        elif choice == '2':
            from web_app import main as web_main
            web_main()
            break
        elif choice.lower() in ('q', 'quit', 'exit'):
            break
        else:
            print("Invalid choice. Enter 1, 2, or q.")


if __name__ == '__main__':
    main()
