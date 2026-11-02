"use strict";
const $ = id => document.getElementById(id);
const dollars = v => v === null || v === undefined || !Number.isFinite(Number(v)) ? "—" : new Intl.NumberFormat("en-US", {style:"currency", currency:"USD", maximumFractionDigits:Math.abs(Number(v))>0&&Math.abs(Number(v))<.01?4:2}).format(Number(v));
const signed = v => v === null || v === undefined ? "—" : (Number(v) > 0 ? "+" : "") + dollars(v);
const time = value => value ? new Date(value).toLocaleString([], {month:"short",day:"numeric",hour:"numeric",minute:"2-digit",second:"2-digit"}) : "Unknown";
function color(el, value) { el.classList.remove("positive", "negative"); if (value !== null && Number(value) !== 0) el.classList.add(Number(value) > 0 ? "positive" : "negative"); }
function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function svgNode(tag, attrs) { const n = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v)); return n; }
function chart(history) {
  const host = $("chart"); host.replaceChildren();
  if (history.length < 2) { host.append(node("p","At least two saved snapshots are needed.","empty")); return; }
  const values = history.map(h => Number(h.equity_usd));
  const W=700,H=200,L=0,R=64,T=9,B=20;
  const min=Math.min(...values),max=Math.max(...values),pad=Math.max((max-min)*.25,Math.abs(values[0])*.005,.05);
  const low=min-pad,high=max+pad;
  const y=v=>T+(high-v)/(high-low)*(H-T-B);
  const x=i=>L+i/(values.length-1)*(W-R-L);
  const svg=svgNode("svg",{viewBox:`0 0 ${W} ${H}`,role:"img","aria-label":"Saved equity snapshots in time order"});
  for(let i=0;i<4;i++){
    const val=low+(high-low)*i/3,yy=y(val);
    svg.append(svgNode("line",{x1:0,y1:yy,x2:W-R,y2:yy,stroke:"#2b352d","stroke-dasharray":"3 5"}));
    const label=svgNode("text",{x:W-R+10,y:yy+3,fill:"#94a18c","font-size":10});label.textContent=dollars(val);svg.append(label);
  }
  const line=values.map((v,i)=>`${i===0?"M":"L"}${x(i)},${y(v)}`).join(" ");
  svg.append(svgNode("path",{d:`${line} L${x(values.length-1)},${H-B} L0,${H-B} Z`,fill:"#253520",opacity:.6}));
  svg.append(svgNode("path",{d:line,fill:"none",stroke:"#bcf17c","stroke-width":2.5,"stroke-linejoin":"round"}));
  const circle=svgNode("circle",{cx:x(values.length-1),cy:y(values.at(-1)),r:4,fill:"#bcf17c"});
  const tip=svgNode("title",{});tip.textContent=`${time(history.at(-1).at)}: $${Number(history.at(-1).equity_usd).toFixed(6)}`;circle.append(tip);svg.append(circle);host.append(svg);
}
function render(s) {
  $("mode").textContent=s.synthetic?"SYNTHETIC DEMO":s.mode.toUpperCase();
  $("equity").textContent=dollars(s.equity_usd); $("cash").textContent=dollars(s.cash_usd); $("exposure").textContent=dollars(s.exposure_usd);
  $("day-pnl").textContent=signed(s.day_pnl_usd);color($("day-pnl"),s.day_pnl_usd);
  $("initial-pnl").textContent=s.initial_pnl_usd===null?"Experiment change unknown":`${signed(s.initial_pnl_usd)} since first snapshot`;
  $("equity").title=s.equity_usd===null?"Unknown":`$${s.equity_usd}`;
  const age=s.updated_at?(Date.now()-new Date(s.updated_at).getTime())/1000:Infinity;
  $("status-dot").style.background=s.halt_reason?"#e3bc70":age<30?"#bcf17c":"#7e8d77";
  $("session-label").textContent=s.halt_reason?"New entries paused":s.updated_at?(age<30?"Recent saved snapshot":"Saved snapshot is stale"):"No saved snapshot";
  $("updated").textContent=time(s.updated_at);
  const notice=$("notice");notice.classList.toggle("alert",!!s.halt_reason||!s.synthetic);
  notice.textContent=s.halt_reason?`Entries paused: ${s.halt_reason}. Pending orders and holdings still need attention.`:s.synthetic?"Synthetic example · the displayed $50 balance and fills are made-up software checks. This screen shows no evidence of trading profitability.":s.mode==="live"?`LIVE records · this desk cannot submit orders. Live submission is ${s.live_enabled?"enabled":"disabled"} in configuration. Refreshing this page does not refresh the broker snapshot.`:"PAPER records · simulated performance can differ from live execution. This page reads saved data only.";
  $("point-count").textContent=`${s.history.length} saved samples`;
  chart(s.history);
  $("chart-range").textContent=s.history.length?`${time(s.history[0].at)} → ${time(s.history.at(-1).at)}`:"Waiting for data";
  const policies=[["Experiment capital cap",s.policy.capital_cap_usd],["Protected equity floor",s.policy.protected_floor_usd],["Maximum order",s.policy.order_cap_usd],["Daily entry-halt threshold",s.policy.daily_entry_halt_usd],["Total entry-halt threshold",s.policy.total_entry_halt_usd]];
  $("policy").replaceChildren(...policies.map(([label,value])=>{const d=node("div");d.append(node("dt",label),node("dd",dollars(value)));return d;}));
  const report=s.research,test=report?.splits?.test;
  $("research-badge").textContent=report?(report.research_checks_passed?"FILTER PASSED":"MORE EVIDENCE"):"UNKNOWN";
  const rstats=[[test?.trades??"—","Completed test trades"],[test?.win_rate===null||test?.win_rate===undefined?"—":`${(test.win_rate*100).toFixed(1)}%`,"Test win rate"],[dollars(test?.net_pnl_usd),"Net test P&L"]];
  $("research-stats").replaceChildren(...rstats.map(([v,l])=>{const d=node("div",undefined,"research-stat");d.append(node("strong",String(v)),node("small",l));return d;}));
  $("research-description").textContent=report?`${report.strategy_version} · ${test?.active_days??0} active test days · extra execution stress: ${report.extra_cost_bps_per_side} bps per side.`:"No test report imported. Knowledge files and agent scores do not establish a trading edge.";
  $("research-failures").replaceChildren(...(report?.failures??[]).slice(0,5).map(f=>node("li",f)));
  $("lesson-count").textContent=`${s.lessons.length} shown`;
  $("lessons").replaceChildren(...(s.lessons.length?s.lessons.map(l=>{const d=node("div",undefined,"lesson");d.append(node("strong",l.hypothesis),node("small",`${l.status.toUpperCase()} · ${l.strategy_version}`),node("small",l.evidence_ref));return d;}):[node("p","No lessons recorded.","muted")]));
  $("order-rows").replaceChildren(...s.orders.map(o=>{const tr=node("tr");tr.append(node("td",time(o.created_at)),node("td",o.symbol,"symbol"));const side=node("td");side.append(node("span",o.side.toUpperCase(),`side ${o.side}`));tr.append(side,node("td",o.side==="buy"?dollars(o.notional_usd):"Close held quantity"),node("td",o.strategy_version),node("td",o.status,"order-status"));return tr;}));
  $("empty-orders").hidden=s.orders.length>0;
}
let busy=false;
async function refresh(){
  if(busy)return;busy=true;$("refresh").disabled=true;
  try{const r=await fetch("/api/state",{cache:"no-store"});if(!r.ok)throw new Error("Local records unavailable");render(await r.json());}
  catch(e){$("notice").textContent="Local records are unavailable. No order has been submitted by this page.";$("notice").classList.add("alert");}
  finally{busy=false;$("refresh").disabled=false;}
}
$("refresh").addEventListener("click",refresh);refresh();setInterval(refresh,10000);
