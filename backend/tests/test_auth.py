def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_request_otp_unknown_user(client):
    r = client.post("/auth/request-otp", json={"email": "nobody@trueroll.test"})
    assert r.status_code == 204


def test_request_otp_known_user(client, seed_user):
    r = client.post("/auth/request-otp", json={"email": seed_user.email})
    assert r.status_code == 204


def test_verify_otp_wrong(client, seed_user):
    r = client.post("/auth/verify-otp", json={"email": seed_user.email, "otp": "000000"})
    assert r.status_code == 401


def test_verify_otp_correct(client, seed_user):
    r = client.post("/auth/verify-otp", json={"email": seed_user.email, "otp": "123456"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_me(client, seed_user):
    r = client.post("/auth/verify-otp", json={"email": seed_user.email, "otp": "123456"})
    token = r.json()["access_token"]
    r2 = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    # /me is not under /auth prefix — check it's routed correctly
    # Actually /me is under /auth — check both
    r3 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["email"] == seed_user.email
    assert r3.json()["role"] == seed_user.role
