if(typeof P==="undefined"){document.body.innerHTML="<p style='padding:20px'>Missing data/pokemon-data.js. Run data/make_data.py first (python data\\make_data.py).</p>";throw new Error("no data")}
const TY="nor fir wat ele gra ice fig poi gro fly psy bug roc gho dra dar ste fai".split(" ");
const TN="Normal Fire Water Electric Grass Ice Fighting Poison Ground Flying Psychic Bug Rock Ghost Dragon Dark Steel Fairy".split(" ");
const COL="#8a8a7a #e8622c #3b82d6 #d9a406 #4aa03a #4bb8c9 #b83a2e #93459f #b9963a #7d8fd6 #e0457b #91a119 #a48e3a #6d5a94 #5a3fd6 #6b4f42 #7d8da1 #d27ab3".split(" ");
const CH={nor:"||ro ste|gho",fir:"gra ice bug ste|fir wat roc dra|",wat:"fir gro roc|wat gra dra|",ele:"wat fly|ele gra dra|gro",gra:"wat gro roc|fir gra poi fly bug dra ste|",ice:"gra gro fly dra|fir wat ice ste|",fig:"nor ice roc dar ste|poi fly psy bug fai|gho",poi:"gra fai|poi gro roc gho|ste",gro:"fir ele poi roc ste|gra bug|fly",fly:"gra fig bug|ele roc ste|",psy:"fig poi|psy ste|dar",bug:"gra psy dar|fir fig poi fly gho ste fai|",roc:"fir ice fly bug|fig gro ste|",gho:"psy gho|dar|nor",dra:"dra|ste|fai",dar:"psy gho|fig dar fai|",ste:"ice roc fai|fir wat ele ste|",fai:"fig dra dar|fir poi ste|"};
const E={};TY.forEach(a=>{E[a]={};TY.forEach(d=>E[a][d]=1);const[s,h,z]=CH[a].split("|").map(x=>x.trim()?x.trim().split(" "):[]);s.forEach(d=>E[a][d]=2);h.forEach(d=>E[a][d]=.5);z.forEach(d=>E[a][d]=0)});
const eff=(a,d)=>d.reduce((m,t)=>m*E[a][t],1);
const MODES=[["fix","Fix my weaknesses"],["heavy","Heavy hitter"],["fast","Fast attacker"],["tank","Defensive tank"],["phys","Physical attacker"],["spec","Special attacker"],["pdef","Physical defense"],["sdef","Special defense"]];
const bulk=p=>p.hp+p.df+p.sd;
const ROLE={heavy:[p=>Math.max(p.at,p.sa)>=105,p=>Math.max(p.at,p.sa)/10],fast:[p=>p.sp>=95,p=>p.sp/10],tank:[p=>bulk(p)>=280,p=>bulk(p)/30],phys:[p=>p.at>=100&&p.at>=p.sa+15,p=>p.at/10],spec:[p=>p.sa>=100&&p.sa>=p.at+15,p=>p.sa/10],pdef:[p=>p.df>=95,p=>p.df/10],sdef:[p=>p.sd>=95,p=>p.sd/10]};
// Role metric + ideal minimum. Suggestions keep the top 40% of what's catchable, so early game still gets options.
const RM={heavy:[p=>Math.max(p.at,p.sa),105],fast:[p=>p.sp,95],tank:[bulk,280],phys:[p=>p.at>p.sa?p.at:0,100],spec:[p=>p.sa>p.at?p.sa:0,100],pdef:[p=>p.df,95],sdef:[p=>p.sd,95]};
const ROLENAME={heavy:"Heavy hitter",fast:"Fast",tank:"Defensive tank",phys:"Physical attacker",spec:"Special attacker",pdef:"Physical defense",sdef:"Special defense"};
let gen=0,team=[],mode="fix";
const $=s=>document.querySelector(s);
const ch=t=>`<span class="chip" style="background:${COL[TY.indexOf(t)]}">${TN[TY.indexOf(t)]}</span>`;
const chs=a=>a.map(ch).join("");
const avail=()=>P.filter(p=>(!gen||p.g<=gen)&&(!$("#nolg").checked||!p.lg)&&(!$("#fin").checked||p.fe));
function mm(p){const r={x4:[],x2:[],h:[],z:[]};TY.forEach(t=>{const m=eff(t,p.t);if(m>=4)r.x4.push(t);else if(m>1)r.x2.push(t);else if(m==0)r.z.push(t);else if(m<1)r.h.push(t)});return r}
function nat(p){const ph=p.at>=p.sa,fast=p.sp>=85,t=bulk(p)>=280;
if(t)return p.df>=p.sd?(ph?"Impish (+Defense, −Sp. Atk)":"Bold (+Defense, −Attack)"):(ph?"Careful (+Sp. Def, −Sp. Atk)":"Calm (+Sp. Def, −Attack)");
return ph?(fast?"Jolly (+Speed, −Sp. Atk)":"Adamant (+Attack, −Sp. Atk)"):(fast?"Timid (+Speed, −Attack)":"Modest (+Sp. Atk, −Attack)")}
function evs(p){const ph=p.at>=p.sa,a=ph?"Attack":"Sp. Atk";
if(bulk(p)>=280)return `252 HP / 252 ${p.df>=p.sd?"Defense":"Sp. Def"} / 4 ${a}`;
if(p.sp>=85)return `252 ${a} / 252 Speed / 4 HP`;
return `252 ${a} / 252 HP / 4 ${ph?"Defense":"Sp. Def"}`}
function roles(p){return Object.keys(ROLE).filter(k=>ROLE[k][0](p))}
function tw(){const w={};TY.forEach(t=>{w[t]=0;team.forEach(p=>{const m=eff(t,p.t);w[t]+=m>=4?2:m>1?1:m==0?-2:m<1?-1:0})});return w}
function fit(p){let s=0,res=[],cov=[];const w=tw();
TY.forEach(t=>{if(w[t]>0){const m=eff(t,p.t);const v=m==0||m<=.25?3:m<1?2:m==1?0:m==2?-2:-4;s+=w[t]*v;if(v>0)res.push(t)}});
const hit=new Set();team.forEach(q=>q.t.forEach(a=>TY.forEach(d=>{if(E[a][d]>1)hit.add(d)})));
TY.forEach(d=>{if(!hit.has(d)&&p.t.some(a=>E[a][d]>1)){s+=1;cov.push(d)}});
team.forEach(q=>q.t.forEach(a=>{if(p.t.includes(a))s-=1}));
s+=(p.hp+p.at+p.df+p.sa+p.sd+p.sp)/200;return{s,res,cov}}
function bar(l,v){return `<div class="bar"><span>${l}</span><div><i class="s${v<60?1:v<90?2:v<120?3:4}" style="width:${Math.min(100,v/1.6)}%"></i></div><span>${v}</span></div>`}
function card(p,i){const m=mm(p),se=TY.filter(d=>p.t.some(a=>E[a][d]>1));
return `<div class="card"><h3>${img(p)}${p.n} <small>Gen ${p.g}</small></h3><div>${chs(p.t)}</div>${lvRow(p,i)}
${bar("HP",p.hp)}${bar("Atk",p.at)}${bar("Def",p.df)}${bar("SpA",p.sa)}${bar("SpD",p.sd)}${bar("Spe",p.sp)}
<div class="k">Role</div><div class="small">${roles(p).map(r=>ROLENAME[r]).join(", ")||"Balanced all-rounder"}</div>
<div class="k b">Weak to</div><div>${m.x4.length?chs(m.x4)+" <span class=small>(×4)</span><br>":""}${chs(m.x2)||"<span class=small>Nothing!</span>"}</div>
<div class="k g">Hits hard against (own-type moves)</div><div>${chs(se)||"<span class=small>No super-effective STAB</span>"}</div>
<div class="k">Resists</div><div>${chs(m.h)||"—"}${m.z.length?"<br>Immune: "+chs(m.z):""}</div>
<div class="k">Best nature</div><div class="small">${nat(p)}</div>
<div class="k">Suggested EVs</div><div class="small">${evs(p)}</div>
<div class="k">Evolution</div><div class="small">${evTxt(p)}</div>
<div class="k">Where &amp; how to get it</div><div class="small">${whereTxt(p)}</div>
<div class="row"><button onclick="rm(${i})">Remove</button></div></div>`}
function render(){
$("#slots").textContent=`(${team.length}/6)`;
$("#team").innerHTML=team.length?team.map(card).join(""):`<div class="empty">No Pokémon yet. Choose a starter above to begin.</div>`;
if(team.length){const w=tw();const c=TY.map(t=>team.filter(p=>eff(t,p.t)>1).length);
$("#summary").innerHTML=`<div class="k">Team weak spots (how many teammates are weak to each type)</div><div class="tw" style="margin:6px 0 12px">${TY.map((t,i)=>`<div style="${c[i]>=2?"border-color:var(--bad);color:var(--bad)":""}"><b>${c[i]}</b>${TN[i]}</div>`).join("")}</div>`}else $("#summary").innerHTML="";
$("#modes").innerHTML=MODES.map(([k,l])=>`<button class="${k==mode?"on":""}" onclick="mode='${k}';recN=6;render()">${l}</button>`).join("");
recs();rateRender();aheadRender();typeRecRender();if(tab=="s")sRun(1)}
function recs(){
if(team.length>=6){$("#recs").innerHTML=`<div class="empty">Your team is full! Remove someone to try other options.</div>`;return}
const all=rank(cands()),c=all.slice(0,recN);
if(!c.length){$("#recs").innerHTML=`<div class="empty">Nothing matched. Try a later story progress, another style, or Competitive mode.</div>`;return}
$("#recs").innerHTML=`<div class="small">Showing ${c.length} of ${all.length} options${comp?"":" you can get by this point in the game"}.</div><div class="grid">${c.map(x=>rcard(x,0)).join("")}</div>${all.length>recN?`<div class="row"><button onclick="recN+=6;recs()">Show 6 more</button></div>`:""}`}
function add(n,l,t){if(team.length>=6||team.some(p=>p.org==n||(t&&p.n==t)))return;l=l||(comp?50:CAP[stage]);const m=mk(n,l);team.push(t&&t!=m.n?mk(t,l):m);render();$("#team").scrollIntoView({behavior:"smooth",block:"nearest"})}
function rm(i){team.splice(i,1);render()}
function pickType(t){const i=TY.indexOf(t),se=TY.filter(d=>E[t][d]>1),h=TY.filter(d=>E[t][d]<1&&E[t][d]>0),z=TY.filter(d=>E[t][d]==0),w=TY.filter(a=>E[a][t]>1),r=TY.filter(a=>E[a][t]<1&&E[a][t]>0),im=TY.filter(a=>E[a][t]==0);
$("#tinfo").innerHTML=`<h3 style="color:var(--ink)">${TN[i]}</h3><p><b class=g>Attacking:</b> super effective against ${chs(se)||"nothing"}. Not very effective against ${chs(h)||"nothing"}.${z.length?" No effect on "+chs(z)+".":""}</p><p><b class=b>Defending:</b> takes double damage from ${chs(w)||"nothing"}. Resists ${chs(r)||"nothing"}.${im.length?" Immune to "+chs(im)+".":""}</p>`}
$("#tchips").innerHTML=TY.map(t=>`<button onclick="pickType('${t}')">${ch(t)}</button>`).join("");
P.forEach((p,i)=>{p.id=p.id||i+1});
const OFF=!!window.OFFLINE;
let skin="diamond";try{skin=localStorage.getItem("skin2")||"diamond"}catch(e){}
const IMG="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/";
const SP={diamond:["generation-iv/diamond-pearl",493],heartgold:["generation-iv/heartgold-soulsilver",493],soulsilver:["generation-iv/heartgold-soulsilver",493],firered:["generation-iii/firered-leafgreen",386],leafgreen:["generation-iii/firered-leafgreen",386],ruby:["generation-iii/ruby-sapphire",386],sapphire:["generation-iii/ruby-sapphire",386]};
// The shared web version ships all sprites as one sprite sheet (window.SHEET), since it can't load images from GitHub.
const img=p=>{if(window.SHEET){const i=SHEET.idx[p.id];return i==null?"":`<span class="sp sh" style="background-position:${-(i%SHEET.cols)*56}px ${-Math.floor(i/SHEET.cols)*56}px"></span>`}const s=SP[skin],u=s&&p.id<=s[1]?IMG+"versions/"+s[0]+"/"+p.id+".png":IMG+p.id+".png";return `<img class="sp" loading="lazy" alt="" src="${u}">`};
function setSkin(v,click){skin=v;const cl=document.body.classList;[...cl].filter(c=>c=="ds"||c=="g3"||c.startsWith("th-")).forEach(c=>cl.remove(c));
if(v!="plain"){cl.add("ds","th-"+v);if(["firered","leafgreen","ruby","sapphire"].includes(v))cl.add("g3")}
try{localStorage.setItem("skin2",v)}catch(e){}$("#skin").value=v;if(click){starters();any();render()}}
const ST={oak:"Choose it from Professor Oak in his lab in Pallet Town at the start of the game.",elm:"Choose it from Professor Elm in his lab in New Bark Town at the start of the game.",birch:"Rescue Professor Birch on Route 101, then pick it from his bag.",rowan:"Take it from Professor Rowan's briefcase on Route 201 near the start of the game.",juniper:"Given to you by Professor Juniper's team at the start of the game in Nuvema Town.",sycamore:"Choose it from Professor Sycamore's friends near the start, in the Kalos starting area (Vaniville/Aquacorde Town).",kukui:"Choose it early in the game from Professor Kukui on Melemele Island.",galar:"Given to you as an early-game gift at the start of the adventure (Postwick/Wedgehurst area).",hisui:"Choose it from Professor Laventon near the start of the game.",paldea:"Choose it early in the game from Nemona (Mesagoza area).",yellow:"Given to you by Professor Oak at the start of the game.",lgpe:"Your partner Pokémon, which you get at the very start of the game in Pallet Town."};
const A=["Bulbasaur","Charmander","Squirtle"],B=["Chikorita","Cyndaquil","Totodile"],C=["Treecko","Torchic","Mudkip"],D=["Turtwig","Chimchar","Piplup"],U=["Snivy","Tepig","Oshawott"],K=["Chespin","Fennekin","Froakie"],AL=["Rowlet","Litten","Popplio"],GA=["Grookey","Scorbunny","Sobble"],PA=["Sprigatito","Fuecoco","Quaxly"],HI=["Rowlet","Cyndaquil","Oshawott"];
// k = saved-team key, v = catch-data version, dx = Pokédexes for games without a National Dex (evolutions must stay inside them).
const g=(k,l,gn,grp,s,t,v,dx)=>({k,l,g:gn,grp,s,t,v:v||k,dx:dx||null});
const G=[{k:"any",l:"Any game (all generations, no catch info)",g:0,grp:"No specific game",s:[],t:"",v:null,dx:null},
g("red","Red",1,"Gen 1",A,ST.oak),g("blue","Blue",1,"Gen 1",A,ST.oak),g("yellow","Yellow",1,"Gen 1",["Pikachu"],ST.yellow),
g("gold","Gold",2,"Gen 2",B,ST.elm),g("silver","Silver",2,"Gen 2",B,ST.elm),g("crystal","Crystal",2,"Gen 2",B,ST.elm),
g("ruby","Ruby",3,"Gen 3",C,ST.birch),g("sapphire","Sapphire",3,"Gen 3",C,ST.birch),g("emerald","Emerald",3,"Gen 3",C,ST.birch),g("firered","FireRed",3,"Gen 3",A,ST.oak),g("leafgreen","LeafGreen",3,"Gen 3",A,ST.oak),
g("diamond","Diamond",4,"Gen 4",D,ST.rowan),g("pearl","Pearl",4,"Gen 4",D,ST.rowan),g("platinum","Platinum",4,"Gen 4",D,ST.rowan),g("heartgold","HeartGold",4,"Gen 4",B,ST.elm),g("soulsilver","SoulSilver",4,"Gen 4",B,ST.elm),
g("black","Black",5,"Gen 5",U,ST.juniper),g("white","White",5,"Gen 5",U,ST.juniper),g("black-2","Black 2",5,"Gen 5",U,ST.juniper),g("white-2","White 2",5,"Gen 5",U,ST.juniper),
g("x","X",6,"Gen 6",K,ST.sycamore),g("y","Y",6,"Gen 6",K,ST.sycamore),g("omega-ruby","Omega Ruby",6,"Gen 6",C,ST.birch),g("alpha-sapphire","Alpha Sapphire",6,"Gen 6",C,ST.birch),
g("sun","Sun",7,"Gen 7",AL,ST.kukui),g("moon","Moon",7,"Gen 7",AL,ST.kukui),g("ultra-sun","Ultra Sun",7,"Gen 7",AL,ST.kukui),g("ultra-moon","Ultra Moon",7,"Gen 7",AL,ST.kukui),
g("lets-go-pikachu","Let's Go, Pikachu!",7,"Gen 7",["Pikachu"],ST.lgpe,0,["lgpe"]),g("lets-go-eevee","Let's Go, Eevee!",7,"Gen 7",["Eevee"],ST.lgpe,0,["lgpe"]),
g("sword","Sword",8,"Gen 8",GA,ST.galar,0,["swsh"]),g("shield","Shield",8,"Gen 8",GA,ST.galar,0,["swsh"]),g("bd","Brilliant Diamond",4,"Gen 8 remakes and Legends",D,ST.rowan,"brilliant-diamond"),g("sp","Shining Pearl",4,"Gen 8 remakes and Legends",D,ST.rowan,"shining-pearl"),g("la","Legends: Arceus",8,"Gen 8 remakes and Legends",HI,ST.hisui,"legends-arceus",["la"]),
g("scarlet","Scarlet",9,"Gen 9",PA,ST.paldea,0,["sv"]),g("violet","Violet",9,"Gen 9",PA,ST.paldea,0,["sv"])];
const OPEN=["legends-arceus","scarlet","violet"];// open-world games: no fixed gym order, timing follows wild levels
const OLD=["any","red","gold","ruby","firered","diamond","heartgold","black","x","omega-ruby","sun","sword","bd","la","scarlet"];
function gIndex(v){if(/^\d+$/.test(String(v)))v=OLD[+v]||"any";const i=G.findIndex(x=>x.k==v);return i<0?0:i}
const vn=x=>x.replace(/-/g," ").replace(/\b\w/g,c=>c.toUpperCase());
function whereTxt(p,d=0){const gm=G[gi];if(gm.s.includes(p.n))return gm.t;
const own=avStage(p),q=p.pre&&d<3?byName(p.pre):null,qa=q?(gm.s.includes(q.n)?{s:0}:avStage(q)):null;
if(qa&&(!own||qa.s<=own.s)){const e=(q.ev||[]).find(x=>x.to==p.n);return "Evolve "+q.n+(e?" ("+e.how+")":"")+". "+whereTxt(q,d+1)}
if(gm.v)return(p.L||{})[gm.v]||"Not found in the wild in this game. It may need a trade, event or other special method.";
return p.w||""}
const PRD=["Before Gym 1 (just started)","After Gym 1","After Gym 2","After Gym 3","After Gym 4","After Gym 5","After Gym 6","After Gym 7","After Gym 8","Victory Road / Elite Four","Post-game (after the Elite Four)"],CAP=[12,18,22,27,32,38,43,48,54,60];
// Legends: Arceus has areas and Nobles instead of gyms.
const PRLA=["Obsidian Fieldlands (just started)","Obsidian Fieldlands, after Kleavor","Crimson Mirelands","Crimson Mirelands, after Lilligant","Cobalt Coastlands","Coronet Highlands","Coronet Highlands, after Electrode","Alabaster Icelands","After Avalugg","Final story missions","Post-game"];
let PR=PRD,stage=0,comp=false,recN=6,wish=[];
function progOpts(){PR=G[gi].v=="legends-arceus"?PRLA:PRD;$("#prog").innerHTML=PR.slice(0,10).map((l,i)=>`<option value="${i}">${l} (about Lv ${CAP[i]})</option>`).join("");$("#prog").value=stage}
const BYN=new Map(P.map(p=>[p.n,p])),byName=n=>BYN.get(n),cl=(v,a,b)=>Math.max(a,Math.min(b,v||a));
function walk(n,l){let c=byName(n);for(let k=0;k<5;k++){const e=(c.ev||[]).find(x=>x.l&&x.l<=l&&evOk(byName(x.to),x)),nx=e&&byName(e.to);if(!nx)break;c=nx}return c}
function mk(n,l){return Object.assign({},walk(n,l),{lv:l,org:n})}
function setLv(i,v,keep){if(keep&&!v)return;const s=team[i];team[i]=mk(s.org,cl(v,1,100));render();if(keep){const el=$("#lv"+i);if(el)el.focus()}}
function evo(i,n){team[i]=mk(n,team[i].lv);render()}
function devo(i){const s=team[i];team[i]=mk(s.pre,s.lv);render()}
function evTxt(p){const a=[];if(p.pre){const q=byName(p.pre),e=q&&(q.ev||[]).find(x=>x.to==p.n);a.push("Evolves from "+p.pre+(e?" ("+e.how+")":""))}
const nx=(p.ev||[]).map(e=>e.to+" ("+e.how+")");a.push(nx.length?"Evolves into "+nx.join(" or "):"Final evolution");return a.join(". ")+"."}
function lvRow(p,i){const q=p.pre&&byName(p.pre),e0=q&&(q.ev||[]).find(x=>x.to==p.n);
const nx=(p.ev||[]).map(e=>e.l?(e.l>p.lv?`<button onclick="setLv(${i},${e.l})">Go to Lv ${e.l}: evolve into ${e.to}</button>`:""):`<button onclick="evo(${i},'${e.to}')">Evolve → ${e.to} (${e.how})</button>`).join(" ");
return `<div class="row"><label><b>Level</b> <input id="lv${i}" type="number" min="1" max="100" value="${p.lv}" style="width:70px" oninput="setLv(${i},+this.value,1)"></label><button onclick="setLv(${i},${p.lv-1})">−</button><button onclick="setLv(${i},${p.lv+1})">+</button>${p.org==p.n&&e0&&!e0.l?`<button onclick="devo(${i})">↩ Undo evolution</button>`:""}</div><div class="row">${nx}</div>`}
function setComp(v){comp=!!v;$("#mR").classList.toggle("on",!comp);$("#mC").classList.toggle("on",comp);$("#modehelp").textContent=comp?"Competitive: suggests the strongest final-evolution Pokémon, ignoring how hard they are to get.":"Realistic: suggests Pokémon you can actually catch by your story progress, evolved as far as your level allows.";render()}
function est(b){return{s:Math.max(0,Math.min(9,Math.ceil((tot(b)-260)/22))),w:0,est:1}}
// Other regions' starters handed out in the hometown (Emerald, ORAS...) are post-game gifts, not day-one catches.
function avStage(b){const gm=G[gi];if(gm.v){const s=(b.S||{})[gm.v];return s==null?null:{s:b.st&&!s?10:s,w:(b.e||{})[gm.v]||0,est:0}}return est(b)}
// Can n evolve here? e.v / e.x list the only / excluded versions for regional evolutions (Pikachu -> Alolan Raichu
// only in Alola, Stantler -> Wyrdeer only in Legends: Arceus). Games without a National Dex stay inside their Pokédex.
function evOk(n,e){const gm=G[gi];if(!n||(gen&&n.g>gen))return false;if(gm.k=="any")return true;
if(e&&((e.v&&!e.v.includes(gm.v))||(e.x&&e.x.includes(gm.v))))return false;
return !gm.dx||(n.S||{})[gm.v]!=null||(n.D||[]).some(d=>gm.dx.includes(d))}
// Every form n can reach by level l at story stage es. Branches (Eevee, Gloom...) each count. Stone evolutions from
// stage 3, friendship/other conditions from stage 1. Trade evolutions are skipped since they need a second player.
function forms(n,l,es){const r=[],go=(c,d)=>{const nx=d<4?(c.ev||[]).map(e=>({e,n:byName(e.to)})).filter(({e,n})=>evOk(n,e)&&!/trade/i.test(e.how)&&(e.l?e.l<=l:es>=(/^Use /.test(e.how)?3:1))):[];if(!nx.length)r.push(c);nx.forEach(x=>go(x.n,d+1))};go(byName(n),0);return r}
function pool(){const gm=G[gi],o=[],nolg=$("#nolg").checked;P.forEach(b=>{if((b.lg&&(nolg||!gm.v))||gm.s.includes(b.n)||(gen&&b.g>gen))return;const a=avStage(b);if(!a||(b.st&&a.est))return;
if(b.pre){if(!gm.v)return;const q=byName(b.pre),qa=q&&avStage(q);if(qa&&qa.s<=a.s)return}
const es=a.s<=stage?stage:Math.min(9,a.s+2);forms(b.n,CAP[es],es).forEach(p=>o.push({b,a,p}))});return o}
function finals(b,seen){const r=[];(b.ev||[]).forEach(e=>{const n=byName(e.to);if(!evOk(n,e)||/trade/i.test(e.how)||seen.includes(n.n))return;r.push(...finals(n,seen.concat(n.n)))});return r.length?r:[b]}
function compPool(){const o=[],seen=new Set();pool().forEach(x=>{if(seen.has(x.b.n))return;seen.add(x.b.n);finals(x.b,[x.b.n]).forEach(f=>o.push({b:x.b,a:x.a,p:f}))});return o}
function ratingRow(p){const r=roles(p),c=x=>Math.max(0,Math.min(100,Math.round(x))),A=p.at>=p.sa+15?"Physical":p.sa>=p.at+15?"Special":"Mixed",D=p.df>=p.sd+15?"Physical":p.sd>=p.df+15?"Special":"Even";
return `<div>${r.length?r.map(k=>`<span class="role">${ROLENAME[k]}</span>`).join(""):`<span class="role">Balanced all-rounder</span>`}</div><div class="small">Attacks: <b>${A}</b> (Atk ${p.at} / SpA ${p.sa}) · Defends: <b>${D}</b> (Def ${p.df} / SpD ${p.sd})<br>Power ${c((Math.max(p.at,p.sa)-50)/70*100)} · Toughness ${c((bulk(p)-180)/160*100)} · Speed ${c((p.sp-40)/70*100)} (out of 100)</div>`}
function topTypes(){return TY.map(t=>({t,f:fit({t:[t],hp:0,at:0,df:0,sa:0,sd:0,sp:0})})).sort((a,b)=>b.f.s-a.f.s).slice(0,3)}
function typeRecRender(){const el=$("#typerecs");if(!team.length){el.innerHTML=`<div class="empty">Add a Pokémon to see type-based suggestions.</div>`;return}
el.innerHTML=topTypes().map(({t,f})=>{const l=pool().filter(x=>x.a.s<=stage&&x.p.t.includes(t)&&!team.some(q=>q.org==x.b.n||q.n==x.p.n)).map(x=>Object.assign(x,{f:fit(x.p)})).sort((a,b)=>b.f.s-a.f.s).slice(0,3),tn=x=>TN[TY.indexOf(x)];
return `<h3 style="margin:10px 0 4px">${chs([t])} <span class=small>${f.res.length?"resists "+f.res.slice(0,3).map(tn).join(", ")+". ":""}${f.cov.length?"Hits "+f.cov.slice(0,3).map(tn).join(", ")+" hard.":""}</span></h3>`+(l.length?`<div class="grid">${l.map(x=>rcard(x,0)).join("")}</div>`:`<div class="small">No ${tn(t)} Pokémon you can catch yet at this point in the game. See "Plan ahead" below.</div>`)}).join("")}
function rank(c){c=c.filter(x=>!team.some(q=>q.org==x.b.n||q.n==x.p.n));let cut=0;
if(mode!="fix"){const[m,t]=RM[mode],v=c.map(x=>m(x.p)).filter(v=>v>0).sort((a,b)=>b-a);cut=Math.min(t,v[Math.floor(v.length*.4)]||t)}
return c.filter(x=>mode=="fix"||(RM[mode][0](x.p)>0&&RM[mode][0](x.p)>=cut)).map(x=>{const f=fit(x.p);return Object.assign(x,{f,sc:(team.length?f.s:0)+(mode=="fix"?0:ROLE[mode][1](x.p))+(mode=="fix"&&!team.length?tot(x.p)/60:0)})}).sort((a,b)=>b.sc-a.sc)}
function rcard(x,fut){const{b,p,f,a}=x,pl=wish.includes(b.n);
return `<div class="card"><h3>${img(p)}${p.n} <small>Gen ${p.g}</small></h3><div>${chs(p.t)}</div>${ratingRow(p)}
${comp&&!G[gi].v?"":`<div class="why"><span class="g">${fut?"Later:":"Catch:"}</span> ${b.n} ${a.est?"(exact spot not in our data)":"(from about Lv "+a.w+")"}${fut||comp?", available from "+PR[a.s]:""}${b.n!=p.n?". Evolves into "+p.n+(comp?"":" (shown at about Lv "+(fut?CAP[Math.min(9,a.s+2)]:CAP[stage])+")"):""}.</div>`}
${team.length&&f.res.length?`<div class="why"><span class="g">Covers:</span> resists ${f.res.map(t=>TN[TY.indexOf(t)]).join(", ")}, which your team is weak to.</div>`:""}
${team.length&&f.cov.length?`<div class="why"><span class="g">Adds punch</span> against ${f.cov.map(t=>TN[TY.indexOf(t)]).join(", ")}, which your team couldn't hit hard yet.</div>`:""}
${mode!="fix"?`<div class="why">Why: ${ROLENAME[mode]} (${mode=="fast"?"Speed "+p.sp:mode=="tank"?"bulk "+bulk(p):mode=="pdef"?"Defense "+p.df:mode=="sdef"?"Sp. Def "+p.sd:"top offense "+Math.max(p.at,p.sa)}).</div>`:""}
<div class="small">Nature: ${nat(p)}<br>EVs: ${evs(p)}<br>Evolution: ${evTxt(b)}<br>Get it: ${whereTxt(b)}</div>
<div class="row">${fut?"":`<button class="add" onclick="add('${b.n}',0,'${p.n}')">Add to team</button>`}<button onclick="wishT('${b.n}')">${pl?"★ Planned":"☆ Plan to catch"}</button></div></div>`}
function wishT(n){const i=wish.indexOf(n);if(i<0)wish.push(n);else wish.splice(i,1);render()}
function setMode(m){mode=m;recN=6;render();$("#recs").scrollIntoView({behavior:"smooth",block:"start"})}
function aheadRender(){const all=rank(pool().filter(x=>x.a.s>stage)).slice(0,6);
$("#ahead").innerHTML=all.length?`<div class="grid">${all.map(x=>rcard(x,1)).join("")}</div>`:`<div class="empty">Nothing further ahead for this game.</div>`;
$("#wishl").innerHTML=wish.length?wish.map(n=>{const b=byName(n);if(!b)return"";const a=avStage(b)||{s:99,none:1};return `<div class="de">${img(b)}<div><b>${b.n}</b><br><span class=small>${a.none?"Not catchable in this game":a.s<=stage?"You can catch it now":"Available around "+PR[a.s]}${a.est?" (estimated)":""}</span></div><button onclick="wishT('${b.n}')">Remove</button></div>`}).join(""):`<div class="small">Nothing yet. Press "Plan to catch" on any suggestion.</div>`}
// Report card has two graders: Casual (story playthrough) and Advanced / competitive (the original, stricter one).
let rmode="casual";try{rmode=localStorage.getItem("rmode")||"casual"}catch(e){}
function setRmode(m){rmode=m;try{localStorage.setItem("rmode",m)}catch(e){}rateRender()}
function rateRender(){const el=$("#rate");
const tg=`<div class="row" role="tablist"><b>Grading:</b><button class="${rmode=="casual"?"on":""}" onclick="setRmode('casual')">🎮 Casual playthrough</button><button class="${rmode=="adv"?"on":""}" onclick="setRmode('adv')">🏆 Advanced / competitive</button></div><p class="small">${rmode=="casual"?"Casual: grades how well your team handles the story (gyms, rivals, Elite Four). Focuses on type coverage, covering each other's weaknesses and overall strength for where you are in the game.":"Advanced / competitive: strict grading of stats, speed, bulk and physical/special balance, like you'd need for competitive battles."}</p>`;
if(!team.length){el.innerHTML=tg+`<div class="empty">Add a Pokémon to see your team report card.</div>`;return}
el.innerHTML=tg+(rmode=="casual"?rateCasual():rateAdv())}
const bars=S=>Object.entries(S).map(([k,x])=>`<div class="bar" style="grid-template-columns:170px 1fr 34px"><span>${k}</span><div><i class="s${x<40?1:x<60?2:x<80?3:4}" style="width:${x}%"></i></div><span>${x}</span></div>`).join("");
function rateCasual(){const n=team.length,avg=f=>team.reduce((s,p)=>s+f(p),0)/n,cp=x=>Math.max(0,Math.min(100,Math.round(x))),tn=t=>TN[TY.indexOf(t)],btn=(m,l)=>` <button onclick="setMode('${m}')">${l}</button>`;
const hit=new Set();team.forEach(q=>q.t.forEach(a=>TY.forEach(d=>{if(E[a][d]>1)hit.add(d)})));
// For each attacking type: how many teammates are weak to it vs. can take it (resist or immune).
const mt=TY.map(t=>({t,w:team.filter(p=>eff(t,p.t)>1).length,r:team.filter(p=>eff(t,p.t)<1).length}));
const prob=mt.filter(x=>x.w>=2&&x.w>x.r),open=mt.filter(x=>x.w>=1&&!x.r&&!(x.w>=2&&x.w>x.r)),safe=mt.filter(x=>x.r>=1&&!x.w);
// Strength is judged against what's normal for your point in the story, not against competitive Pokémon.
const want=comp?500:300+Math.min(stage,9)*22,avgT=avg(tot),phy=team.some(p=>p.at>=p.sa),spc=team.some(p=>p.sa>=p.at);
const S={"Type coverage":cp(hit.size/11*100),"Covering weaknesses":cp(100-18*prob.length-4*open.length),"Strength for your progress":cp(75+(avgT-want)/1.6),"Attack variety":phy&&spc?100:n<2?80:60,"Speed":cp((avg(p=>p.sp)-35)/55*100)};
const v=Object.values(S),all=Math.round(v[0]*.3+v[1]*.35+v[2]*.2+v[3]*.1+v[4]*.05),gr=all>=80?"A":all>=68?"B":all>=55?"C":all>=40?"D":"E";
const st=[],wk=[];
if(S["Type coverage"]>=75)st.push(`Your Pokémon's own-type attacks hit ${hit.size} of 18 types super effectively. Most gyms will have someone you can hit hard.`);
if(!prob.length)st.push("No type beats half your team. Your teammates cover each other well.");
if(S["Strength for your progress"]>=75)st.push("Your team is strong for this point in the story.");
if(phy&&spc&&n>1)st.push("You have both physical and special attackers, so stat-lowering moves won't shut you down.");
if(safe.length>=6)st.push("Your team safely takes hits from "+chs(safe.slice(0,8).map(x=>x.t))+".");
if(prob.length)wk.push("Watch out for "+chs(prob.map(x=>x.t))+": several teammates are weak to "+(prob.length>1?"these types":"this type")+" and few can take the hit. A gym leader or Elite Four member using "+(prob.length>1?"them":"it")+" could be trouble."+btn("fix","Find Pokémon that cover this"));
if(open.length>=3)wk.push("Nobody on your team resists "+chs(open.slice(0,6).map(x=>x.t))+". Not urgent, but one teammate that takes these hits would help.");
const miss=TY.filter(d=>!hit.has(d));if(S["Type coverage"]<75)wk.push("Your own-type attacks can't hit these super effectively yet: "+chs(miss.slice(0,6))+". Teaching a move of another type (TMs) also fixes this.");
if(S["Strength for your progress"]<50)wk.push("Your team is a bit weak for this point in the story. Evolving or swapping in stronger Pokémon will help."+btn("heavy","Find stronger Pokémon"));
if(!(phy&&spc)&&n>2)wk.push(`All your attackers are ${phy?"physical":"special"}. One ${phy?"special":"physical"} attacker would make the team more flexible.`+btn(phy?"spec":"phys",`Find ${phy?"special":"physical"} attackers`));
if(n<6)wk.push(`${n} of 6 slots filled. The grade covers the Pokémon you have so far.`);
const tr=topTypes(),fin=team.filter(p=>p.ev&&p.ev.length).length;
return `<div class="row"><h3>Casual grade: ${all}/100 (grade ${gr})</h3></div>`+bars(S)+
`<div class="k g">Strengths</div><div class="why">${st.join("<br>")||"Keep building. Strengths will show up as your team grows!"}</div><div class="k b">Things to work on</div><div class="why">${wk.map(x=>"• "+x).join("<br>")||"Nothing major. This team is ready for the story!"}</div>`+
`<div class="k">Types that would help most</div><div class="why">${tr.map(x=>chs([x.t])+` <span class=small>${x.f.res.length?"takes "+x.f.res.slice(0,3).map(tn).join(", ")+" hits. ":""}${x.f.cov.length?"Hits "+x.f.cov.slice(0,3).map(tn).join(", ")+" hard.":""}</span>`).join("<br>")}</div>`+(fin?`<div class="small">Note: ${fin} of your Pokémon can still evolve, so the team will get stronger as you level them up.</div>`:"")}
function rateAdv(){const n=team.length,avg=f=>team.reduce((s,p)=>s+f(p),0)/n,cp=x=>Math.max(0,Math.min(100,Math.round(x)));
const off=avg(p=>Math.max(p.at,p.sa)),bk=avg(bulk),spd=avg(p=>p.sp),ph=team.filter(p=>p.at>=p.sa+15).length,sp=team.filter(p=>p.sa>=p.at+15).length;
const hit=new Set();team.forEach(q=>q.t.forEach(a=>TY.forEach(d=>{if(E[a][d]>1)hit.add(d)})));
const tv=tw(),bad=TY.filter(t=>tv[t]>=2),mild=TY.filter(t=>tv[t]==1).length,miss=TY.filter(d=>!hit.has(d));
const S={"Offense power":cp((off-50)/70*100),"Bulk (toughness)":cp((bk-180)/160*100),"Speed":cp((spd-40)/70*100),"Type coverage":cp(hit.size/14*100),"Defensive balance":cp(100-18*bad.length-6*mild),"Physical/special mix":cp(100-Math.abs(ph-sp)/n*100),"Physical attack":cp((avg(p=>p.at)-40)/70*100),"Special attack":cp((avg(p=>p.sa)-40)/70*100),"Physical defense":cp((avg(p=>p.df)-40)/80*100),"Special defense":cp((avg(p=>p.sd)-40)/80*100)};
const v=Object.values(S),all=Math.round(v[0]*.2+v[1]*.15+v[2]*.15+v[3]*.2+v[4]*.2+v[5]*.1),gr=all>=80?"A":all>=65?"B":all>=50?"C":all>=35?"D":"E";
const st=[],wk=[],btn=(m,l)=>` <button onclick="setMode('${m}')">${l}</button>`;
if(S["Offense power"]>=70)st.push("Strong damage output.");if(S["Bulk (toughness)"]>=70)st.push("Sturdy team that can take hits.");if(S["Speed"]>=70)st.push("Fast team that usually moves first.");
if(S["Type coverage"]>=75)st.push(`Your attacks hit ${hit.size} of 18 types super effectively.`);if(S["Defensive balance"]>=75)st.push("Few shared weaknesses.");if(ph&&sp&&Math.abs(ph-sp)<=1)st.push("Good mix of physical and special attackers.");
if(S["Offense power"]<50)wk.push("Low damage."+btn("heavy","Find heavy hitters"));if(S["Speed"]<45)wk.push("Mostly slow, so enemies will often hit first."+btn("fast","Find fast Pokémon"));if(S["Bulk (toughness)"]<45)wk.push("Fragile team."+btn("tank","Find tanks"));
if(bad.length)wk.push("Several teammates share weaknesses to: "+chs(bad)+btn("fix","Fix weaknesses"));
if(S["Type coverage"]<60)wk.push("Little super-effective coverage against: "+chs(miss.slice(0,5)));
if(S["Special attack"]<S["Physical attack"]-15)wk.push("Your team leans physical. You need more special attackers."+btn("spec","Find special attackers"));
if(S["Physical attack"]<S["Special attack"]-15)wk.push("Your team leans special. You need more physical attackers."+btn("phys","Find physical attackers"));
if(S["Special defense"]<S["Physical defense"]-15)wk.push("Weak against special attacks. You need more special defense."+btn("sdef","Find special defense"));
if(S["Physical defense"]<S["Special defense"]-15)wk.push("Weak against physical attacks. You need more physical defense."+btn("pdef","Find physical defense"));
const tr=TY.map(t=>({t,f:fit({t:[t],hp:0,at:0,df:0,sa:0,sd:0,sp:0})})).sort((a,b)=>b.f.s-a.f.s).slice(0,3),tn=t=>TN[TY.indexOf(t)];
const typeRec=tr.map(x=>chs([x.t])+` <span class=small>${x.f.res.length?"resists "+x.f.res.slice(0,3).map(tn).join(", ")+". ":""}${x.f.cov.length?"Hits "+x.f.cov.slice(0,3).map(tn).join(", ")+" hard.":""}</span>`).join("<br>");
if(n<6)wk.push(`Only ${n} of 6 slots filled.`);
const fin=team.filter(p=>p.ev&&p.ev.length).length;
return `<div class="row"><h3>Advanced grade: ${all}/100 (grade ${gr})</h3></div>`+bars(S)+
`<div class="k g">Strengths</div><div class="why">${st.join("<br>")||"None yet. Keep building!"}</div><div class="k b">Weaknesses and advice</div><div class="why">${wk.map(x=>"• "+x).join("<br>")||"Nothing major. Nice team!"}</div><div class="k">Type recommendations</div><div class="why">Adding one of these types would help your team most:<br>${typeRec}</div>`+(fin?`<div class="small">Note: ${fin} of your Pokémon can still evolve, so the team will get stronger as you level them up.</div>`:"")}
function cands(){const gm=G[gi];if(comp)return gm.v?compPool():avail().map(p=>({b:p,p,a:{s:0,w:0,est:1}}));return pool().filter(x=>x.a.s<=stage)}
const tot=p=>p.hp+p.at+p.df+p.sa+p.sd+p.sp;
let gi=0,saved=[],cur=null;
$("#game").innerHTML=[...new Set(G.map(x=>x.grp))].map(gr=>`<optgroup label="${gr}">`+G.map((x,i)=>x.grp==gr?`<option value="${i}">${x.l}</option>`:"").join("")+`</optgroup>`).join("");
function setGame(i){gi=i;gen=G[i].g;try{localStorage.setItem("game",G[i].k)}catch(e){}team=team.filter(p=>!gen||p.g<=gen);progOpts();stnote();starters();any();render()}
function stnote(){const gm=G[gi];$("#stnote").textContent=gm.k=="any"?"You picked \"Any game\", so suggestions come from ALL generations and ignore where Pokémon can be caught. Choose a specific game to only see Pokémon you can really get in it.":
"Suggestions use this version's real route-by-route wild, gift and fishing data (version exclusives included). Trades and events are left out."+(OPEN.includes(gm.v)?" This game is open-world, so \"story progress\" is matched by your team's level and each area's wild levels.":" Story timing follows this game's route and gym order and can be off by a gym in a few spots.")}
function starters(){const n=G[gi].s,s=n.length?n.map(x=>P.find(p=>p.n==x)).filter(Boolean):P.filter(p=>p.st);$("#starters").innerHTML=s.map(p=>`<button onclick="add('${p.n}',5)">${img(p)}${p.n} ${chs(p.t)}</button>`).join("")}
function any(){const q=$("#q").value.toLowerCase().trim(),r=q?P.filter(p=>(!gen||p.g<=gen)&&p.n.toLowerCase().includes(q)).slice(0,8):[];$("#qres").innerHTML=r.map(p=>`<button onclick="add('${p.n}');$('#q').value='';any()">${img(p)}${p.n} ${chs(p.t)}${G[gi].v&&!G[gi].s.includes(p.n)&&!avStage(p)&&!(p.pre&&avStage(byName(p.pre)))?"<span class=small> (not catchable in this game)</span>":""}</button>`).join("")||(q?"<span class=small>No match. Check the filter boxes below (legendary / final evolutions).</span>":"")}
// Without the local server (shared copy / web link), teams are saved in this browser instead of data/teams.csv.
async function loadTeams(){if(OFF){$("#stopbtn").style.display="none";try{saved=JSON.parse(localStorage.getItem("teams")||"[]")}catch(e){saved=[]}
$("#teams .sub").textContent="Name your team and save it. Teams are saved on this device and browser only.";teamList();return}
try{saved=await(await fetch("/api/teams")).json()}catch(e){$("#tmsg").textContent="Saving needs the server. Start the site with start.bat.";saved=[]}teamList()}
function teamList(){$("#tsel").innerHTML=`<option value="">Saved teams (${saved.length})</option>`+saved.map(t=>`<option value="${t.id}"${t.id==cur?" selected":""}>${t.name} (${t.members.filter(m=>m[0]!="*").length})</option>`).join("")}
async function put(){if(OFF){try{localStorage.setItem("teams",JSON.stringify(saved));return 1}catch(e){$("#tmsg").textContent="This browser is blocking saving (private mode?).";return}}try{await fetch("/api/teams",{method:"POST",body:JSON.stringify(saved)});return 1}catch(e){$("#tmsg").textContent="Could not save. Is the server running?"}}
async function saveTeam(){const name=$("#tname").value.trim();if(!name||!team.length){$("#tmsg").textContent="Give the team a name and add at least one Pokémon.";return}
let t=saved.find(x=>x.id==cur);if(!t){t={id:String(Date.now())};saved.push(t)}
Object.assign(t,{name,game:G[gi].k,members:team.map(p=>p.org+":"+p.lv).concat(wish.map(n=>"*"+n))});cur=t.id;if(await put())$("#tmsg").textContent="Saved!";teamList()}
function loadTeam(id){const t=saved.find(x=>x.id==id);if(!t){cur=null;return}cur=t.id;$("#tname").value=t.name;const gx=gIndex(t.game);setGame(gx);$("#game").value=gx;wish=t.members.filter(m=>m[0]=="*").map(m=>m.slice(1));team=t.members.filter(m=>m[0]!="*").map(m=>{const[n,l]=m.split(":");return byName(n)?mk(n,+l||(comp?50:CAP[stage])):null}).filter(Boolean);render();$("#tmsg").textContent="Loaded. Edit, then press Save team."}
async function delTeam(){if(!cur)return;saved=saved.filter(x=>x.id!=cur);await put();newTeam();$("#tmsg").textContent="Deleted."}
function newTeam(){cur=null;team=[];wish=[];$("#tname").value="";teamList();render()}
async function stopServer(){try{await fetch("/api/shutdown",{method:"POST"})}catch(e){}document.body.innerHTML="<p style='padding:30px;font-size:1.2rem'>Server stopped. You can close this tab.</p>";window.close()}
// ===== Step 2, Search & Pokédex tab: find Pokémon by name, type and strength =====
const SROLE=[["heavy","Heavy hitter"],["fast","Fast"],["tank","Defensive / tank"],["phys","Physical attacker"],["spec","Special attacker"],["pdef","Physical defense"],["sdef","Special defense"]];
const SSORT=[["best","Best match"],["tot","Total stats"],["hp","HP"],["at","Attack"],["df","Defense"],["sa","Sp. Atk"],["sd","Sp. Def"],["sp","Speed"],["num","Pokédex number"],["n","Name (A-Z)"]];
let tab="v",sRoles=[],sN=24;
// Plain-English words -> strengths. Longer phrases go first so "physical defense" isn't read as "physical attacker".
const WORDS=[[/\bsp[ -]*(def|defen[cs]e)\b/g,"sdef"],[/\bsp[ -]*(atk|att|attack)\b/g,"spec"],
[/\bphysical(ly)?[ -]*(def|defen[cs]e|defensive|wall|tank|bulk)\b/g,"pdef"],[/\bspecial(ly)?[ -]*(def|defen[cs]e|defensive|wall|tank|bulk)\b/g,"sdef"],
[/\bphysical(ly)?([ -]*(atk|attack(er|ers|ing|s)?|hitter|sweeper|offen[cs]e|offensive))?\b/g,"phys"],[/\bspecial(ly)?([ -]*(atk|attack(er|ers|ing|s)?|hitter|sweeper|offen[cs]e|offensive))?\b/g,"spec"],
[/\b(defen[cs]e|defensive|tank|tanks|tanky|bulky|bulk|wall|walls|sturdy|tough)\b/g,"tank"],[/\b(fast|faster|fastest|speedy|quick|speed)\b/g,"fast"],
[/\b(strong|strongest|heavy|hitters?|power|powerful|offensive|offen[cs]e|attackers?|attack|hard[ -]?hitting|damage|sweepers?)\b/g,"heavy"],[/\batk\b/g,"phys"],[/\bdef\b/g,"pdef"]];
const FILL=/\b(pok[eé]mon|mons?|types?|with|and|or|a|an|the|good|great|best|top|in|for|of|that|is|are|which|me|show|find|i|want|need|high|very|really|some|any)\b/g;
function sParse(q){q=" "+q.toLowerCase().replace(/[^a-z0-9é -]/g," ")+" ";const r={t:[],r:[],lg:false,gen:0};
q=q.replace(/\b(legendar(y|ies)|mythicals?|legends?)\b/g,()=>{r.lg=true;return" "}).replace(/\bgen(eration)?\s*(\d)\b/g,(m,a,d)=>{r.gen=+d;return" "});
WORDS.forEach(([re,k])=>{q=q.replace(re,()=>{if(!r.r.includes(k))r.r.push(k);return" "})});
TN.forEach((n,i)=>{q=q.replace(new RegExp("\\b"+n.toLowerCase()+"(-?types?)?s?\\b","g"),()=>{if(!r.t.includes(TY[i]))r.t.push(TY[i]);return" "})});
r.name=q.replace(FILL," ").replace(/\s+/g," ").trim();return r}
// Everything you can get in the chosen game at any point: wild/gift catches plus everything they evolve into
// (trade evolutions included but flagged). a = earliest story stage. Cached per game.
let GMC={};
function gameMap(){if(GMC[gi])return GMC[gi];const m=new Map(),q=[];
P.forEach(b=>{if(gen&&b.g>gen)return;const a=avStage(b);if(a){m.set(b.n,{p:b,a});q.push(b)}});
G[gi].s.forEach(n=>{const b=byName(n);if(b){m.set(n,{p:b,a:{s:0,w:5,est:0}});q.push(b)}});
while(q.length){const c=q.shift(),cx=m.get(c.n);(c.ev||[]).forEach(e=>{const n=byName(e.to);if(!evOk(n,e)||m.has(n.n))return;m.set(n.n,{p:n,a:cx.a,tr:cx.tr||/trade/i.test(e.how)});q.push(n)})}
return GMC[gi]=m}
function sItems(sc){if(sc=="all"||G[gi].k=="any")return P.map(p=>({p,a:G[gi].k=="any"?null:(gameMap().get(p.n)||{}).a}));
if(sc=="now"){const m=new Map();pool().filter(x=>x.a.s<=stage).forEach(x=>[x.b,x.p].forEach(p=>{if(!m.has(p.n))m.set(p.n,{p,a:x.a})}));return[...m.values()]}
return[...gameMap().values()]}
function sRun(keep){if(!keep)sN=24;const q=sParse($("#sq").value),ts=[...new Set([$("#st1").value,$("#st2").value,...q.t].filter(Boolean))],rs=[...new Set([...sRoles,...q.r])],
sc=$("#sscope").value,nm=q.name.replace(/[^a-z0-9]/g,""),lg=$("#slg").checked||nm,norm=s=>s.toLowerCase().replace(/[^a-z0-9]/g,"");
// Typing "legendary" shows only legendaries; the checkbox just lets them in.
let c=sItems(sc).filter(({p})=>ts.every(t=>p.t.includes(t))&&(q.lg?p.lg:lg||!p.lg)&&(!$("#sfin").checked||!(p.ev||[]).length)&&($("#srf").checked||!p.rf)&&(!q.gen||p.g==q.gen)&&(!nm||norm(p.n).includes(nm)));
// Each strength keeps Pokémon that meet the ideal stat, or the top 40% of matches if few do (so searches never come up empty).
rs.forEach(k=>{const m=RM[k][0],v=c.map(x=>m(x.p)).filter(v=>v>0).sort((a,b)=>b-a),cut=Math.min(RM[k][1],v[Math.floor(v.length*.4)]||RM[k][1]);c=c.filter(x=>m(x.p)>0&&m(x.p)>=cut)});
const so=$("#ssort").value,key=so=="best"?x=>rs.reduce((s,k)=>s+RM[k][0](x.p)/RM[k][1]*10,0)+(team.length?fit(x.p).s:0)+tot(x.p)/100:so=="tot"?x=>tot(x.p):so=="num"?x=>-(x.p.num||x.p.id):x=>x.p[so];
c.sort(so=="n"?(a,b)=>a.p.n.localeCompare(b.p.n):(a,b)=>key(b)-key(a));
const und=[...ts.map(t=>TN[TY.indexOf(t)]+" type"),...rs.map(k=>SROLE.find(r=>r[0]==k)[1]),...(q.lg?["legendary"]:[]),...(q.gen?["Gen "+q.gen]:[]),...(nm?[`name has "${q.name}"`]:[])];
const where=G[gi].k=="any"||sc=="all"?"in the full Pokédex":sc=="now"?"you can have at your story point ("+PR[stage].replace(/ \(.*/,"")+")":"you can get in "+G[gi].l;
$("#sinfo").innerHTML=(und.length?`<div class="understood">Looking for: ${und.map(x=>`<span>${x}</span>`).join("")}</div>`:"")+`<b>${c.length}</b> Pokémon ${where}.`;
$("#sres").innerHTML=c.length?`<div class="grid">${c.slice(0,sN).map(scard).join("")}</div>`+(c.length>sN?`<div class="row"><button onclick="sN+=24;sRun(1)">Show 24 more</button></div>`:""):
`<div class="empty">Nothing matched.${sc!="all"?" Try <b>Show: Every Pokémon</b>, or remove a filter.":" Try removing a filter."}</div>`}
function scard(x){const{p,a,tr}=x,gm=G[gi],m=mm(p),f=team.length?fit(p):null,tn=t=>TN[TY.indexOf(t)],inT=team.some(q=>q.n==p.n||q.org==p.n);
const S6=[["HP",p.hp],["Atk",p.at],["Def",p.df],["SpA",p.sa],["SpD",p.sd],["Spe",p.sp]];
const when=!a?"":a.s==0?"Available from the start":a.s<=stage?"Available now":a.s>=10?"Post-game":"Available from: "+PR[a.s];
const get=gm.k=="any"?`<div class="small">${p.w||""}</div>`:a?`<div class="why"><span class="g">${when}</span>${tr?" · needs a trade to evolve":""}</div><div class="small">Get it: ${whereTxt(p)}</div>`:`<div class="why"><span class="b">Not obtainable in ${gm.l}</span></div>`;
return `<div class="card"><h3>${img(p)}${p.n} <small>#${p.num||p.id} · Gen ${p.g}</small></h3><div>${chs(p.t)}</div>
<div class="stat6">${S6.map(([l,v])=>`<div class="${v>=100?"hi":v<50?"lo":""}">${l}<b>${v}</b></div>`).join("")}<div>Total<b>${tot(p)}</b></div></div>
<div>${roles(p).map(k=>`<span class="role">${ROLENAME[k]}</span>`).join("")||`<span class="role">Balanced all-rounder</span>`}</div>
${f&&f.res.length?`<div class="why"><span class="g">Covers:</span> resists ${f.res.map(tn).join(", ")}, which your team is weak to.</div>`:""}
${f&&f.cov.length?`<div class="why"><span class="g">Adds punch</span> against ${f.cov.map(tn).join(", ")}.</div>`:""}${get}
<details><summary>More info</summary><div class="k b">Weak to</div><div>${m.x4.length?chs(m.x4)+" <span class=small>(×4)</span><br>":""}${chs(m.x2)||"<span class=small>Nothing!</span>"}</div>
<div class="k">Resists</div><div>${chs(m.h)||"—"}${m.z.length?"<br>Immune: "+chs(m.z):""}</div><div class="k">Best nature</div><div class="small">${nat(p)}</div>
<div class="k">Suggested EVs</div><div class="small">${evs(p)}</div><div class="k">Evolution</div><div class="small">${evTxt(p)}</div></details>
<div class="row">${inT?`<span class="small">✔ On your team</span>`:`<button class="add" onclick="add('${p.n}')"${team.length>=6?" disabled":""}>Add to team</button>`}<button onclick="wishT('${p.n}')">${wish.includes(p.n)?"★ Planned":"☆ Plan to catch"}</button></div></div>`}
function sRoleT(k){const i=sRoles.indexOf(k);if(i<0)sRoles.push(k);else sRoles.splice(i,1);sRolesRender();sRun()}
function sRolesRender(){$("#sroles").innerHTML="<b>Strength:</b>"+SROLE.map(([k,l])=>`<button class="${sRoles.includes(k)?"on":""}" onclick="sRoleT('${k}')">${l}</button>`).join("")}
function sReset(){$("#sq").value="";$("#st1").value=$("#st2").value="";$("#ssort").value="best";sRoles=[];sRolesRender();sRun()}
function setTab(t){tab=t;$("#paneV").hidden=t!="v";$("#paneS").hidden=t!="s";["V","S"].forEach(k=>{const b=$("#tab"+k),on=t==k.toLowerCase();b.classList.toggle("on",on);b.setAttribute("aria-selected",on)});if(t=="s")sRun()}
function openSearch(){const s=$("#find");s.classList.remove("shut");setTab("s");$("#sscope").value="all";sRun();s.scrollIntoView({behavior:"smooth",block:"start"});$("#sq").focus({preventScroll:true})}
$("#st1").innerHTML=$("#st2").innerHTML=`<option value="">Any type</option>`+TY.map((t,i)=>`<option value="${t}">${TN[i]}</option>`).join("");
$("#ssort").innerHTML=SSORT.map(([k,l])=>`<option value="${k}">${l}</option>`).join("");sRolesRender();
// Every section folds up when you click its heading (remembered between visits).
document.querySelectorAll("main>section").forEach((s,i)=>{const h=s.querySelector(":scope>h2");if(!h)return;h.classList.add("tog");h.tabIndex=0;h.setAttribute("role","button");
let shut=false;try{shut=localStorage.getItem("shut"+i)=="1"}catch(e){}
const set=v=>{s.classList.toggle("shut",v);h.setAttribute("aria-expanded",!v);try{localStorage.setItem("shut"+i,v?"1":"0")}catch(e){}};set(shut);
h.addEventListener("click",e=>{if(!e.target.closest("button,select,input,a"))set(!s.classList.contains("shut"))});
h.addEventListener("keydown",e=>{if(e.key=="Enter"||e.key==" "){e.preventDefault();set(!s.classList.contains("shut"))}})});
if(!P.some(p=>p.ev&&p.ev.length)||!P.some(p=>p.L))document.querySelector("header").insertAdjacentHTML("afterend",'<section style="border-color:#c72f3a"><b>Your data file is out of date.</b> Evolutions and game-progress suggestions need the newer data. Run <code>python data\\make_data.py</code>, then refresh this page.</section>');
{let k="red";try{k=localStorage.getItem("game")||"red"}catch(e){}const x=gIndex(k);gi=x;gen=G[x].g;$("#game").value=x;team=team.filter(p=>!gen||p.g<=gen)}
progOpts();stnote();setSkin(skin);setTab("v");setComp(0);pickType("fir");starters();any();render();loadTeams();