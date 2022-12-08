from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse
from fastapi import Request, Response
from fastapi import Header
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pathlib import Path

import database, schemas, models

from stream.stream import get_stream_video, get_stream_video2

import json

router = APIRouter(
    prefix="/live"
)

templates = Jinja2Templates(directory="templates")

CHUNK_SIZE = 1024*1024
video_path = Path("./static/video/detect/h264_v01.mp4")

@router.get("/")
async def index(request:Request):
    # 보낼 request를 설정
    return templates.TemplateResponse("live.html", context={"request": request})

@router.get("/video")
async def video_endpoint(range: str = Header(None)):
    start, end = range.replace("bytes=", "").split("-")
    # print(start)
    # print(end)
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        filesize = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")

@router.get("/stream_video")
async def stream_video(request:Request):
    # StringResponse함수를 return하고,
    # 인자로 OpenCV에서 가져온 "바이트"이미지와 type을 명시
    return StreamingResponse(get_stream_video(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.post('/post')
async def get_test(form:schemas.MiniMapForm, db:Session=Depends(database.get_db)):
    
    minimapobj = db.query(models.MiniMap).filter(
                                                and_(models.MiniMap.sec >= form.sec),
                                                and_(models.MiniMap.sec <= form.sec+59),
                                                ).all()
    testdata = {}
    for data in minimapobj:
        sec = str(data.sec)
        frame = str(data.frame)
        cow_id = str(data.cow_id)
        x = str(data.xc)
        y = str(data.yc)
        if sec not in testdata.keys():
            testdata[sec] = {}
        if frame not in testdata[sec].keys():
            testdata[sec][frame] = {}
        testdata[sec][frame][cow_id] = {"x":x, "y":y}
    
    return json.dumps(testdata)