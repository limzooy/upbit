from fastapi import FastAPI
from controller import router

# FastAPI 애플리케이션 생성
app = FastAPI()

# 라우터 등록
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버 정상 작동 중"}
