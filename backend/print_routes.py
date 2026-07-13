from app.main import app

print("All registered FastAPI routes:")
for route in app.routes:
    # Check if it has a path
    if hasattr(route, "path"):
        print(f"{route.methods} - {route.path}")
