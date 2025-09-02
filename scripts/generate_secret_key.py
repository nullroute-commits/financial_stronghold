#!/usr/bin/env python3
"""
Generate secure Django SECRET_KEY for production use.
Created by Team Delta (Security & Compliance Agents)

Usage:
    python scripts/generate_secret_key.py
"""

import secrets
import string


def generate_secret_key(length=50):
    """Generate a secure random secret key for Django."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


if __name__ == "__main__":
    secret_key = generate_secret_key()
    print("Generated Django SECRET_KEY:")
    print(f"SECRET_KEY={secret_key}")
    print("\nAdd this to your environment configuration file.")
    print("NEVER commit this key to version control!")