from fastapi import FastAPI

from knowledgehub.api import router

app = FastAPI(title="KnowledgeHub")
app.include_router(router)
