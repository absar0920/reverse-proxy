from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="Proxy Service")


class ProxyOptions(BaseModel):
    timeout: float = 30
    headers: dict[str, str] = {}
    follow_redirects: bool = True
    verify_ssl: bool = True


class ProxyRequest(BaseModel):
    route: str
    method: str = "GET"
    body: Any = None
    options: ProxyOptions = ProxyOptions()


@app.post("/proxy")
async def proxy(req: ProxyRequest):
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(req.options.timeout),
            follow_redirects=req.options.follow_redirects,
            verify=req.options.verify_ssl,
        ) as client:
            response = await client.request(
                method=req.method.upper(),
                url=req.route,
                headers=req.options.headers,
                json=req.body if req.body is not None else None,
            )

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream request timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
