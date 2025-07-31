#!/usr/bin/env python3
"""
Startup script for the Slack Data Manager Bot.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

if __name__ == "__main__":
    from main import create_app
    
    try:
        app = create_app()
        print("🚀 Slack Data Manager Bot starting...")
        print("📊 Bot is ready to handle commands and interactions!")
        print("🌐 Server running on http://localhost:5000")
        print("📝 Available endpoints:")
        print("   - /health (health check)")
        print("   - / (root)")
        print("   - /api/command (Slack commands)")
        print("   - /api/interactions/command (Slack interactions)")
        print("\nPress Ctrl+C to stop the bot.")
        
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1) 