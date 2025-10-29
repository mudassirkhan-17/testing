from fastapi import FastAPI

# Create a FastAPI app
app = FastAPI()

# Define a simple GET endpoint
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/create")
def create_item(item: dict):
    return {"message": f"Item {item} created!"}
 