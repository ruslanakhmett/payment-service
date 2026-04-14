import asyncio
import random

import httpx


async def send_webhook_with_retries(
    *,
    url: str,
    payload: dict,
    max_attempts: int,
) -> None:
    delay_s = 1.0
    timeout = httpx.Timeout(10.0, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_attempts + 1):
            try:
                resp = await client.post(url, json=payload)
                if 200 <= resp.status_code < 300:
                    return
                raise RuntimeError(f"Webhook returned {resp.status_code}")
            except Exception:
                if attempt >= max_attempts:
                    raise
                await asyncio.sleep(delay_s + random.uniform(0, 0.25))
                delay_s = min(delay_s * 2.0, 10.0)

