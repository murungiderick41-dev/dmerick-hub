import os, glob, subprocess
from flask import Flask, request, render_template_string, session, send_file
import requests
import urllib.parse, urllib.request, re, json
import datetime, random

app = Flask(__name__)
app.secret_key = "dmerick-hub-secret-123"
os.makedirs("downloads", exist_ok=True)
os.makedirs("static", exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="/static/logo.png">
<link rel="manifest" href="/manifest.json">
<title>Dmerick Hub</title>
<style>
body{font-family:'Segoe UI',Arial,sans-serif;background:#0b0c10;color:#c5c6c7;margin:0;padding:0 0 90px 0}
.app-container{max-width:600px;margin:0 auto;background:#1f2833;min-height:100vh;padding:20px 15px;box-sizing:border-box}
h1{color:#66fcf1;text-align:center;margin:5px 0}
.tagline{color:#45a29e;text-align:center;margin-bottom:15px;font-size:.9rem}
.feature-box{background:#0b0c10;border-radius:12px;padding:15px}
.chat-window{display:flex;flex-direction:column;gap:12px;max-height:55vh;overflow-y:auto;padding:10px 5px}
.bubble{max-width:85%;padding:12px 14px;border-radius:16px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word}
.bubble.user{align-self:flex-end;background:#66fcf1;color:#0b0c10;border-bottom-right-radius:4px}
.bubble.ai{align-self:flex-start;background:#1f2833;border:1px solid #45a29e;color:#e5e7eb;border-bottom-left-radius:4px}
.chat-input-row{display:flex;gap:8px;padding-top:10px}
.chat-input-row input{flex:1;padding:14px;border-radius:25px;border:1px solid #45a29e;background:#1f2833;color:white}
.chat-input-row button{width:60px;border-radius:50%;font-size:1.2rem;background:#66fcf1;border:none}
.mode-select{width:100%;padding:10px;border-radius:8px;background:#1f2833;color:white;border:1px solid #45a29e;margin-bottom:10px}
.display-output{background:#0b0c10;border:none;padding:5px;margin-top:15px;color:#e5e7eb}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#1f2833;border-top:2px solid #45a29e;display:flex;padding:8px 6px 14px 6px;z-index:1000}
.bottom-nav a{color:#c5c6c7;text-decoration:none;font-size:.72rem;display:flex;flex-direction:column;align-items:center;flex:1;padding:6px 4px;border-radius:10px}
.bottom-nav a span.icon{font-size:1.6rem;margin-bottom:3px}
.bottom-nav a.active{color:#66fcf1;background:#0b0c10;border:1px solid #45a29e;font-weight:bold}
button{cursor:pointer}
.game-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.game-grid a button{width:100%;padding:16px;border-radius:10px;border:none;font-weight:bold;font-size:.9rem}
.news-card{background:#1f2833;border:1px solid #2a3a4a;border-radius:12px;padding:12px;margin-bottom:10px}
.news-card h4{color:#66fcf1;margin:0 0 8px 0}
.news-card p{color:#e5e7eb;line-height:1.5}
.logo-head{text-align:center;padding:10px 0}
.logo-head img{width:90px;height:90px;border-radius:20px;object-fit:cover;background:#fff}
</style></head><body>
<div class="app-container">
<div class="logo-head"><img src="/static/logo.png" onerror="this.style.display='none'"><h1>⚡ Dmerick Hub</h1></div>
<div class="tagline">The Ultimate Multi-Platform Utility Engine</div>
<div class="feature-box">
{% if mode=='downloader' %}
<h3 style="color:#66fcf1">📥 Downloader</h3>
<form method="POST" action="/?mode=downloader">
<input style="width:100%;padding:14px;border-radius:8px;background:#1f2833;color:white;border:1px solid #45a29e;box-sizing:border-box" type="url" name="vid_url" placeholder="Paste TikTok, Reel, or Shorts Link..." required>
<button style="width:100%;padding:14px;margin-top:10px;border-radius:8px;background:#66fcf1;border:none;font-weight:bold" type="submit">Download Video ⬇️</button>
</form>
{% if result %}<div class="display-output">{{ result|safe }}</div>{% endif %}
{% elif mode=='ai' %}
<h3 style="color:#66fcf1">🤖 AI Assistant</h3>
<form method="POST" action="/?mode=ai"><select name="ai_type" class="mode-select"><option>💡 General Assistant</option><option>📖 Storyteller</option><option>💻 Code Assistant</option></select>
<div class="chat-window" id="chatWin">{% for msg in chat_history %}<div class="bubble {{msg.role}}">{{msg.text}}</div>{% endfor %}{% if not chat_history %}<div class="bubble ai">Hello! I'm your Dmerick AI. Ask me anything... ✨</div>{% endif %}</div>
<div class="chat-input-row"><input type="text" name="ai_prompt" placeholder="Message..." required autocomplete="off"><button type="submit">➤</button></div></form>
<form method="POST" action="/?mode=ai&action=clear"><button style="width:100%;margin-top:8px;background:transparent;border:1px solid #ff4444;color:#ff4444;padding:6px;border-radius:8px" type="submit">Clear Chat</button></form>
<script>var w=document.getElementById('chatWin');w.scrollTop=w.scrollHeight;</script>
{% elif mode=='games' %}
<h3 style="color:#66fcf1">🎮 Trending Games</h3>
<div class="game-grid">
<a href="/?mode=games&play=bubble"><button style="background:#66fcf1">🫧 Bubble Shooter</button></a>
<a href="/?mode=games&play=runner"><button style="background:#ff6b9d;color:white">👸 Princess Runner</button></a>
<a href="/?mode=games&play=brain"><button style="background:#9d4edd;color:white">🧠 Brain Games</button></a>
<a href="/?mode=games&play=race"><button style="background:#ff9e00">🏎️ Turbo Racing</button></a>
</div>
{% set gp = request.args.get('play','bubble') %}
{% if gp=='bubble' %}
<div style="text-align:center;background:#1f2833;padding:12px;border-radius:10px"><canvas id="bb" width="300" height="400" style="background:#0b0c10;border-radius:8px;max-width:100%"></canvas><p style="color:#66fcf1;font-size:.8rem">Tap to shoot • Match colors</p><p id="bbs" style="color:white">Score: 0</p></div>
<script>let c1=document.getElementById('bb'),x1=c1.getContext('2d'),bubbles=[],scoreB=0,cols=['#ff6b9d','#66fcf1','#ffeb3b','#9d4edd','#00ff88'];for(let r=0;r<4;r++)for(let i=0;i<8;i++)bubbles.push({x:20+i*34+(r%2)*17,y:30+r*30,col:cols[Math.floor(Math.random()*5)]});let cur={x:150,y:380,vx:0,vy:0,col:cols[0],fly:false};cur.col=cols[Math.floor(Math.random()*5)];c1.onclick=e=>{if(cur.fly)return;let rc=c1.getBoundingClientRect();let ang=Math.atan2(e.clientY-rc.top-cur.y,e.clientX-rc.left-cur.x);cur.vx=Math.cos(ang)*6;cur.vy=Math.sin(ang)*6;cur.fly=true;};(function loopBB(){x1.clearRect(0,0,300,400);bubbles.forEach(b=>{x1.fillStyle=b.col;x1.beginPath();x1.arc(b.x,b.y,14,0,7);x1.fill();});if(cur.fly){cur.x+=cur.vx;cur.y+=cur.vy;if(cur.x<14||cur.x>286)cur.vx*=-1;let hi=bubbles.findIndex(b=>Math.hypot(b.x-cur.x,b.y-cur.y)<28);if(hi>-1||cur.y<20){if(hi>-1&&bubbles[hi].col===cur.col){bubbles.splice(hi,1);scoreB+=10;document.getElementById('bbs').innerText='Score: '+scoreB;}else bubbles.push({x:cur.x,y:cur.y,col:cur.col});cur={x:150,y:380,vx:0,vy:0,col:cols[Math.floor(Math.random()*5)],fly:false};}}x1.fillStyle=cur.col;x1.beginPath();x1.arc(cur.x,cur.y,14,0,7);x1.fill();requestAnimationFrame(loopBB);})();</script>
{% elif gp=='runner' %}
<div style="text-align:center;background:#1f2833;padding:12px;border-radius:10px"><canvas id="rn" width="300" height="400" style="background:#16213e;border-radius:8px;max-width:100%"></canvas><p style="color:#66fcf1">Tap = Jump</p><p id="rns" style="color:white">Score: 0</p></div>
<script>let rc2=document.getElementById('rn'),rx=rc2.getContext('2d'),py=320,pvy=0,jump=false,obst=[],rscore=0,aliveR=true;rc2.onclick=()=>{if(!jump){pvy=-12;jump=true;}};setInterval(()=>{if(aliveR)obst.push({x:300,y:330});},1200);(function loopR(){if(!aliveR)return;rx.clearRect(0,0,300,400);pvy+=0.6;py+=pvy;if(py>320){py=320;pvy=0;jump=false;}rscore++;document.getElementById('rns').innerText='Score: '+Math.floor(rscore/10);rx.fillStyle='#ff6b9d';rx.fillRect(130,py,30,40);rx.fillStyle='#ffd700';rx.beginPath();rx.arc(145,py-5,10,0,7);rx.fill();rx.fillStyle='#45a29e';obst.forEach(o=>{o.x-=4;rx.fillRect(o.x,o.y,50,30);if(o.x>100&&o.x<170&&py>290){aliveR=false;rx.fillStyle='white';rx.font='16px Arial';rx.fillText('Game Over! Tap to restart',40,200);rc2.onclick=()=>location.reload();}});obst=obst.filter(o=>o.x>-60);requestAnimationFrame(loopR);})();</script>
{% elif gp=='brain' %}
<div style="background:#1f2833;padding:20px;border-radius:10px;text-align:center"><h4 style="color:#9d4edd">🧠 Quick Math</h4><p id="bq" style="font-size:2rem;color:white"></p><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px" id="ba"></div><p id="bsc" style="color:#66fcf1">Score: 0</p></div>
<script>let bscore=0;function newQ(){let a=Math.floor(Math.random()*20)+1,b=Math.floor(Math.random()*20)+1,ans=a+b;document.getElementById('bq').innerText=a+' + '+b+' =?';let opts=[ans,ans+2,ans-2,ans+5].sort(()=>Math.random()-0.5);let el=document.getElementById('ba');el.innerHTML='';opts.forEach(o=>{let btn=document.createElement('button');btn.style.cssText='padding:15px;font-size:1.2rem;border-radius:10px;border:none;background:#0b0c10;color:white;border:1px solid #9d4edd';btn.innerText=o;btn.onclick=()=>{if(o===ans)bscore+=10;else bscore=Math.max(0,bscore-5);document.getElementById('bsc').innerText='Score: '+bscore;newQ();};el.appendChild(btn);});}newQ();</script>
{% elif gp=='race' %}
<div style="text-align:center;background:#1f2833;padding:12px;border-radius:10px"><canvas id="tr" width="300" height="400" style="background:#2a2a2a;border-radius:8px;max-width:100%"></canvas><p style="color:#66fcf1">Tap left / right to steer</p></div>
<script>let tc=document.getElementById('tr'),tx=tc.getContext('2d'),rx2=130,enn=[],aliveT=true;tc.onclick=e=>{let r=tc.getBoundingClientRect();rx2+= (e.clientX-r.left<150?-25:25);rx2=Math.max(20,Math.min(240,rx2));};setInterval(()=>{if(aliveT)enn.push({x:[40,130,220][Math.floor(Math.random()*3)],y:-60});},900);(function loopT(){if(!aliveT)return;tx.clearRect(0,0,300,400);tx.fillStyle='#444';tx.fillRect(30,0,240,400);tx.fillStyle='white';for(let y=0;y<400;y+=40)tx.fillRect(148,y,4,20);tx.fillStyle='#ff9e00';tx.fillRect(rx2,300,40,60);tx.fillStyle='#ff0000';enn.forEach(o=>{o.y+=5;tx.fillRect(o.x,o.y,40,60);if(o.y>280&&o.y<360&&Math.abs(o.x-rx2)<35){aliveT=false;tx.fillStyle='white';tx.font='16px Arial';tx.fillText('Crash! Tap to restart',70,200);tc.onclick=()=>location.reload();}});enn=enn.filter(o=>o.y<450);requestAnimationFrame(loopT);})();</script>
{% endif %}
{% elif mode=='pulse' %}
<h3 style="color:#66fcf1">📈 Daily Pulse</h3>
<form method="GET" action="/"><input type="hidden" name="mode" value="pulse"><input name="q" placeholder="Search world news..." value="{{request.args.get('q','')}}" style="width:100%;padding:12px;border-radius:8px;background:#1f2833;color:white;border:1px solid #45a29e;box-sizing:border-box"><button style="width:100%;padding:12px;margin-top:8px;border-radius:8px;background:#66fcf1;border:none;font-weight:bold">Search News 🌍</button></form>
<a href="/?mode=pulse&fetch=true"><button style="width:100%;padding:14px;margin-top:8px;border-radius:8px;background:transparent;border:1px solid #66fcf1;color:#66fcf1">Load Fresh Daily Brief ✨</button></a>
{% if result %}<div class="display-output">{{result|safe}}</div>{% endif %}
{% endif %}
</div></div>
<div class="bottom-nav">
<a href="/?mode=downloader" class="{{'active' if mode=='downloader' else ''}}"><span class="icon">📥</span>Downloader</a>
<a href="/?mode=ai" class="{{'active' if mode=='ai' else ''}}"><span class="icon">🤖</span>AI Assistant</a>
<a href="/?mode=games&play=bubble" class="{{'active' if mode=='games' else ''}}"><span class="icon">🎮</span>Social Games</a>
<a href="/?mode=pulse" class="{{'active' if mode=='pulse' else ''}}"><span class="icon">📈</span>Daily Pulse</a>
</div></body></html>
"""

def call_gemini_api(prompt_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY missing."
    models = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]
    last_err = "unknown"
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            r = requests.post(url, params={'key': api_key}, json={"contents": [{"parts": [{"text": prompt_text}]}]}, headers={'Content-Type': 'application/json'}, timeout=30)
            j = r.json()
            if r.status_code == 200 and 'candidates' in j:
                return j['candidates'][0]['content']['parts'][0]['text'].replace("**","").strip()
            else:
                last_err = f"{model}: {r.status_code} {str(j)[:300]}"
        except Exception as e:
            last_err = f"{model} exception: {e}"
            continue
    return f"AI error: {last_err}"

def clean_url(u):
    if not u: return ""
    u = u.strip().split()[0]
    if u.startswith("vm.tiktok") or u.startswith("vt.tiktok"):
        u = "https://"+u
    return u

@app.route("/download-file")
def download_file():
    fname = request.args.get("f","")
    safe_path = os.path.join("downloads", os.path.basename(fname))
    if os.path.exists(safe_path):
        return send_file(safe_path, as_attachment=True)
    return "File expired, download again."

@app.route("/manifest.json")
def manifest():
    return {"name":"Dmerick Hub","short_name":"Dmerick","display":"standalone","icons":[{"src":"/static/logo.png","sizes":"512x512","type":"image/png"}]}

@app.route("/read")
def read_article():
    url = request.args.get("url","")
    if not url: return "No URL"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        if "news.google.com" in url:
            g_html = requests.get(url, headers=headers, timeout=12).text
            links = re.findall(r'"(https://[^"]+)"', g_html)
            for l in links:
                if "google.com" not in l and "gstatic" not in l and len(l) > 20:
                    url = l
                    break
        html = requests.get(url, headers=headers, timeout=12).text
        m_title = re.search(r'<meta property="og:title" content="(.*?)"', html) or re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        title = m_title.group(1) if m_title else "News Article"
        m_img = re.search(r'<meta property="og:image" content="(.*?)"', html)
        img = m_img.group(1) if m_img else ""
        paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)[:25]
        clean_paras = []
        for p in paras:
            t = re.sub(r'<[^>]+>', '', p).strip()
            if len(t) > 80 and "cookie" not in t.lower() and "subscribe" not in t.lower():
                clean_paras.append(f"<p>{t}</p>")
            if len(clean_paras)>=8: break
        body = "".join(clean_paras) if clean_paras else "<p><i>Preview not available. Tap Open Original for full story.</i></p>"
        img_tag = f"<img src='{img}' style='width:100%;border-radius:12px;margin:10px 0'>" if img and img.startswith("http") else ""
        return f"""<div style="max-width:600px;margin:0 auto;background:#0b0c10;min-height:100vh;padding:15px;font-family:Arial;color:#e5e7eb"><a href="/?mode=pulse" style="color:#66fcf1;text-decoration:none">← Back</a><h2 style="color:white;line-height:1.3">{title[:200]}</h2>{img_tag}<div style="line-height:1.7;font-size:1rem">{body}</div><a href="{url}" target="_blank" style="display:block;margin:20px 0;padding:14px;text-align:center;background:#66fcf1;color:#0b0c10;border-radius:10px;font-weight:bold;text-decoration:none">Open Original ↗</a><div style="height:80px"></div></div>"""
    except Exception as e:
        return f"<p>Could not load preview: {e}</p><a href='{url}' target='_blank'>Open original</a>"

def build_cards(raw_items):
    cards = ""
    for title, link, source, pubdate in raw_items:
        title_clean = re.sub(r'<[^>]+>', '', title)[:140].strip()
        if not title_clean: continue
        domain = urllib.parse.urlparse(link).netloc
        # Use Google News icon like in your image 3 for consistency
        img = "https://upload.wikimedia.org/wikipedia/commons/d/d6/Google_News_icon.png"
        # fallback to favicon if not google news link
        if "news.google.com" not in link and domain:
            img = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
        short_date = pubdate[5:16] if len(pubdate)>16 else pubdate[:16]
        read_url = "/read?url=" + urllib.parse.quote(link, safe='')
        cards += f"""<a href='{read_url}' style='text-decoration:none'><div class='news-card'><div style='display:flex;gap:10px;align-items:flex-start'><img src='{img}' style='width:42px;height:42px;border-radius:8px;background:#fff;object-fit:contain;flex-shrink:0'><div><div style='color:white;font-weight:bold;font-size:.9rem;line-height:1.3'>{title_clean}</div><div style='color:#45a29e;font-size:.75rem;margin-top:4px'>{source} • {short_date}</div></div></div></div></a>"""
    return cards

@app.route("/", methods=["GET","POST"])
def home():
    mode = request.args.get("mode","downloader")
    result = None
    if 'chat_history' not in session: session['chat_history'] = []
    if mode=="ai" and request.args.get("action")=="clear" and request.method=="POST":
        session['chat_history']=[]; session.modified=True
    elif mode=="ai" and request.method=="POST" and request.args.get("action")!="clear":
        p = request.form.get("ai_prompt","").strip()
        t = request.form.get("ai_type","General Assistant")
        if p:
            session['chat_history'].append({"role":"user","text":p})
            reply = call_gemini_api(f"Role:{t}. No ** markdown. Input:{p}")
            session['chat_history'].append({"role":"ai","text":reply})
            session['chat_history'] = session['chat_history'][-20:]
            session.modified=True
    elif mode=="downloader" and request.method=="POST":
        link = clean_url(request.form.get("vid_url","").strip())
        try:
            for f in glob.glob("downloads/*"): os.remove(f)
            cmd = ["yt-dlp","-f","mp4/best","-o","downloads/%(title).30s.%(ext)s","--no-playlist","--max-filesize","50m",link]
            subprocess.run(cmd, timeout=120, check=True)
            files = glob.glob("downloads/*")
            if files:
                fname = os.path.basename(files[0])
                result = f"✅ Done!<br><a href='/download-file?f={urllib.parse.quote(fname)}' style='font-weight:bold;font-size:1.2rem'>⬇️ TAP TO SAVE VIDEO</a><br><small>{fname}</small>"
            else:
                result = "❌ Could not extract."
        except Exception as e:
            result = f"❌ Failed: {str(e)[:200]}"
    elif mode=="pulse":
        def fetch_google_news(search_q=None):
            if search_q:
                q = urllib.parse.quote(search_q)
                rss_url = f"https://news.google.com/rss/search?q={q}%20when:7d&hl=en-US&gl=US&ceid=US:en"
            else:
                rss_url = "https://news.google.com/rss/search?q=top%20world%20news%20when:1d&hl=en-US&gl=US&ceid=US:en"
            try:
                data = urllib.request.urlopen(rss_url, timeout=12).read().decode(errors='ignore')
                items = re.findall(r'<item>(.*?)</item>', data, re.DOTALL)[:12]
                out = []
                for it in items:
                    tm = re.search(r'<title>(.*?)</title>', it, re.DOTALL)
                    lm = re.search(r'<link>(.*?)</link>', it, re.DOTALL)
                    sm = re.search(r'<source[^>]*>(.*?)</source>', it, re.DOTALL)
                    dm = re.search(r'<pubDate>(.*?)</pubDate>', it, re.DOTALL)
                    if not tm or not lm: continue
                    title = re.sub(r'<[^>]+>', '', tm.group(1)).strip()
                    source = re.sub(r'<[^>]+>', '', sm.group(1)).strip() if sm else "World News"
                    link = lm.group(1).strip()
                    pubdate = dm.group(1).strip() if dm else ""
                    out.append((title, link, source, pubdate))
                return out
            except Exception as e:
                print("news error", e)
                return []
        if request.args.get("fetch")=="true":
            today = datetime.date.today().isoformat()
            rnd = random.randint(1,99999)
            ai_text = call_gemini_api(f"Today is {today}, seed {rnd}. Give 1 NEW surprising world fact, 1 fresh funny joke, 1 practical life tip. Must be unique every time. No **.")
            result = f"<div class='news-card'><h4>✨ AI Daily Brief - {today}</h4><p>{ai_text}</p></div>"
        elif request.args.get("q"):
            q = request.args.get("q").strip()
            raw_items = fetch_google_news(q)
            result = f"<div style='color:#45a29e;font-size:.8rem;margin:10px 0'>🌍 Results for '{q}'</div>" + build_cards(raw_items) if raw_items else f"No results for '{q}'. Check internet."
        else:
            raw_items = fetch_google_news(None)
            result = "<div style='color:#45a29e;font-size:.8rem;margin:10px 0'>🌍 Top World Stories</div>" + build_cards(raw_items) if raw_items else "Connect to internet to load news."
    return render_template_string(HTML_TEMPLATE, mode=mode, result=result, chat_history=session.get('chat_history',[]), request=request)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
