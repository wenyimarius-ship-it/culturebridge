export const MAX_BYTES=262144;
export function validPayload(site,p){
 if(!p||p.schema!==1||typeof p!=='object'||Array.isArray(p))return false;
 if(site==='cinema'){
  const d=p.data;return !!d&&Array.isArray(d.answers)&&d.answers.length===3&&d.answers.every(v=>v===null||Number.isInteger(v)&&v>=0&&v<=2)&&Number.isInteger(d.scene)&&d.scene>=-1&&d.scene<=3&&(d.scene!==3||d.answers.every(v=>v!==null))&&Number.isInteger(d.resultIndex)&&d.resultIndex>=0&&d.resultIndex<=10000&&typeof d.confirmed==='boolean';
 }
 if(site==='puzzle')return !!p.data&&p.data.version===1&&Array.isArray(p.data.cards)&&p.data.cards.length<=2000&&Array.isArray(p.data.groups);
 if(site==='city'){
  if(!p.storage||typeof p.storage!=='object'||Array.isArray(p.storage)||Object.keys(p.storage).length>200)return false;
  return Object.entries(p.storage).every(([key,value])=>/^(ember-city-(observation|small-cards|route-records)-v1|ember-city-card-session:[a-f0-9-]{36})$/.test(key)&&typeof value==='string'&&(()=>{try{let x=JSON.parse(value);return !!x&&typeof x==='object'}catch{return false}})());
 }
 return false;
}
export function validateRequest(body,key){
 if(!/^ember_[a-f0-9]{64}$/.test(key||''))return 'unauthorized';
 if(!body||!['puzzle','city','cinema'].includes(body.site)||!['load','save','delete'].includes(body.action)||!Number.isSafeInteger(body.revision??0)||(body.revision??0)<0)return 'invalid_request';
 if(body.action==='save'&&!validPayload(body.site,body.payload))return 'invalid_payload';
 return null;
}
