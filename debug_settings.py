from interpretation_service.infrastructure.config.settings import settings
try:
    print(f"Settings loaded. Key present: {bool(settings.groq_api_key)}")
except Exception as e:
    print(f"Error loading settings: {e}")
