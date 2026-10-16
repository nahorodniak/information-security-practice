from fastapi import FastAPI

app = FastAPI(title="Електронний деканат")


@app.get("/")
def root():
    return {"message": "Hello World"}
