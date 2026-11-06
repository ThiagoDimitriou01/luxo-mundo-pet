#!/usr/bin/env python3
"""Luxo Mundo Pet - projeto acadêmico: e-commerce e atendimento online.
Python 3.10+, somente biblioteca padrão. Não processa pagamentos.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, secrets, hmac, hashlib, html, threading, webbrowser
from datetime import datetime
from pathlib import Path

BASE=Path(__file__).resolve().parent
DB=BASE/"loja.db"
HOST=os.getenv("HOST","127.0.0.1")
PORT=int(os.getenv("PORT","8080"))
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","troque-esta-senha")
STORE_PHONE=os.getenv("STORE_PHONE","") # Ex.: 5511999999999
LOCK=threading.Lock()
SESSIONS={}
def db():
    con=sqlite3.connect(DB, timeout=15)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con
def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products(
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
          price_cents INTEGER NOT NULL CHECK(price_cents>=0),
          stock INTEGER NOT NULL CHECK(stock>=0), description TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS orders(
          id INTEGER PRIMARY KEY, customer TEXT NOT NULL, phone TEXT NOT NULL,
          address TEXT NOT NULL, total_cents INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT 'Recebido', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS order_items(
          id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
          product_id INTEGER NOT NULL, name TEXT NOT NULL,
          qty INTEGER NOT NULL, unit_cents INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS tickets(
          id INTEGER PRIMARY KEY, customer TEXT NOT NULL, contact TEXT NOT NULL,
          subject TEXT NOT NULL, message TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Aberto', created_at TEXT NOT NULL);
        """)
        if not c.execute("SELECT 1 FROM products LIMIT 1").fetchone():
            c.executemany("INSERT INTO products(name,category,price_cents,stock,description) VALUES (?,?,?,?,?)",[
              ("Ração para cães 15 kg (exemplo)","Rações",13500,12,"Produto demonstrativo. Atualize marca, preço e estoque."),
              ("Ração para gatos 10 kg (exemplo)","Rações",11990,8,"Produto demonstrativo."),
              ("Petisco para cães (exemplo)","Petiscos",1890,25,"Produto demonstrativo."),
              ("Sachê para gatos (exemplo)","Sachês",450,40,"Produto demonstrativo."),
              ("Brinquedo para cães (exemplo)","Acessórios",2990,10,"Produto demonstrativo.")
            ])
def esc(s): return html.escape(str(s),quote=True)
def money(cents): return f"R$ {cents/100:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
CSS="""
:root{--bg:#f5f7f9;--ink:#152334;--accent:#096e63;--gold:#e8b85a}
*{box-sizing:border-box}body{margin:0;font:16px system-ui,Arial;background:var(--bg);color:var(--ink)}
header{background:#102b2a;color:white;padding:20px 6%;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
header h1{margin:0;font-size:25px}nav a{color:white;margin-left:16px;text-decoration:none}
main{max-width:1120px;margin:30px auto;padding:0 18px}.hero{padding:36px;border-radius:16px;background:linear-gradient(110deg,#123c38,#147c6d);color:white}
.hero h2{font-size:32px;margin:0 0 10px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:18px;margin:22px 0}
.card,.panel{background:white;padding:22px;border-radius:14px;box-shadow:0 2px 14px #132a2911}.card h3{margin:0 0 10px}
.tag{font-size:12px;color:#176e64;font-weight:700;text-transform:uppercase}.price{font-size:23px;font-weight:750}
button,.btn{border:0;background:var(--accent);color:white;padding:11px 16px;border-radius:8px;cursor:pointer;text-decoration:none;display:inline-block;font-weight:650}
button:hover,.btn:hover{filter:brightness(.9)}button:disabled{background:#999;cursor:not-allowed}
input,textarea,select{width:100%;padding:11px;margin:6px 0 15px;border:1px solid #c9d4d5;border-radius:8px;font:inherit}
label{font-weight:650}table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #dce5e6;padding:10px;text-align:left}
.notice{background:#fff4d8;padding:12px;border-radius:8px;margin:14px 0}footer{text-align:center;padding:30px;color:#526364}
.row{display:flex;gap:16px;flex-wrap:wrap}.row>*{flex:1;min-width:220px}.muted{color:#5b6d70}
@media(max-width:600px){header{display:block}nav{margin-top:14px}nav a{margin:0 14px 0 0}.hero h2{font-size:26px}}
"""
JS=r"""
const KEY="lmp_cart";
function cart(){try{return JSON.parse(localStorage.getItem(KEY)||"{}")}catch{return {}}}
function save(c){localStorage.setItem(KEY,JSON.stringify(c));count()}
function count(){document.querySelectorAll(".cart-count").forEach(e=>e.textContent=Object.values(cart()).reduce((a,b)=>a+Number(b),0))}
function add(id){let c=cart();c[id]=(c[id]||0)+1;save(c);alert("Produto adicionado ao carrinho!")}
function removeItem(id){let c=cart();delete c[id];save(c);renderCart()}
function brl(n){return (n/100).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}
async function renderCart(){
 let box=document.getElementById("cart-items");if(!box)return;
 let p=await (await fetch("/api/products")).json(), c=cart(),total=0;
 let rows=Object.entries(c).map(([id,q])=>{
   let item=p.find(x=>x.id==id);if(!item)return "";
   let n=Math.max(1,Math.min(99,Number(q)||1));total+=item.price_cents*n;
   return `<tr><td>${item.name}</td><td>${n}</td><td>${brl(item.price_cents*n)}</td><td><button onclick="removeItem(${item.id})">Remover</button></td></tr>`;
 }).join("");
 box.innerHTML=rows||'<tr><td colspan="4">Carrinho vazio.</td></tr>';
 document.getElementById("total").textContent=brl(total);
}
async function checkout(ev){
 ev.preventDefault();let c=cart();if(!Object.keys(c).length){alert("Adicione produtos ao carrinho.");return}
 let f=new FormData(ev.target);
 let payload={customer:f.get("customer"),phone:f.get("phone"),address:f.get("address"),
 items:Object.entries(c).map(([product_id,qty])=>({product_id:Number(product_id),qty:Number(qty)}))};
 let r=await fetch("/api/orders",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
 let x=await r.json();document.getElementById("result").textContent=x.message;
 if(r.ok){save({});renderCart();ev.target.reset()}
}
async function support(ev){
 ev.preventDefault();let f=new FormData(ev.target);
 let payload=Object.fromEntries(f.entries());
 let r=await fetch("/api/tickets",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
 let x=await r.json();document.getElementById("support-result").textContent=x.message;
 if(r.ok)ev.target.reset();
}
window.addEventListener("DOMContentLoaded",()=>{count();renderCart()});
"""
def page(title,body):
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | Luxo Mundo Pet</title><style>{CSS}</style></head>
    <body><header><h1>🐾 Luxo Mundo Pet</h1><nav><a href="/">Loja</a><a href="/carrinho">Carrinho (<span class="cart-count">0</span>)</a><a href="/suporte">Suporte online</a><a href="/admin">Admin</a></nav></header><main>{body}</main><footer>Luxo Mundo Pet • Protótipo acadêmico • Pedidos sujeitos à confirmação</footer><script>{JS}</script></body></html>"""
def home():
    with db() as c: products=c.execute("SELECT * FROM products ORDER BY id").fetchall()
    cards="".join(f"""<article class="card"><div class="tag">{esc(p['category'])}</div><h3>{esc(p['name'])}</h3><p class="muted">{esc(p['description'])}</p><p class="price">{money(p['price_cents'])}</p><p>Estoque: {p['stock']}</p><button {'disabled' if p['stock']==0 else ''} onclick="add({p['id']})">Adicionar ao carrinho</button></article>""" for p in products)
    return page("Produtos",f"""<section class="hero"><h2>Seu pet merece carinho em cada pedido.</h2><p>Catálogo digital, solicitação de pedidos e atendimento online.</p><a class="btn" href="/suporte">Falar com a loja</a></section><div class="notice">Demonstração acadêmica: preços e produtos são ilustrativos. Sem pagamento online; pedidos precisam de confirmação pela loja.</div><h2>Nossos produtos</h2><section class="grid">{cards}</section>""")
def cart_page():
    return page("Carrinho","""<h2>Seu carrinho</h2><div class="panel"><table><thead><tr><th>Produto</th><th>Qtd.</th><th>Subtotal</th><th></th></tr></thead><tbody id="cart-items"></tbody></table><h3>Total: <span id="total">R$ 0,00</span></h3></div><h2>Solicitar pedido</h2><form class="panel" onsubmit="checkout(event)"><label>Nome completo<input name="customer" maxlength="100" required></label><label>Telefone/WhatsApp<input name="phone" maxlength="30" required></label><label>Endereço para entrega ou 'Retirada na loja'<textarea name="address" maxlength="300" required></textarea></label><button>Enviar pedido</button><p id="result" role="status"></p></form>""")
def support_page():
    wa=f'<p><a class="btn" target="_blank" rel="noopener" href="https://wa.me/{STORE_PHONE}">Conversar pelo WhatsApp</a></p>' if STORE_PHONE.isdigit() else ""
    return page("Suporte",f"""<h2>Suporte online</h2><p>Envie sua dúvida. A equipe poderá consultar sua solicitação no painel administrativo.</p>{wa}<form class="panel" onsubmit="support(event)"><label>Nome<input name="customer" maxlength="100" required></label><label>Contato (telefone ou e-mail)<input name="contact" maxlength="100" required></label><label>Assunto<input name="subject" maxlength="120" required></label><label>Mensagem<textarea name="message" maxlength="2000" required></textarea></label><button>Enviar solicitação</button><p id="support-result" role="status"></p></form><p class="muted">Este canal registra mensagens; não é um chat em tempo real.</p>""")
def admin_login(message=""):
    return page("Acesso administrativo",f'<h2>Painel administrativo</h2><p class="notice">{esc(message)}</p><form class="panel" method="post" action="/admin/login"><label>Senha de administrador<input type="password" name="password" required></label><button>Entrar</button></form>')
def admin_page():
    with db() as c:
        products=c.execute("SELECT * FROM products ORDER BY id").fetchall()
        orders=c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall()
        tickets=c.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 50").fetchall()
        items=c.execute("SELECT * FROM order_items ORDER BY order_id DESC").fetchall()
    by_order={}
    for x in items:by_order.setdefault(x["order_id"],[]).append(f"{x['qty']}× {esc(x['name'])}")
    prod="".join(f"""<tr><td>{p['id']}</td><td>{esc(p['name'])}</td><td>{money(p['price_cents'])}</td><td>{p['stock']}</td><td><form method="post" action="/admin/stock"><input type="hidden" name="id" value="{p['id']}"><input type="number" name="stock" min="0" max="999999" value="{p['stock']}" required><button>Salvar</button></form></td></tr>""" for p in products)
    orders_html="".join(f"<tr><td>#{o['id']}</td><td>{esc(o['customer'])}<br>{esc(o['phone'])}<br>{esc(o['address'])}</td><td>{', '.join(by_order.get(o['id'],[]))}</td><td>{money(o['total_cents'])}</td><td>{esc(o['created_at'])}</td></tr>" for o in orders)
    tickets_html="".join(f"<tr><td>#{t['id']}</td><td>{esc(t['customer'])}<br>{esc(t['contact'])}</td><td>{esc(t['subject'])}</td><td>{esc(t['message'])}</td><td>{esc(t['created_at'])}</td></tr>" for t in tickets)
    return page("Admin",f"""<h2>Painel administrativo</h2><form action="/admin/logout" method="post"><button>Sair</button></form>
    <h3>Estoque</h3><div class="panel" style="overflow:auto"><table><tr><th>ID</th><th>Produto</th><th>Preço</th><th>Estoque</th><th>Atualizar</th></tr>{prod}</table></div>
    <h3>Cadastrar produto</h3><form class="panel" method="post" action="/admin/product"><div class="row"><label>Nome<input name="name" maxlength="120" required></label><label>Categoria<input name="category" maxlength="80" required></label></div><div class="row"><label>Preço (ex.: 135,90)<input name="price" required></label><label>Quantidade<input type="number" name="stock" min="0" max="999999" required></label></div><label>Descrição<textarea name="description" maxlength="500"></textarea></label><button>Cadastrar</button></form>
    <h3>Pedidos recebidos</h3><div class="panel" style="overflow:auto"><table><tr><th>Número</th><th>Cliente</th><th>Itens</th><th>Total</th><th>Data</th></tr>{orders_html}</table></div>
    <h3>Mensagens de suporte</h3><div class="panel" style="overflow:auto"><table><tr><th>ID</th><th>Cliente</th><th>Assunto</th><th>Mensagem</th><th>Data</th></tr>{tickets_html}</table></div>""")
class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,typ="text/html; charset=utf-8",headers=None):
        raw=body.encode("utf-8") if isinstance(body,str) else body
        self.send_response(status);self.send_header("Content-Type",typ)
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Security-Policy","default-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(raw)
    def data(self):
        n=int(self.headers.get("Content-Length","0"))
        if n<0 or n>100000:raise ValueError("Dados muito grandes")
        return self.rfile.read(n)
    def form(self):return {k:v[0] for k,v in parse_qs(self.data().decode(),keep_blank_values=True).items()}
    def reply(self,status,msg,extra=None):
        self.send(status,json.dumps({"message":msg,**(extra or {})},ensure_ascii=False),"application/json; charset=utf-8")
    def authorized(self):
        from http.cookies import SimpleCookie
        cookie=SimpleCookie()
        try:cookie.load(self.headers.get("Cookie",""))
        except Exception:return False
        token=cookie.get("lmp_session")
        return bool(token and token.value in SESSIONS)
    def redirect(self,path,headers=None):
        self.send(303,b"",headers={"Location":path,**(headers or {})})
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/":self.send(200,home())
        elif path=="/carrinho":self.send(200,cart_page())
        elif path=="/suporte":self.send(200,support_page())
        elif path=="/admin":self.send(200,admin_page() if self.authorized() else admin_login("Entre para consultar pedidos e mensagens."))
        elif path=="/api/products":
            with db() as c:rows=c.execute("SELECT id,name,category,price_cents,stock FROM products").fetchall()
            self.send(200,json.dumps([dict(x) for x in rows],ensure_ascii=False),"application/json; charset=utf-8")
        else:self.send(404,page("Não encontrado","<h2>Página não encontrada</h2>"))
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            if path=="/api/orders":
                x=json.loads(self.data());customer=str(x.get("customer","")).strip();phone=str(x.get("phone","")).strip();address=str(x.get("address","")).strip();items=x.get("items",[])
                if not all([customer,phone,address]) or any(len(s)>n for s,n in [(customer,100),(phone,30),(address,300)]) or not isinstance(items,list) or not 1<=len(items)<=50:raise ValueError("Confira os dados do pedido.")
                normalized={}
                for item in items:
                    pid=int(item["product_id"]);qty=int(item["qty"])
                    if qty<1 or qty>99 or pid in normalized:raise ValueError("Quantidade ou produto inválido.")
                    normalized[pid]=qty
                with LOCK:
                    with db() as c:
                        c.execute("BEGIN IMMEDIATE");total=0;details=[]
                        for pid,qty in normalized.items():
                            p=c.execute("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
                            if not p or p["stock"]<qty:raise ValueError(f"Estoque insuficiente para o produto ID {pid}.")
                            total+=p["price_cents"]*qty;details.append((pid,p["name"],qty,p["price_cents"]))
                        cur=c.execute("INSERT INTO orders(customer,phone,address,total_cents,created_at) VALUES(?,?,?,?,?)",(customer,phone,address,total,datetime.now().isoformat(timespec="seconds")))
                        for pid,name,qty,price in details:
                            c.execute("INSERT INTO order_items(order_id,product_id,name,qty,unit_cents) VALUES(?,?,?,?,?)",(cur.lastrowid,pid,name,qty,price))
                            c.execute("UPDATE products SET stock=stock-? WHERE id=?",(qty,pid))
                self.reply(201,f"Pedido #{cur.lastrowid} registrado! A loja confirmará disponibilidade, entrega e pagamento.",{"order_id":cur.lastrowid})
            elif path=="/api/tickets":
                x=json.loads(self.data());fields=[str(x.get(k,"")).strip() for k in ("customer","contact","subject","message")]
                if not all(fields) or any(len(s)>n for s,n in zip(fields,[100,100,120,2000])):raise ValueError("Preencha todos os campos corretamente.")
                with db() as c:
                    cur=c.execute("INSERT INTO tickets(customer,contact,subject,message,created_at) VALUES(?,?,?,?,?)",(*fields,datetime.now().isoformat(timespec="seconds")))
                self.reply(201,f"Solicitação #{cur.lastrowid} enviada! A loja responderá pelo contato informado.")
            elif path=="/admin/login":
                pwd=self.form().get("password","")
                if not hmac.compare_digest(pwd,ADMIN_PASSWORD):self.send(403,admin_login("Senha incorreta."))
                else:
                    token=secrets.token_urlsafe(32);SESSIONS[token]=True
                    self.redirect("/admin",{"Set-Cookie":f"lmp_session={token}; HttpOnly; SameSite=Strict; Path=/"})
            elif path=="/admin/logout":
                from http.cookies import SimpleCookie
                cookie=SimpleCookie();cookie.load(self.headers.get("Cookie",""))
                if cookie.get("lmp_session"):SESSIONS.pop(cookie["lmp_session"].value,None)
                self.redirect("/admin",{"Set-Cookie":"lmp_session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/"})
            elif path in ("/admin/stock","/admin/product"):
                if not self.authorized():self.send(403,page("Acesso negado","<h2>Acesso negado</h2>"));return
                f=self.form()
                if path=="/admin/stock":
                    pid=int(f["id"]);stock=int(f["stock"])
                    if not 0<=stock<=999999:raise ValueError("Estoque inválido.")
                    with db() as c:c.execute("UPDATE products SET stock=? WHERE id=?",(stock,pid))
                else:
                    name=f.get("name","").strip();category=f.get("category","").strip();desc=f.get("description","").strip()
                    price=f.get("price","").strip().replace(".","").replace(",",".")
                    from decimal import Decimal, InvalidOperation
                    try:
                        amount=Decimal(price)
                        if not amount.is_finite() or amount<0 or amount.as_tuple().exponent < -2:raise ValueError()
                        cents=int(amount*100)
                    except (InvalidOperation,ValueError):raise ValueError("Preço inválido. Use 135,90.")
                    stock=int(f.get("stock","-1"))
                    if not name or not category or len(name)>120 or len(category)>80 or len(desc)>500 or not 0<=stock<=999999 or cents>100000000:raise ValueError("Dados do produto inválidos.")
                    with db() as c:c.execute("INSERT INTO products(name,category,price_cents,stock,description) VALUES(?,?,?,?,?)",(name,category,cents,stock,desc))
                self.redirect("/admin")
            else:self.send(404,page("Não encontrado","<h2>Página não encontrada</h2>"))
        except (ValueError,KeyError,TypeError,UnicodeDecodeError,json.JSONDecodeError) as e:
            msg=str(e) if isinstance(e,ValueError) else "Dados inválidos."
            if path.startswith("/api/"):self.reply(400,msg)
            else:self.send(400,page("Erro",f"<h2>Erro</h2><p>{esc(msg)}</p><a href='/admin'>Voltar</a>"))
        except Exception as e:
            print("Erro interno:",repr(e))
            if path.startswith("/api/"):self.reply(500,"Erro interno no servidor.")
            else:self.send(500,page("Erro","<h2>Erro interno</h2>"))
if __name__=="__main__":
    init()
    print(f"Luxo Mundo Pet: http://{HOST}:{PORT}")
    if ADMIN_PASSWORD=="troque-esta-senha":print("ATENÇÃO: altere ADMIN_PASSWORD antes de usar dados reais.")
    try:ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
    except KeyboardInterrupt:print("\nServidor encerrado.")
