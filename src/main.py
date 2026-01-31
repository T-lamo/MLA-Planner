from fastapi import FastAPI

app = FastAPI(title="MLA App")


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}
