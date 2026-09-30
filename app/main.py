import json
from pathlib import Path
from fastapi import FastAPI,Depends,HTTPException,Request,UploadFile,File,Form
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from jose import jwt
from app.config import settings
from app.database import Base,engine,get_db
from app.models import User,Recommendation
from app.schemas import RegisterIn,UserOut,HomeIn,PartyIn
from app.security import hash_password,verify_password,create_token,get_current_user
from app.services.recommender import generate
Base.metadata.create_all(bind=engine)
app=FastAPI(title=settings.app_name,version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:8000","http://localhost:8000"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
BASE=Path(__file__).resolve().parent
templates=Jinja2Templates(directory=str(BASE/"templates"))
app.mount("/static",StaticFiles(directory=str(BASE/"static")),name="static")
def ui_user(req,db):
    try:return db.get(User,int(jwt.decode(req.cookies["pocketsmart_token"],settings.secret_key,algorithms=["HS256"])["sub"]))
    except Exception:return None
def save(db,user,planner,data,result):
    rec=Recommendation(user_id=user.id,planner=planner,title=result["title"],budget=data["budget"],input_json=json.dumps(data),result_json=json.dumps(result))
    db.add(rec);db.commit();db.refresh(rec);result["history_id"]=rec.id;return result
@app.get("/",response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )
@app.get("/health")
def health():return {"status":"ok","ai_configured":bool(settings.gemini_api_key)}
@app.post("/api/auth/register",response_model=UserOut)
def register(p:RegisterIn,db:Session=Depends(get_db)):
    email=p.email.lower()
    if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,"Email already registered")
    u=User(name=p.name.strip(),email=email,password_hash=hash_password(p.password));db.add(u);db.commit();db.refresh(u);return u
@app.post("/api/auth/login")
def login(request:Request,db:Session=Depends(get_db),username:str=Form(...),password:str=Form(...)):
    u=db.scalar(select(User).where(User.email==username.lower()))
    if not u or not verify_password(password,u.password_hash):raise HTTPException(401,"Incorrect email or password")
    token=create_token(u.id)
    if request.headers.get("x-ui-login")=="1":
        r=RedirectResponse("/dashboard",status_code=303);r.set_cookie("pocketsmart_token",token,httponly=True,samesite="lax",secure=False,max_age=settings.access_token_minutes*60);return r
    return {"access_token":token,"token_type":"bearer"}
@app.post("/api/auth/logout")
def logout():
    r=RedirectResponse("/",status_code=303);r.delete_cookie("pocketsmart_token");return r
@app.get("/api/auth/me",response_model=UserOut)
def me(u:User=Depends(get_current_user)):return u
@app.get("/api/session-info")
def session(request:Request,db:Session=Depends(get_db)):
    u=ui_user(request,db);return {"authenticated":bool(u),"user":{"id":u.id,"name":u.name,"email":u.email} if u else None}
@app.post("/api/generate-home")
def home_plan(p:HomeIn,u:User=Depends(get_current_user),db:Session=Depends(get_db)):
    d=p.model_dump();return save(db,u,"home",d,generate("home",d))
@app.post("/api/generate-party")
def party_plan(p:PartyIn,u:User=Depends(get_current_user),db:Session=Depends(get_db)):
    d=p.model_dump();return save(db,u,"party",d,generate("party",d))
@app.post("/api/generate-jewelry")
async def jewelry(budget:int=Form(...,gt=0),occasion:str=Form(...,min_length=2),style:str=Form("Elegant"),notes:str=Form(""),outfit_image:UploadFile|None=File(None),u:User=Depends(get_current_user),db:Session=Depends(get_db)):
    if budget>100000000:raise HTTPException(422,"Budget is too high")
    raw=None;mime=None
    if outfit_image and outfit_image.filename:
        mime=outfit_image.content_type or ""
        if mime not in ("image/jpeg","image/png","image/webp"):raise HTTPException(415,"Upload JPG, PNG or WebP")
        raw=await outfit_image.read()
        if len(raw)>settings.max_upload_mb*1024*1024:raise HTTPException(413,"Image exceeds upload limit")
    d={"budget":budget,"occasion":occasion,"style":style,"notes":notes,"image_provided":bool(raw)}
    return save(db,u,"jewelry",d,generate("jewelry",d,raw,mime))
@app.get("/api/history")
def history(u:User=Depends(get_current_user),db:Session=Depends(get_db)):
    rs=db.scalars(select(Recommendation).where(Recommendation.user_id==u.id).order_by(Recommendation.created_at.desc()).limit(100)).all()
    return [{"id":r.id,"planner":r.planner,"title":r.title,"budget":r.budget,"created_at":r.created_at.isoformat()} for r in rs]
@app.get("/api/history/{rid}")
def detail(rid:int,u:User=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.scalar(select(Recommendation).where(Recommendation.id==rid,Recommendation.user_id==u.id))
    if not r:raise HTTPException(404,"History item not found")
    return {"id":r.id,"planner":r.planner,"input":json.loads(r.input_json),"result":json.loads(r.result_json)}
@app.delete("/api/history/{rid}")
def delete(rid:int,u:User=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.scalar(select(Recommendation).where(Recommendation.id==rid,Recommendation.user_id==u.id))
    if not r:raise HTTPException(404,"History item not found")
    db.delete(r);db.commit();return {"deleted":True}
@app.get("/api/recommendations-details/{rid}")
def recommendation_details(rid:int,u:User=Depends(get_current_user),db:Session=Depends(get_db)):return detail(rid,u,db)
@app.get("/dashboard",response_class=HTMLResponse)
def dashboard(request:Request,db:Session=Depends(get_db)):
    u=ui_user(request,db)
    if not u:return RedirectResponse("/",303)
    return templates.TemplateResponse(
    request=request,
    name="dashboard.html",
    context={"user": user}
)
@app.get("/history",response_class=HTMLResponse)
def history_page(request:Request,db:Session=Depends(get_db)):
    u=ui_user(request,db)
    if not u:return RedirectResponse("/",303)
    return templates.TemplateResponse("history.html",{"request":request,"user":u})
@app.get("/planner/{planner}",response_class=HTMLResponse)
def planner_page(planner:str,request:Request,db:Session=Depends(get_db)):
    if planner not in ("home","party","jewelry"):raise HTTPException(404,"Planner not found")
    u=ui_user(request,db)
    if not u:return RedirectResponse("/",303)
    return templates.TemplateResponse("planner.html",{"request":request,"user":u,"planner":planner})
@app.get("/startup")
def startup():return {"ready":True,"database":"connected","gemini_configured":bool(settings.gemini_api_key)}
