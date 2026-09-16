import json
from pathlib import Path


def test_vercel_security_headers_cover_every_route_with_same_origin_csp():
    config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))

    assert config["headers"][0]["source"] == "/(.*)"
    headers = {item["key"]: item["value"] for item in config["headers"][0]["headers"]}
    assert headers["Content-Security-Policy"] == (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_page_metadata_favicon_and_robots_are_present():
    page = Path("public/index.html").read_text(encoding="utf-8")

    assert '<meta name="description"' in page
    assert 'href="/favicon.svg"' in page
    assert '<svg' in Path("public/favicon.svg").read_text(encoding="utf-8")
    assert Path("public/robots.txt").read_text(encoding="utf-8") == "User-agent: *\nAllow: /\n"
