
import hmac

from fastapi import Header, HTTPException

from app.core.config import settings


def verify_recovery_api_key(
    x_recovery_api_key: str | None = Header(
        default=None,
        alias="X-Recovery-API-Key",
    ),
) -> None:
    expected_key = settings.recovery_api_key

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Recovery API key is not configured.",
        )

    if (
        not x_recovery_api_key
        or not hmac.compare_digest(
            x_recovery_api_key,
            expected_key,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing recovery API key.",
        )
