"""Public verify redirect — handles QR code scans."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/{code}", response_class=HTMLResponse)
def public_verify(code: str):
    """Browser QR scan lands here; redirect to the frontend verify page."""
    safe = "".join(c for c in code if c.isalnum() or c == "-")[:9]
    return HTMLResponse(
        f'<!doctype html><html><head>'
        f'<meta http-equiv="refresh" content="0;url=/verify?code={safe}">'
        f'<title>Redirecting...</title></head>'
        f'<body><p>Redirecting to verification page...</p></body></html>',
        status_code=200,
    )
