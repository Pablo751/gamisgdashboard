#!/usr/bin/env python3
"""
Gaming Marketing Analytics Dashboard
Entry point for Railway deployment
"""

from datvis_marketing import app, server

if __name__ == "__main__":
    # This will only run locally for testing
    app.run_server(debug=False, host='0.0.0.0', port=8050)
else:
    # This is what gunicorn will use
    application = server 