from a2wsgi import ASGIMiddleware
from app.main import app

# Wrap ASGI app as WSGI so Vercel doesn't spin up uvicorn internally
app = ASGIMiddleware(app)
