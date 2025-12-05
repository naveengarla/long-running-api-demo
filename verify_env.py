import sys
print(sys.executable)
try:
    import uvicorn
    print(f"uvicorn: {uvicorn.__file__}")
    import pydantic_settings
    print(f"pydantic_settings: {pydantic_settings.__file__}")
    print("SUCCESS")
except ImportError as e:
    print(f"ERROR: {e}")
