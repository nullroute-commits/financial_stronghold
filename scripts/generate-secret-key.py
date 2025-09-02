#!/usr/bin/env python3
"""Generate a secure Django SECRET_KEY."""

import secrets
import string

def generate_secret_key(length=50):
    """Generate a secure random secret key."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(chars) for _ in range(length))

if __name__ == "__main__":
    print("Generated SECRET_KEY:")
    print(generate_secret_key())
    print("\nAdd this to your environment variables:")
    print(f"export SECRET_KEY='{generate_secret_key()}'")