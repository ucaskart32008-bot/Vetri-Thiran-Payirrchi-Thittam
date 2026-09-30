import json,re
from urllib.parse import quote_plus
from google import genai
from google.genai import types
from app.config import settings
PLATFORMS={"Amazon":"https://www.amazon.in/s?k=","Flipkart":"https://www.flipkart.com/search?q=","IKEA":"https://www.ikea.com/in/en/search/?q=","Swiggy":"https://www.swiggy.com/search?query=","Zomato":"https://www.zomato.com/","OYO":"https://www.oyorooms.com/search/?query="}
def fallback(planner,d):
    b=int(d["budget"])
    rowspec=([("Lighting",.12,"LED ceiling lights","Amazon"),("Furniture",.38,"compact sofa or dining set","IKEA"),("Storage",.18,"modular storage","Flipkart"),("Decor",.17,"wall art and soft furnishings","Amazon"),("Reserve",.15,"installation and contingency","Amazon")] if planner=="home" else [("Food",.40,"catering and meal packages","Swiggy"),("Venue",.25,"event venue or stay","OYO"),("Decoration",.15,"event backdrop and flowers","Amazon"),("Entertainment",.12,"music and activities","Amazon"),("Reserve",.08,"contingency","Amazon")] if planner=="party" else [("Earrings",.30,"occasion earrings","Flipkart"),("Necklace",.35,"matching necklace","Amazon"),("Bangles",.20,"minimal bangles","Flipkart"),("Reserve",.15,"delivery or alterations","Amazon")])
    items=[{"category":c,"suggestion":s,"estimated_cost":round(b*p),"platform":v,"url":PLATFORMS[v]+quote_plus(s)} for c,p,s,v in rowspec]
    return {"title":f"{d.get('event_type',d.get('occasion','Home'))} plan","summary":"Starter allocation. Confirm current prices, stock, provider terms and delivery directly.","currency":"INR","total_estimated":sum(x["estimated_cost"] for x in items),"items":items,"source":"demo_fallback"}
def parse_json(s):
    s=re.sub(r"^```(?:json)?\\s*|\\s*```$","",s.strip(),flags=re.I)
    a,b=s.find("{"),s.rfind("}")
    if a<0 or b<a: raise ValueError("Model did not return JSON")
    return json.loads(s[a:b+1])
def generate(planner,data,image_bytes=None,mime=None):
    if not settings.gemini_api_key:return fallback(planner,data)
    prompt=("You are PocketSmart AI, a practical budget planner for India. Return only valid JSON with title, summary, currency, total_estimated, items. Include 4-7 item objects with category, suggestion, estimated_cost integer INR, platform (Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO), search_term. Never claim live stock or verified prices. Sum costs within budget. User planner: "+planner+"; data: "+json.dumps(data,ensure_ascii=False))
    try:
        client=genai.Client(api_key=settings.gemini_api_key); contents=[prompt]
        if image_bytes: contents.append(types.Part.from_bytes(data=image_bytes,mime_type=mime or "image/jpeg"))
        out=client.models.generate_content(model=settings.gemini_model,contents=contents)
        raw=parse_json(out.text or ""); items=[]
        for x in raw.get("items",[])[:7]:
            platform=x.get("platform","Amazon")
            if platform not in PLATFORMS:platform="Amazon"
            term=str(x.get("search_term") or x.get("suggestion") or "budget products")
            items.append({"category":str(x.get("category","Option"))[:80],"suggestion":str(x.get("suggestion",""))[:300],"estimated_cost":max(0,int(float(x.get("estimated_cost",0)))),"platform":platform,"url":PLATFORMS[platform]+quote_plus(term)})
        if not items:return fallback(planner,data)
        total=sum(x["estimated_cost"] for x in items)
        if total>data["budget"]:
            factor=data["budget"]/total
            for x in items:x["estimated_cost"]=int(x["estimated_cost"]*factor)
            total=sum(x["estimated_cost"] for x in items)
        return {"title":str(raw.get("title","Your plan"))[:200],"summary":str(raw.get("summary",""))[:1000],"currency":"INR","total_estimated":total,"items":items,"source":"gemini"}
    except Exception:return fallback(planner,data)
