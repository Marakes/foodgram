import pytest


@pytest.mark.django_db
def test_avatar_put_and_delete(auth, user, small_png_b64):
    # PUT с base64
    resp = auth.put(
        "/api/users/me/avatar/",
        data={"avatar": small_png_b64},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    assert resp.json()["avatar"]  # вернулся абсолютный URL

    # DELETE
    resp = auth.delete("/api/users/me/avatar/")
    assert resp.status_code == 204
