from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio
import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

async def repondre_avec_mistral(question: str) -> str:
    """Appel à l'API Mistral avec prompt optimisé"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MISTRAL_URL,
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-tiny",
                    "messages": [
                        {
                            "role": "system",
                            "content": """Tu es un professeur d'informatique. Regles strictes :
1. Reponses COURTES (max 150 mots)
2. PRECISES et factuelles
3. PEDAGOGIQUES : utilise une analogie simple
4. Structure : definition + analogie + exemple
5. Termine par une question ouverte
6. Pas de bla-bla, va droit au but
7. Si l'utilisateur dit "pas compris", reformule avec une analogie DIFFERENTE"""
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ],
                    "temperature": 0.5,
                    "max_tokens": 400
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            return f"Erreur: {response.status_code}"
    except Exception as e:
        return f"Erreur: {str(e)}"

async def generate_stream(question: str):
    yield f"data: {json.dumps({'type': 'start'})}\n\n"
    await asyncio.sleep(0.05)
    
    yield f"data: {json.dumps({'type': 'thinking', 'content': '...'})}\n\n"
    await asyncio.sleep(0.2)
    
    reponse = await repondre_avec_mistral(question)
    
    for char in reponse:
        yield f"data: {json.dumps({'type': 'chunk', 'content': char})}\n\n"
        await asyncio.sleep(0.015)
    
    yield f"data: {json.dumps({'type': 'end'})}\n\n"

@app.get("/")
async def root():
    html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Professeur Informatique</title>
    <meta charset="UTF-8">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Segoe UI,Roboto,sans-serif;background:#e9ecef;height:100vh;display:flex;justify-content:center;align-items:center}
        .container{width:95%;max-width:900px;height:90vh;background:white;border-radius:12px;display:flex;flex-direction:column;overflow:hidden}
        .header{background:#1a1a2e;color:white;padding:16px}
        .header h1{font-size:1.2rem}
        .badge{background:#2c2c54;display:inline-block;padding:2px 10px;border-radius:12px;font-size:0.65rem;margin-top:8px}
        .chat{flex:1;overflow:auto;padding:20px;background:#f8f9fa}
        .message{display:flex;margin-bottom:16px}
        .user{justify-content:flex-end}
        .bot{justify-content:flex-start}
        .bubble{max-width:75%;padding:10px 14px;border-radius:16px;line-height:1.4;white-space:pre-wrap}
        .user .bubble{background:#1a1a2e;color:white}
        .bot .bubble{background:white;border:1px solid #dee2e6}
        .time{font-size:0.6rem;margin-top:4px;opacity:0.6}
        .input-area{display:flex;padding:16px;background:white;border-top:1px solid #dee2e6;gap:10px}
        input{flex:1;padding:10px;border:1px solid #dee2e6;border-radius:24px;outline:none}
        input:focus{border-color:#1a1a2e}
        button{padding:10px 20px;background:#1a1a2e;color:white;border:none;border-radius:24px;cursor:pointer}
        .suggestions{display:flex;gap:8px;padding:10px;background:#f8f9fa;flex-wrap:wrap}
        .suggestion{padding:4px 12px;background:white;border:1px solid #dee2e6;border-radius:16px;cursor:pointer;font-size:0.75rem}
        .suggestion:hover{background:#1a1a2e;color:white}
        .cursor{display:inline-block;width:2px;height:1em;background:#1a1a2e;animation:blink 1s infinite;margin-left:2px}
        @keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}
        .thinking{font-style:italic;color:#6c757d}
    </style>
</head>
<body>
<div class="container">
<div class="header">
<h1>Professeur Informatique</h1>
<div class="badge">Mistral-7B | Reponses courtes et precises</div>
</div>
<div class="suggestions">
<span class="suggestion" onclick="ask('C\'est quoi un ordinateur ?')">Ordinateur</span>
<span class="suggestion" onclick="ask('C\'est quoi un processeur ?')">Processeur</span>
<span class="suggestion" onclick="ask('C\'est quoi la RAM ?')">RAM</span>
<span class="suggestion" onclick="ask('C\'est quoi l\'IA ?')">IA</span>
<span class="suggestion" onclick="ask('J\'ai pas compris')">Reformuler</span>
</div>
<div class="chat" id="chat">
<div class="message bot">
<div class="bubble">Bonjour. Posez votre question sur l'informatique. Je reponds de maniere courte et claire.</div>
</div>
</div>
<div class="input-area">
<input type="text" id="input" placeholder="Votre question...">
<button onclick="send()">Envoyer</button>
</div>
</div>
<script>
let isStreaming=false;const chat=document.getElementById('chat');const input=document.getElementById('input');
function ask(q){input.value=q;send();}
async function send(){
if(isStreaming)return;
const question=input.value.trim();
if(!question)return;
addMessage(question,'user');
input.value='';
isStreaming=true;
const tempDiv=document.createElement('div');
tempDiv.className='message bot';
tempDiv.id='tempMsg';
const bubble=document.createElement('div');
bubble.className='bubble';
bubble.innerHTML='<span class="cursor"></span>';
tempDiv.appendChild(bubble);
chat.appendChild(tempDiv);
chat.scrollTop=chat.scrollHeight;
try{
const response=await fetch('/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:question})});
const reader=response.body.getReader();
const decoder=new TextDecoder();
let text='';
while(true){
const{done,value}=await reader.read();
if(done)break;
const chunk=decoder.decode(value);
const lines=chunk.split('\\n');
for(const line of lines){
if(line.startsWith('data: ')){
const data=JSON.parse(line.slice(6));
if(data.type==='chunk'){
text+=data.content;
bubble.innerHTML=text.replace(/\\n/g,'<br>')+'<span class="cursor"></span>';
chat.scrollTop=chat.scrollHeight;
}else if(data.type==='thinking'){
bubble.innerHTML='<span class="thinking">'+data.content+'</span>';
}else if(data.type==='end'){
bubble.innerHTML=text.replace(/\\n/g,'<br>');
const timeDiv=document.createElement('div');
timeDiv.className='time';
timeDiv.textContent=new Date().toLocaleTimeString();
bubble.appendChild(timeDiv);
}
}
}
}
}catch(e){bubble.innerHTML='Erreur';}
finally{isStreaming=false;const temp=document.getElementById('tempMsg');if(temp)temp.removeAttribute('id');input.focus();}
}
function addMessage(text,sender){
const div=document.createElement('div');
div.className='message '+sender;
div.innerHTML='<div class="bubble">'+escapeHtml(text)+'<div class="time">'+new Date().toLocaleTimeString()+'</div></div>';
chat.appendChild(div);
chat.scrollTop=chat.scrollHeight;
}
function escapeHtml(t){const div=document.createElement('div');div.textContent=t;return div.innerHTML;}
input.addEventListener('keypress',(e)=>{if(e.key==='Enter')send();});
</script>
</body>
</html>'''
    return HTMLResponse(html)

@app.post("/stream")
async def stream(request: Request):
    data = await request.json()
    question = data.get("question", "")
    return StreamingResponse(
        generate_stream(question),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.get("/health")
async def health():
    return {"status": "ok", "model": "mistral-tiny"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
