import {MAX_BYTES,validateRequest} from './validate.mjs';
const rate=new Map<string,{minute:number,count:number}>();
const origins=new Set(['https://puzzle.mariustang.com','https://city.mariustang.com','https://cinema.mariustang.com','https://ember-idea-puzzle.vercel.app','https://ember-city-observer.vercel.app','https://ember-film-experiment.vercel.app']);
Deno.serve(async(req:Request)=>{
 const origin=req.headers.get('origin')||'';
 const allowed=!origin||origins.has(origin)||/^http:\/\/127\.0\.0\.1:(4173|4174|4175|8000)$/.test(origin);
 const headers={'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Vary':'Origin',...(origin&&allowed?{'Access-Control-Allow-Origin':origin}:{}),'Access-Control-Allow-Headers':'apikey, authorization, content-type, x-ember-recovery-key','Access-Control-Allow-Methods':'POST, OPTIONS'};
 const json=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers});
 if(!allowed)return json({error:'origin_not_allowed'},403);
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
 if(req.method!=='POST')return json({error:'method_not_allowed'},405);
 try{
  const reader=req.body?.getReader();let size=0,parts:Uint8Array[]=[];
  if(reader)while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>MAX_BYTES){await reader.cancel();return json({error:'payload_too_large'},413)}parts.push(value)}
  let bytes=new Uint8Array(size),i=0;for(const part of parts){bytes.set(part,i);i+=part.length}
  let body;try{body=JSON.parse(new TextDecoder().decode(bytes))}catch{return json({error:'invalid_request'},400)}
  const key=req.headers.get('x-ember-recovery-key')||'';
  const invalid=validateRequest(body,key);if(invalid)return json({error:invalid},invalid==='unauthorized'?401:400);
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body.site+':'+key));
  const hash=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
  const url=Deno.env.get('SUPABASE_URL'),secret=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if(!url||!secret)return json({error:'storage_unavailable'},503);
  const minute=Math.floor(Date.now()/60000),bucket=rate.get(hash);
  if(bucket?.minute===minute){bucket.count++;if(bucket.count>30)return json({error:'rate_limited'},429)}else rate.set(hash,{minute,count:1});
  if(rate.size>10000)for(const [k,v]of rate)if(v.minute<minute-1)rate.delete(k);
  const filter=new URLSearchParams({site:'eq.'+body.site,owner_hash:'eq.'+hash});
  const h={'Content-Type':'application/json',apikey:secret,Authorization:'Bearer '+secret,Prefer:'return=representation'};
  if(body.action==='load'){
   filter.set('select','payload,revision,updated_at');
   const r=await fetch(url+'/rest/v1/ember_cloud_documents?'+filter,{headers:h,signal:AbortSignal.timeout(15000)});
   if(!r.ok)return json({error:'storage_unavailable'},503);
   const rows=await r.json();return json(rows.length?{found:true,payload:rows[0].payload,revision:rows[0].revision,updatedAt:rows[0].updated_at}:{found:false,revision:0});
  }
  if(body.action==='save'&&(body.revision??0)===0){
   const r=await fetch(url+'/rest/v1/ember_cloud_documents',{method:'POST',headers:h,body:JSON.stringify({site:body.site,owner_hash:hash,payload:body.payload}),signal:AbortSignal.timeout(15000)});
   if(r.status===409)return json({error:'conflict'},409);
   if(!r.ok)return json({error:'storage_unavailable'},503);
   const [row]=await r.json();return json({saved:true,revision:row.revision,updatedAt:row.updated_at});
  }
  filter.set('revision','eq.'+(body.revision??0));
  const r=await fetch(url+'/rest/v1/ember_cloud_documents?'+filter,{method:body.action==='delete'?'DELETE':'PATCH',headers:h,...(body.action==='save'?{body:JSON.stringify({payload:body.payload,revision:body.revision+1,updated_at:new Date().toISOString()})}:{}),signal:AbortSignal.timeout(15000)});
  if(!r.ok)return json({error:'storage_unavailable'},503);
  const rows=await r.json();if(!rows.length){if(body.action==='delete'&&(body.revision??0)===0)return json({deleted:true,revision:0});return json({error:'conflict'},409)}
  return json(body.action==='delete'?{deleted:true,revision:0}:{saved:true,revision:rows[0].revision,updatedAt:rows[0].updated_at});
 }catch{return json({error:'storage_unavailable'},503)}
});
