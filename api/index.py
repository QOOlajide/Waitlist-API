"""
Vercel Serverless Function Entry Point.

This file exposes the FastAPI app for Vercel's Python runtime.
Vercel will automatically detect the `app` variable.
"""

from app.main import app

# Re-export for Vercel
__all__ = ["app"]
