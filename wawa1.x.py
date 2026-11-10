#!/usr/bin/env python3
"""Wa Waa Engine 0.1.1.1 - single-file Tkinter 2D game editor.
© AC Kondo 1999–2026
No third-party dependencies. Projects live in memory unless explicitly saved/exported.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json, math, os, sys, subprocess, shutil, tempfile, zipfile, html, copy

TITLE = 'Wa Waa Engine 0.1.1.1 — Fusion-style Editor'
W, H = 800, 480
COLORS = {'Player':'#45b7ff','Platform':'#5bc17a','Enemy':'#f46c78','Coin':'#ffcf4c','Text':'#ffffff'}

def default_project():
    return {'name':'My Wa Wa Game','width':W,'height':H,'background':'#202a40','fps':60,
            'objects':[{'kind':'Player','x':80,'y':320,'w':34,'h':34,'name':'Player 1'},
                       {'kind':'Platform','x':0,'y':440,'w':800,'h':40,'name':'Ground'},
                       {'kind':'Platform','x':230,'y':350,'w':170,'h':22,'name':'Platform 1'},
                       {'kind':'Coin','x':300,'y':310,'w':20,'h':20,'name':'Coin 1'},
                       {'kind':'Enemy','x':570,'y':408,'w':32,'h':32,'name':'Enemy 1'}],
            'events':['Arrow keys / A,D: move','Space / Up: jump','Collect coins; avoid enemies'], 'rules':[], 'grid':16}

def game_html(project):
    data=json.dumps(project).replace('</','<\\/')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+html.escape(project['name'])+'''</title><style>body{background:#101622;color:white;font:16px system-ui;display:grid;place-items:center;min-height:100vh;margin:0}canvas{max-width:95vw;border:2px solid #586a89;image-rendering:pixelated}p{opacity:.8}</style></head><body><main><h2>'''+html.escape(project['name'])+'''</h2><canvas id="game"></canvas><p>Move: arrows / A,D &nbsp; Jump: Space / Up &nbsp; Restart: R</p></main><script>
const project='''+data+''';const c=document.getElementById('game'),ctx=c.getContext('2d');c.width=project.width;c.height=project.height;
let keys={},player,items,score=0,dead=false,won=false;function reset(){items=project.objects.map(o=>({...o,active:true}));player=items.find(o=>o.kind==='Player');if(player){player.vy=0;player.grounded=false}score=0;dead=false;won=false}reset();
addEventListener('keydown',e=>{keys[e.key.toLowerCase()]=true;if([' ','arrowup','arrowdown','arrowleft','arrowright'].includes(e.key.toLowerCase()))e.preventDefault();if(e.key.toLowerCase()==='r')reset()});addEventListener('keyup',e=>keys[e.key.toLowerCase()]=false);
function overlap(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y}
let previous=performance.now(),acc=0;function frame(now){let dt=Math.min(.05,(now-previous)/1000);previous=now;acc+=dt;let step=1/Math.max(1,Math.min(120,project.fps||60));while(acc>=step){update(step);acc-=step}draw();requestAnimationFrame(frame)}
function update(dt){if(!player||dead)return;let dx=((keys.arrowright||keys.d)?1:0)-((keys.arrowleft||keys.a)?1:0);player.x=Math.max(0,Math.min(c.width-player.w,player.x+dx*230*dt));if((keys[' ']||keys.arrowup||keys.w)&&player.grounded){player.vy=-430;player.grounded=false}let oldBottom=player.y+player.h;player.vy=Math.min(700,player.vy+1100*dt);player.y+=player.vy*dt;player.grounded=false;for(let o of items){if(o.kind==='Platform'&&overlap(player,o)&&player.vy>=0&&oldBottom<=o.y+12){player.y=o.y-player.h;player.vy=0;player.grounded=true}}if(player.y>c.height+100){dead=true}for(let o of items){if(!o.active||o===player)continue;if(o.kind==='Coin'&&overlap(player,o)){o.active=false;score++}if(o.kind==='Enemy'&&overlap(player,o))dead=true}for(let rule of (project.rules||[])){let target=items.find(o=>o.name===rule.target&&o.active);let fired=(rule.when==='always'||(rule.when==='touch'&&target&&overlap(player,target))||(rule.when==='score'&&score>=Number(rule.value||1)));if(!fired)continue;if(rule.action==='add_score'){score+=Number(rule.amount||1)}else if(rule.action==='game_over'){dead=true}else if(rule.action==='hide'&&target){target.active=false}else if(rule.action==='teleport'){player.x=Number(rule.x||0);player.y=Number(rule.y||0)}else if(rule.action==='win'){dead=true;won=true}}}
function draw(){ctx.fillStyle=project.background;ctx.fillRect(0,0,c.width,c.height);for(let o of items){if(!o.active)continue;ctx.fillStyle=({Player:'#45b7ff',Platform:'#5bc17a',Enemy:'#f46c78',Coin:'#ffcf4c',Text:'#fff'})[o.kind]||'#fff';if(o.kind==='Coin'){ctx.beginPath();ctx.arc(o.x+o.w/2,o.y+o.h/2,Math.min(o.w,o.h)/2,0,Math.PI*2);ctx.fill()}else ctx.fillRect(o.x,o.y,o.w,o.h)}ctx.fillStyle='white';ctx.font='bold 20px sans-serif';ctx.fillText('Coins: '+score,16,30);if(dead){ctx.fillStyle='#000b';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='white';ctx.textAlign='center';ctx.font='bold 34px sans-serif';ctx.fillText(won?'You Win - Press R':'Game Over - Press R',c.width/2,c.height/2);ctx.textAlign='left'}}requestAnimationFrame(frame);
</script></body></html>'''

def desktop_source(project):
    payload=repr(json.dumps(project))
    return '''#!/usr/bin/env python3
"""Wa Wa Engine exported desktop game - stdlib Tkinter."""
import tkinter as tk, json, time
P=json.loads('''+payload+''')
root=tk.Tk();root.title(P['name']);w=P['width'];h=P['height'];cv=tk.Canvas(root,width=w,height=h,bg=P['background'],highlightthickness=0);cv.pack();keys=set();objs=[];player=None;score=0;dead=False
colors={'Player':'#45b7ff','Platform':'#5bc17a','Enemy':'#f46c78','Coin':'#ffcf4c','Text':'#ffffff'}
def reset():
 global objs,player,score,dead
 objs=[dict(o,active=True) for o in P['objects']];player=next((o for o in objs if o['kind']=='Player'),None)
 if player:player['vy']=0;player['grounded']=False
 score=0;dead=False
def down(e):
 keys.add(e.keysym.lower())
 if e.keysym.lower()=='r':reset()
def up(e):keys.discard(e.keysym.lower())
root.bind('<KeyPress>',down);root.bind('<KeyRelease>',up)
def hit(a,b):return a['x']<b['x']+b['w'] and a['x']+a['w']>b['x'] and a['y']<b['y']+b['h'] and a['y']+a['h']>b['y']
def update(dt):
 global score,dead
 if not player or dead:return
 dx=int('right' in keys or 'd' in keys)-int('left' in keys or 'a' in keys)
 player['x']=max(0,min(w-player['w'],player['x']+dx*230*dt))
 if ('space' in keys or 'up' in keys or 'w' in keys) and player['grounded']:player['vy']=-430;player['grounded']=False
 bottom=player['y']+player['h'];player['vy']=min(700,player['vy']+1100*dt);player['y']+=player['vy']*dt;player['grounded']=False
 for o in objs:
  if o['kind']=='Platform' and hit(player,o) and player['vy']>=0 and bottom<=o['y']+12:player['y']=o['y']-player['h'];player['vy']=0;player['grounded']=True
 if player['y']>h+100:dead=True
 for o in objs:
  if not o['active'] or o is player:continue
  if o['kind']=='Coin' and hit(player,o):o['active']=False;score+=1
  if o['kind']=='Enemy' and hit(player,o):dead=True
  for rule in P.get('rules',[]):
   target=next((a for a in objs if a.get('name')==rule.get('target') and a.get('active')),None)
   fired=rule.get('when')=='always' or (rule.get('when')=='touch' and target is not None and hit(player,target)) or (rule.get('when')=='score' and score>=float(rule.get('value',1)))
   if not fired:continue
   action=rule.get('action')
   if action=='add_score':score+=int(rule.get('amount',1))
   elif action in ('game_over','win'):dead=True
   elif action=='hide' and target:target['active']=False
   elif action=='teleport':player['x']=float(rule.get('x',0));player['y']=float(rule.get('y',0))
def draw():
 cv.delete('all')
 for o in objs:
  if not o['active']:continue
  x,y,ww,hh=(o[k] for k in ('x','y','w','h'));color=colors.get(o['kind'],'white')
  if o['kind']=='Coin':cv.create_oval(x,y,x+ww,y+hh,fill=color,outline='')
  else:cv.create_rectangle(x,y,x+ww,y+hh,fill=color,outline='')
 cv.create_text(16,16,text='Coins: '+str(score),anchor='w',fill='white',font=('Arial',16,'bold'))
 if dead:cv.create_text(w/2,h/2,text='Game Over - Press R',fill='white',font=('Arial',28,'bold'))
reset();last=time.monotonic();acc=0.0;step=1/max(1,min(120,P.get('fps',60)))
def loop():
 global last,acc
 now=time.monotonic();acc+=min(.05,now-last);last=now
 while acc>=step:update(step);acc-=step
 draw();root.after(8,loop)
loop();root.mainloop()
'''

class Editor:
 def __init__(self,root):
  self.root=root;self.project=default_project();self.selected=None;self.drag=None;self.zoom=0.85
  root.title(TITLE+' — '+self.project['name']);root.geometry('1230x780');root.minsize(950,620)
  self.style=ttk.Style();self.style.theme_use('clam');self.style.configure('Treeview',rowheight=24)
  self.make_menu();self.make_ui();self.refresh()
 def make_menu(self):
  menu=tk.Menu(self.root);self.root.config(menu=menu)
  file=tk.Menu(menu,tearoff=0);menu.add_cascade(label='File',menu=file)
  for label,fn in [('New',self.new),('Open Project…',self.open),('Save Project…',self.save),('Export HTML5…',self.export_html),('Export Desktop Python…',self.export_python),('Build Windows EXE…',self.export_exe),('Export macOS / Linux Bundle…',self.export_bundle),('Export Source ZIP…',self.export_zip),('Exit',self.root.destroy)]:file.add_command(label=label,command=fn)
  edit=tk.Menu(menu,tearoff=0);menu.add_cascade(label='Edit',menu=edit)
  edit.add_command(label='Delete Selected',command=self.delete);edit.add_command(label='Duplicate Selected',command=self.duplicate)
  game=tk.Menu(menu,tearoff=0);menu.add_cascade(label='Run',menu=game);game.add_command(label='Preview Game',command=self.preview)
  themes=tk.Menu(menu,tearoff=0);menu.add_cascade(label='Themes',menu=themes)
  for choice in ('Dark','Light','System'):
   themes.add_radiobutton(label=choice,variable=self.theme_choice,value=choice,command=self.apply_theme)
  helpm=tk.Menu(menu,tearoff=0);menu.add_cascade(label='Help',menu=helpm);helpm.add_command(label='About',command=lambda:messagebox.showinfo('About',TITLE+'\n© AC Kondo 1999–2026\nSingle-file Tkinter game editor.'))
 def make_ui(self):
  top=tk.Frame(self.root,bg='#202a3a');top.pack(fill='x')
  for text,fn in [('New',self.new),('Open',self.open),('Save',self.save),('▶ Preview',self.preview),('HTML5',self.export_html),('Desktop',self.export_python),('EXE',self.export_exe)]:tk.Button(top,text=text,command=fn,bg='black',fg='#238BFF',activebackground='black',activeforeground='#238BFF',relief='flat',padx=12,pady=8).pack(side='left',padx=3,pady=5)
  main=tk.PanedWindow(self.root,orient='horizontal',sashwidth=5,bg='#17202d');main.pack(fill='both',expand=True)
  left=tk.Frame(main,bg='#253246',width=210);main.add(left,minsize=160)
  tk.Label(left,text='PROJECT WORKSPACE',bg='#253246',fg='#e3efff',font=('Arial',11,'bold')).pack(anchor='w',padx=10,pady=12)
  self.tree=ttk.Treeview(left,show='tree',selectmode='browse');self.tree.pack(fill='both',expand=True,padx=6,pady=6);self.tree.bind('<<TreeviewSelect>>',self.tree_select)
  tk.Label(left,text='INSERT OBJECT',bg='#253246',fg='#e3efff').pack(anchor='w',padx=10,pady=6)
  for kind in COLORS:tk.Button(left,text='+ '+kind,command=lambda k=kind:self.add(k),bg='black',fg='#238BFF',activebackground='black',activeforeground='#238BFF',relief='flat').pack(fill='x',padx=10,pady=2)
  center=tk.Frame(main,bg='#141c2a');main.add(center,minsize=430)
  tk.Label(center,text='FRAME EDITOR  •  drag objects to position them',bg='#141c2a',fg='#a7c8f0').pack(anchor='w',padx=12,pady=8)
  self.canvas=tk.Canvas(center,bg='#101722',highlightthickness=0);self.canvas.pack(fill='both',expand=True,padx=10,pady=5)
  self.canvas.bind('<Button-1>',self.click);self.canvas.bind('<B1-Motion>',self.motion);self.canvas.bind('<ButtonRelease-1>',lambda e:setattr(self,'drag',None));self.canvas.bind('<Configure>',lambda e:self.draw())
  tk.Label(center,text='Built-in demo: platformer • player / platforms / coins / enemies • 60 FPS',bg='#141c2a',fg='#92a9c4').pack(anchor='w',padx=12,pady=7)
  right=tk.Frame(main,bg='#253246',width=230);main.add(right,minsize=190)
  tk.Label(right,text='PROPERTIES',bg='#253246',fg='white',font=('Arial',11,'bold')).pack(anchor='w',padx=12,pady=12)
  self.entries={}
  for field in ('name','x','y','w','h'):
   tk.Label(right,text=field.upper(),bg='#253246',fg='#c2d6ed').pack(anchor='w',padx=12)
   ent=tk.Entry(right,bg='#101c2b',fg='white',insertbackground='white',relief='flat');ent.pack(fill='x',padx=12,pady=(2,10));self.entries[field]=ent
  tk.Button(right,text='Apply Properties',command=self.apply,bg='black',fg='#238BFF',activebackground='black',activeforeground='#238BFF').pack(fill='x',padx=12,pady=5)
  tk.Button(right,text='Duplicate',bg='black',fg='#238BFF',activebackground='black',activeforeground='#238BFF',command=self.duplicate).pack(fill='x',padx=12,pady=5)
  tk.Button(right,text='Delete',bg='black',fg='#238BFF',activebackground='black',activeforeground='#238BFF',command=self.delete).pack(fill='x',padx=12,pady=5)
  tk.Label(right,text='EVENT EDITOR (notes)',bg='#253246',fg='white',font=('Arial',10,'bold')).pack(anchor='w',padx=12,pady=(25,4))
  self.events=tk.Text(right,height=7,bg='#101c2b',fg='#cde3fc',wrap='word');self.events.pack(fill='x',padx=12)
  tk.Button(right,text='Apply Event Notes',bg='black',fg='#238BFF',activebackground='black',activeforeground='#238BFF',command=self.apply_events).pack(fill='x',padx=12,pady=5)
  self.status=tk.Label(self.root,text='Ready',anchor='w',bg='#152031',fg='#bcd1e8');self.status.pack(fill='x')
 def refresh(self):
  self.tree.delete(*self.tree.get_children());self.tree.insert('', 'end',iid='root',text=self.project['name'],open=True)
  for i,o in enumerate(self.project['objects']):self.tree.insert('root','end',iid=str(i),text=f"{o['kind']}  •  {o['name']}")
  self.events.delete('1.0','end');self.events.insert('1.0','\n'.join(self.project.get('events',[])))
  self.draw();self.show_props();self.root.title(TITLE+' — '+self.project['name'])
 def geometry(self):
  cw=max(1,self.canvas.winfo_width());ch=max(1,self.canvas.winfo_height());scale=min((cw-32)/self.project['width'],(ch-32)/self.project['height'],1.5)
  return ((cw-self.project['width']*scale)/2,(ch-self.project['height']*scale)/2,scale)
 def draw(self):
  c=self.canvas;c.delete('all');ox,oy,s=self.geometry();w=self.project['width'];h=self.project['height']
  c.create_rectangle(ox,oy,ox+w*s,oy+h*s,fill=self.project['background'],outline='#60748c',width=2)
  for i,o in enumerate(self.project['objects']):
   x=ox+o['x']*s;y=oy+o['y']*s;xx=x+o['w']*s;yy=y+o['h']*s
   if o['kind']=='Coin':c.create_oval(x,y,xx,yy,fill=COLORS['Coin'],outline='')
   else:c.create_rectangle(x,y,xx,yy,fill=COLORS.get(o['kind'],'white'),outline='#ffffff' if i==self.selected else '')
   if i==self.selected:c.create_rectangle(x-3,y-3,xx+3,yy+3,outline='#f5ff73',dash=(4,3),width=2)
  c.create_text(ox+8,oy+8,text=f"{w} × {h} | {self.project['fps']} FPS",fill='white',anchor='nw')
 def select(self,i):
  self.selected=i;self.show_props();self.draw()
  if i is not None and str(i) in self.tree.get_children('root'):self.tree.selection_set(str(i))
 def tree_select(self,event):
  sel=self.tree.selection()
  if sel and sel[0]!='root':self.select(int(sel[0]))
 def click(self,event):
  ox,oy,s=self.geometry();x=(event.x-ox)/s;y=(event.y-oy)/s
  for i in range(len(self.project['objects'])-1,-1,-1):
   o=self.project['objects'][i]
   if o['x']<=x<=o['x']+o['w'] and o['y']<=y<=o['y']+o['h']:
    self.select(i);self.drag=(x-o['x'],y-o['y']);return
  self.select(None)
 def motion(self,event):
  if self.selected is None or self.drag is None:return
  ox,oy,s=self.geometry();o=self.project['objects'][self.selected]
  o['x']=round(max(0,min(self.project['width']-o['w'],(event.x-ox)/s-self.drag[0])))
  o['y']=round(max(0,min(self.project['height']-o['h'],(event.y-oy)/s-self.drag[1])))
  self.draw();self.show_props()
 def show_props(self):
  o=self.project['objects'][self.selected] if self.selected is not None and self.selected<len(self.project['objects']) else {}
  for k,e in self.entries.items():e.delete(0,'end');e.insert(0,str(o.get(k,'')))
 def add(self,kind):
  o={'kind':kind,'x':120,'y':120,'w':32,'h':32,'name':kind+' '+str(len(self.project['objects'])+1)}
  if kind=='Platform':o['w']=120;o['h']=24
  self.project['objects'].append(o);self.refresh();self.select(len(self.project['objects'])-1)
 def apply(self):
  if self.selected is None:return
  o=self.project['objects'][self.selected]
  try:
   for k in ('x','y','w','h'):o[k]=int(self.entries[k].get())
   if o['w']<=0 or o['h']<=0:raise ValueError('Size must be positive')
   o['name']=self.entries['name'].get().strip() or o['kind']
  except ValueError as e:messagebox.showerror('Invalid property',str(e));return
  self.refresh();self.select(self.selected)
 def apply_events(self):
  self.project['events']=self.events.get('1.0','end').strip().splitlines();self.status.config(text='Event notes saved. Runtime uses built-in platformer behaviors.')
 def delete(self):
  if self.selected is None:return
  self.project['objects'].pop(self.selected);self.selected=None;self.refresh()
 def duplicate(self):
  if self.selected is None:return
  o=dict(self.project['objects'][self.selected]);o['x']+=20;o['y']+=20;o['name']+=' Copy';self.project['objects'].append(o);self.refresh();self.select(len(self.project['objects'])-1)
 def new(self):self.project=default_project();self.selected=None;self.refresh()
 def open(self):
  path=filedialog.askopenfilename(filetypes=[('Wa Wa projects','*.wawa'),('JSON','*.json')]);
  if not path:return
  try:
   with open(path,encoding='utf-8') as f:p=json.load(f)
   if not isinstance(p.get('objects'),list) or not all(k in p for k in ('width','height','background','name')):raise ValueError('Invalid project structure')
   self.project=p;self.selected=None;self.refresh();self.status.config(text='Opened '+path)
  except (OSError,ValueError,TypeError,KeyError) as e:messagebox.showerror('Open failed',str(e))
 def save(self):
  path=filedialog.asksaveasfilename(defaultextension='.wawa',filetypes=[('Wa Wa project','*.wawa')]);
  if path:
   try:
    self.apply_events()
    with open(path,'w',encoding='utf-8') as f:json.dump(self.project,f,indent=2)
    self.status.config(text='Saved '+path)
   except OSError as e:messagebox.showerror('Save failed',str(e))
 def export_html(self):
  path=filedialog.asksaveasfilename(defaultextension='.html',filetypes=[('HTML5 Game','*.html')]);
  if path:self.write(path,game_html(self.project))
 def export_python(self):
  path=filedialog.asksaveasfilename(defaultextension='.py',filetypes=[('Python game','*.py')]);
  if path:self.write(path,desktop_source(self.project))
 def write(self,path,data):
  try:
   with open(path,'w',encoding='utf-8') as f:f.write(data)
   self.status.config(text='Exported '+path);messagebox.showinfo('Export complete',path)
  except OSError as e:messagebox.showerror('Export failed',str(e))
 def export_zip(self):
  path=filedialog.asksaveasfilename(defaultextension='.zip',filetypes=[('ZIP archive','*.zip')]);
  if not path:return
  try:
   with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('game.html',game_html(self.project));z.writestr('game.py',desktop_source(self.project));z.writestr('project.wawa',json.dumps(self.project,indent=2));z.writestr('README.txt','Wa Wa Engine source bundle. Run game.py with Python 3 + Tkinter, or open game.html in a browser.\n')
   messagebox.showinfo('Export complete',path)
  except OSError as e:messagebox.showerror('Export failed',str(e))
 def export_bundle(self):
  folder=filedialog.askdirectory(title='Choose destination folder')
  if not folder:return
  try:
   target=os.path.join(folder,'WaWaGame');os.makedirs(target,exist_ok=True)
   self.write_silent(os.path.join(target,'game.py'),desktop_source(self.project))
   self.write_silent(os.path.join(target,'game.html'),game_html(self.project))
   self.write_silent(os.path.join(target,'run.sh'),'#!/bin/sh\ncd "$(dirname "$0")"\nexec python3 game.py\n')
   os.chmod(os.path.join(target,'run.sh'),0o755)
   messagebox.showinfo('Bundle exported','Portable source bundle at '+target+'\nRequires Python 3 with Tkinter on the destination system. Not a native .app or binary.')
  except OSError as e:messagebox.showerror('Bundle failed',str(e))
 def write_silent(self,path,data):
  with open(path,'w',encoding='utf-8') as f:f.write(data)
 def export_exe(self):
  if sys.platform!='win32':messagebox.showinfo('Windows EXE','Windows EXE builds require running this editor on Windows with PyInstaller installed.\nYou can export the .py now and build it on Windows.');return
  if not shutil.which('pyinstaller'):messagebox.showinfo('PyInstaller required','Install PyInstaller on Windows: py -m pip install pyinstaller');return
  folder=filedialog.askdirectory(title='Choose EXE output folder')
  if not folder:return
  try:
   with tempfile.TemporaryDirectory() as tmp:
    src=os.path.join(tmp,'wawa_game.py');self.write_silent(src,desktop_source(self.project))
    result=subprocess.run([sys.executable,'-m','PyInstaller','--onefile','--windowed','--name','WaWaGame','--distpath',folder,'--workpath',os.path.join(tmp,'build'),'--specpath',tmp,src],capture_output=True,text=True,timeout=240)
    if result.returncode:raise RuntimeError((result.stderr or result.stdout)[-1800:])
   messagebox.showinfo('EXE built','Created '+os.path.join(folder,'WaWaGame.exe'))
  except (OSError,RuntimeError,subprocess.TimeoutExpired) as e:messagebox.showerror('Build failed',str(e))
 def preview(self):
  win=tk.Toplevel(self.root);win.title('▶ '+self.project['name']);p=json.loads(json.dumps(self.project));w=p['width'];h=p['height'];canvas=tk.Canvas(win,width=w,height=h,bg=p['background'],highlightthickness=0);canvas.pack();win.focus_set()
  keys=set();objects=[dict(o,active=True) for o in p['objects']];player=next((o for o in objects if o['kind']=='Player'),None);state={'score':0,'dead':False,'last':None,'acc':0}
  if player:player.update(vy=0,grounded=False)
  def reset():
   nonlocal objects,player
   objects=[dict(o,active=True) for o in p['objects']];player=next((o for o in objects if o['kind']=='Player'),None)
   if player:player.update(vy=0,grounded=False)
   state['score']=0;state['dead']=False
  def down(e):
   keys.add(e.keysym.lower())
   if e.keysym.lower()=='r':reset()
  def up(e):keys.discard(e.keysym.lower())
  win.bind('<KeyPress>',down);win.bind('<KeyRelease>',up)
  def hit(a,b):return a['x']<b['x']+b['w'] and a['x']+a['w']>b['x'] and a['y']<b['y']+b['h'] and a['y']+a['h']>b['y']
  def update(dt):
   if not player or state['dead']:return
   dx=int('right' in keys or 'd' in keys)-int('left' in keys or 'a' in keys)
   player['x']=max(0,min(w-player['w'],player['x']+dx*230*dt))
   if ('space' in keys or 'up' in keys or 'w' in keys) and player['grounded']:player['vy']=-430;player['grounded']=False
   bottom=player['y']+player['h'];player['vy']=min(700,player['vy']+1100*dt);player['y']+=player['vy']*dt;player['grounded']=False
   for o in objects:
    if o['kind']=='Platform' and hit(player,o) and player['vy']>=0 and bottom<=o['y']+12:player['y']=o['y']-player['h'];player['vy']=0;player['grounded']=True
   if player['y']>h+100:state['dead']=True
   for o in objects:
    if not o['active'] or o is player:continue
    if o['kind']=='Coin' and hit(player,o):o['active']=False;state['score']+=1
    if o['kind']=='Enemy' and hit(player,o):state['dead']=True
   for rule in p.get('rules',[]):
    target=next((a for a in objects if a.get('name')==rule.get('target') and a.get('active')),None)
    fired=rule.get('when')=='always' or (rule.get('when')=='touch' and target is not None and hit(player,target)) or (rule.get('when')=='score' and state['score']>=float(rule.get('value') or 1))
    if not fired:continue
    action=rule.get('action')
    if action=='add_score':state['score']+=int(rule.get('amount') or 1)
    elif action in ('game_over','win'):state['dead']=True
    elif action=='hide' and target:target['active']=False
    elif action=='teleport':player['x']=float(rule.get('x') or 0);player['y']=float(rule.get('y') or 0)
  def loop():
   if not win.winfo_exists():return
   import time
   now=time.monotonic()
   if state['last'] is None:state['last']=now
   state['acc']+=min(.05,now-state['last']);state['last']=now;step=1/max(1,min(120,p.get('fps',60)))
   while state['acc']>=step:update(step);state['acc']-=step
   canvas.delete('all')
   for o in objects:
    if not o['active']:continue
    x,y,ww,hh=(o[k] for k in ('x','y','w','h'));color=COLORS.get(o['kind'],'white')
    if o['kind']=='Coin':canvas.create_oval(x,y,x+ww,y+hh,fill=color,outline='')
    else:canvas.create_rectangle(x,y,x+ww,y+hh,fill=color,outline='')
   canvas.create_text(15,20,text='Coins: '+str(state['score']),fill='white',anchor='w',font=('Arial',16,'bold'))
   if state['dead']:canvas.create_text(w/2,h/2,text='Game Over - Press R',fill='white',font=('Arial',28,'bold'))
   win.after(8,loop)
  loop()


class FusionEditor(Editor):
 def __init__(self,root):
  self.frames=[];self.frame_index=0;self.history=[];self.future=[];self.snap=False
  self.theme_choice=tk.StringVar(master=root,value="Dark")
  super().__init__(root)
  self.frames=[copy.deepcopy(self.project)]
  self.install_tools()
  self.apply_theme()
 def system_dark(self):
  """Read native appearance when available; fall back to a light system theme."""
  if sys.platform == 'darwin':
   try:
    result=subprocess.run(['defaults','read','-g','AppleInterfaceStyle'],capture_output=True,text=True,timeout=2)
    return result.returncode == 0 and result.stdout.strip().lower() == 'dark'
   except (OSError,subprocess.TimeoutExpired):return False
  if sys.platform == 'win32':
   try:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
     return winreg.QueryValueEx(key,'AppsUseLightTheme')[0] == 0
   except (OSError,ImportError):return False
  return os.environ.get('GTK_THEME','').lower().endswith(':dark')
 def apply_theme(self):
  """Recolor the editor chrome without changing the project or game canvas."""
  choice=self.theme_choice.get()
  dark=(choice == 'Dark' or (choice == 'System' and self.system_dark()))
  bg='#202a3a' if dark else '#edf2fa'
  panel='#253246' if dark else '#e1e9f5'
  surface='#101c2b' if dark else '#ffffff'
  foreground='#e3efff' if dark else '#21324b'
  blue='#238BFF'
  self.root.configure(bg=bg)
  self.style.configure('Treeview',background=surface,fieldbackground=surface,foreground=foreground,rowheight=24)
  self.style.map('Treeview',background=[('selected','#1760aa')],foreground=[('selected','#ffffff')])
  self.style.configure('Treeview.Heading',background=panel,foreground=foreground)
  def recolor(widget):
   if isinstance(widget,tk.Button):
    widget.configure(bg='black',fg=blue,activebackground='black',activeforeground=blue)
   elif isinstance(widget,tk.Entry):
    widget.configure(bg=surface,fg=foreground,insertbackground=foreground)
   elif isinstance(widget,tk.Text):
    widget.configure(bg=surface,fg=foreground,insertbackground=foreground)
   elif isinstance(widget,tk.Label):
    widget.configure(bg=panel,fg=foreground)
   elif isinstance(widget,tk.PanedWindow):
    widget.configure(bg=bg)
   elif isinstance(widget,tk.Frame):
    widget.configure(bg=panel)
   elif isinstance(widget,tk.Canvas):
    widget.configure(bg=surface)
   for child in widget.winfo_children():recolor(child)
  for child in self.root.winfo_children():recolor(child)
  if hasattr(self,'status'):self.status.configure(text=f'Theme: {choice} · Blue text / black buttons')
  if hasattr(self,'canvas'):self.draw()
 def install_tools(self):
  bar=tk.Frame(self.root,bg='#101a2a')
  bar.pack(fill='x',before=self.status)
  for label,callback in [('＋ Frame',self.add_frame),('◀ Frame',self.prev_frame),('Frame ▶',self.next_frame),('Rename Frame',self.rename_frame),('Events',self.event_editor),('Project',self.project_settings),('Undo',self.undo),('Redo',self.redo),('Grid',self.toggle_grid),('Snap',self.toggle_snap),('Sprite',self.import_sprite)]:
   tk.Button(bar,text=label,command=callback,bg='black',fg='#238BFF',activebackground='#16253d',activeforeground='#62b3ff',relief='flat',padx=7,pady=6).pack(side='left',padx=2)
  self.frame_label=tk.Label(bar,text='',bg='#101a2a',fg='white');self.frame_label.pack(side='right',padx=8)
  self.show_frame_label()
  self.root.bind_all('<Control-z>',lambda e:self.undo())
  self.root.bind_all('<Control-y>',lambda e:self.redo())
  self.root.bind_all('<Control-s>',lambda e:self.save())
 def show_frame_label(self):
  if hasattr(self,'frame_label'):self.frame_label.config(text=f'Frame {self.frame_index+1}/{len(self.frames)} · {self.project["name"]}')
 def snapshot(self):
  self.history.append(copy.deepcopy((self.frames,self.frame_index,self.project)))
  self.history=self.history[-60:];self.future.clear()
 def restore(self,state):
  self.frames,self.frame_index,self.project=copy.deepcopy(state)
  self.frames[self.frame_index]=self.project
  self.selected=None;self.refresh();self.show_frame_label()
 def undo(self):
  if self.history:
   self.future.append(copy.deepcopy((self.frames,self.frame_index,self.project)))
   self.restore(self.history.pop())
 def redo(self):
  if self.future:
   self.history.append(copy.deepcopy((self.frames,self.frame_index,self.project)))
   self.restore(self.future.pop())
 def add_frame(self):
  self.snapshot();self.frames.append(default_project());self.frame_index=len(self.frames)-1
  self.project=self.frames[self.frame_index];self.project['name']=f'Frame {self.frame_index+1}'
  self.selected=None;self.refresh();self.show_frame_label()
 def switch_frame(self,index):
  if not 0<=index<len(self.frames):return
  self.frames[self.frame_index]=self.project
  self.frame_index=index;self.project=self.frames[index];self.selected=None;self.refresh();self.show_frame_label()
 def prev_frame(self):self.switch_frame(self.frame_index-1)
 def next_frame(self):self.switch_frame(self.frame_index+1)
 def rename_frame(self):
  name=simpledialog.askstring('Frame name','Frame name:',initialvalue=self.project['name'],parent=self.root)
  if name:self.snapshot();self.project['name']=name;self.refresh();self.show_frame_label()
 def toggle_grid(self):
  self.project['show_grid']=not self.project.get('show_grid',False);self.draw()
 def toggle_snap(self):
  self.snap=not self.snap;self.status.config(text='Grid snap '+('ON' if self.snap else 'OFF'))
 def draw(self):
  super().draw()
  if not self.project.get('show_grid'):return
  ox,oy,s=self.geometry();step=max(4,int(self.project.get('grid',16)))
  for x in range(step,self.project['width'],step):
   xx=ox+x*s;self.canvas.create_line(xx,oy,xx,oy+self.project['height']*s,fill='#344158',dash=(2,4))
  for y in range(step,self.project['height'],step):
   yy=oy+y*s;self.canvas.create_line(ox,yy,ox+self.project['width']*s,yy,fill='#344158',dash=(2,4))
 def click(self,event):
  self.snapshot();super().click(event)
 def motion(self,event):
  super().motion(event)
  if self.snap and self.selected is not None:
   o=self.project['objects'][self.selected];step=max(1,int(self.project.get('grid',16)))
   o['x']=round(o['x']/step)*step;o['y']=round(o['y']/step)*step
   self.draw();self.show_props()
 def add(self,kind):self.snapshot();super().add(kind)
 def delete(self):self.snapshot();super().delete()
 def duplicate(self):self.snapshot();super().duplicate()
 def apply(self):self.snapshot();super().apply()
 def new(self):
  self.snapshot();self.frames=[default_project()];self.frame_index=0;self.project=self.frames[0];self.selected=None;self.refresh();self.show_frame_label()
 def open(self):
  path=filedialog.askopenfilename(filetypes=[('Wa Wa projects','*.wawa'),('JSON','*.json')])
  if not path:return
  try:
   with open(path,encoding='utf-8') as f:data=json.load(f)
   frames=data.get('frames') if isinstance(data,dict) else None
   if not frames:frames=[data]
   if not all(isinstance(p,dict) and isinstance(p.get('objects'),list) for p in frames):raise ValueError('Invalid frame data')
   self.snapshot();self.frames=frames;self.frame_index=0;self.project=frames[0];self.selected=None;self.refresh();self.show_frame_label()
  except (OSError,ValueError,TypeError) as e:messagebox.showerror('Open failed',str(e))
 def save(self):
  path=filedialog.asksaveasfilename(defaultextension='.wawa',filetypes=[('Wa Wa project','*.wawa')])
  if path:
   try:
    self.apply_events();self.frames[self.frame_index]=self.project
    with open(path,'w',encoding='utf-8') as f:json.dump({'format':'wawa-2','frames':self.frames},f,indent=2)
    self.status.config(text='Saved '+path)
   except OSError as e:messagebox.showerror('Save failed',str(e))
 def project_settings(self):
  self.snapshot()
  for key in ('width','height','fps','grid'):
   val=simpledialog.askinteger('Project settings',key.upper(),initialvalue=self.project.get(key,16),minvalue=1,maxvalue=4096,parent=self.root)
   if val is not None:self.project[key]=val
  bg=simpledialog.askstring('Background','Hex color:',initialvalue=self.project.get('background','#202a40'),parent=self.root)
  if bg:
   try:self.root.winfo_rgb(bg);self.project['background']=bg
   except tk.TclError:messagebox.showerror('Color','Invalid Tk color')
  self.refresh()
 def import_sprite(self):
  if self.selected is None:messagebox.showinfo('Sprite','Select an object first');return
  path=filedialog.askopenfilename(filetypes=[('PNG/GIF image','*.png *.gif')])
  if not path:return
  self.snapshot();self.project['objects'][self.selected]['sprite']=path
  self.status.config(text='Sprite path attached. Native image rendering/export not yet supported: '+path)
 def event_editor(self):
  win=tk.Toplevel(self.root);win.title('Wa Wa Event Editor');win.geometry('850x450');win.configure(bg='#172235')
  tk.Label(win,text='EVENT EDITOR · condition → action',fg='#8bc1ff',bg='#172235',font=('Arial',13,'bold')).pack(pady=10)
  table=ttk.Treeview(win,columns=('when','target','value','action','amount','x','y'),show='headings')
  for col in ('when','target','value','action','amount','x','y'):table.heading(col,text=col.upper());table.column(col,width=110)
  table.pack(fill='both',expand=True,padx=12)
  def redraw():
   table.delete(*table.get_children())
   for i,r in enumerate(self.project.setdefault('rules',[])):table.insert('','end',iid=str(i),values=[r.get(k,'') for k in ('when','target','value','action','amount','x','y')])
  redraw()
  line=tk.Frame(win,bg='#172235');line.pack(fill='x',padx=12,pady=8)
  values={}
  specs=[('when',['touch','score','always']),('target',[o['name'] for o in self.project['objects']]),('value',None),('action',['hide','add_score','game_over','win','teleport']),('amount',None),('x',None),('y',None)]
  for key,options in specs:
   f=tk.Frame(line,bg='#172235');f.pack(side='left',fill='x',expand=True)
   tk.Label(f,text=key,bg='#172235',fg='white').pack()
   if options is not None:widget=ttk.Combobox(f,values=options,width=11)
   else:widget=tk.Entry(f,width=9)
   widget.pack(padx=2);values[key]=widget
  values['when'].set('touch');values['action'].set('hide');values['value'].insert(0,'1');values['amount'].insert(0,'1')
  def add_rule():
   r={k:w.get().strip() for k,w in values.items()}
   if r['when']=='touch' and not r['target']:messagebox.showerror('Event','Choose a target object',parent=win);return
   self.snapshot();self.project.setdefault('rules',[]).append(r);redraw()
  def delete_rule():
   sel=table.selection()
   if sel:self.snapshot();self.project['rules'].pop(int(sel[0]));redraw()
  buttons=tk.Frame(win,bg='#172235');buttons.pack(pady=8)
  for title,cmd in [('Add Event',add_rule),('Delete Selected',delete_rule),('Close',win.destroy)]:tk.Button(buttons,text=title,command=cmd,bg='black',fg='#238BFF').pack(side='left',padx=6)

if __name__=='__main__':
 root=tk.Tk();FusionEditor(root);root.mainloop()
