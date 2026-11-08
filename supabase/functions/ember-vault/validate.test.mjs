import test from 'node:test';import assert from 'node:assert/strict';import {validateRequest,validPayload}from './validate.mjs';
const key='ember_'+'a'.repeat(64);
test('requires a full recovery credential and valid revision before any database access',()=>{
 assert.equal(validateRequest({site:'puzzle',action:'load',revision:0},''),'unauthorized');
 assert.equal(validateRequest({site:'puzzle',action:'load',revision:-1},key),'invalid_request');
 assert.equal(validateRequest({site:'unknown',action:'load',revision:0},key),'invalid_request');
 assert.equal(validateRequest({site:'puzzle',action:'load',revision:0},key),null);
});
test('City restore cannot write arbitrary local-storage keys or credentials',()=>{
 assert(validPayload('city',{schema:1,storage:{'ember-city-observation-v1':'{"version":1}'}}));
 for(const k of ['ember-cloud-vault-city-v1','posthog','__proto__','session','ember-city-card-session:untrusted'])assert(!validPayload('city',{schema:1,storage:JSON.parse('{"'+k+'":"{}"}')}));
 assert(!validPayload('city',{schema:1,storage:{'ember-city-observation-v1':'not JSON'}}));
});
test('Cinema can restore only valid answered states, not an incomplete final result',()=>{
 const p={schema:1,data:{answers:[0,1,2],scene:3,resultIndex:0,confirmed:true}};assert(validPayload('cinema',p));p.data.answers[1]=null;assert(!validPayload('cinema',p));p.data.scene=1;assert(validPayload('cinema',p));p.data.answers[0]=100;assert(!validPayload('cinema',p));
});
