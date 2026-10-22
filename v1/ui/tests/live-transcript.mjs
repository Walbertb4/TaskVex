/** Balon tekilliği, eski/sırasız bildirim, güvenli metin ve kesilme korunumu. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
class Element {
  constructor(){this.children=[];this.dataset={};this.value='';}
  append(...children){for(const child of children)child.parentNode=this;this.children.push(...children);}
  insertBefore(child,before){child.parentNode=this;this.children.splice(this.children.indexOf(before),0,child);}
  set textContent(value){this.value=value;this.children=[];}
  get textContent(){return this.value+this.children.map(c=>c.textContent).join('');}
}
const panel=new Element();
globalThis.document={getElementById:()=>panel,createElement:()=>new Element()};
const source=fs.readFileSync(new URL('../js/live_transcript.js',import.meta.url),'utf8');
const {liveTranscript:t}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const packet=(id,role,text,sequence)=>({request_id:id,role,text,sequence});
t.begin('one');
assert.ok(t.chunk(packet('one','u','Mer',1)));
assert.ok(t.chunk(packet('one','u','Merhaba',2)));
assert.ok(t.chunk(packet('one','j','Hello',3)));
assert.ok(t.chunk(packet('one','j','Hello world',4)));
assert.equal(panel.children.length,2);
assert.equal(panel.children[0].children[0].textContent,'› Merhaba');
assert.equal(panel.children[1].children[0].textContent,'Hello world');
assert.ok(!t.chunk(packet('old','j','STALE',5)));
assert.ok(!t.chunk(packet('one','j','DUPLICATE',4)));
assert.ok(!t.chunk(packet('one','j','x'.repeat(32001),5)));
t.interrupt('one');
assert.ok(t.chunk(packet('one','j','LATE words',5))); // Tüketilir, kesilen balona yazılmaz.
t.finish('one',{text:'Late final words',input_text:'Merhaba'},'interrupted');
assert.equal(panel.children.length,2);
assert.equal(panel.children[1].children[0].textContent,'Hello world');
assert.equal(panel.children[1].dataset.state,'interrupted');
assert.ok(!t.chunk(packet('one','j','After completion',6)));
t.begin('two',true);
assert.ok(t.chunk(packet('two','j','<img onerror="bad()">',1)));
t.finish('two',{text:'<img onerror="bad()">'},'complete');
assert.equal(panel.children.length,3);
assert.equal(panel.children.at(-1).children[0].textContent,'<img onerror="bad()">');
t.begin('three');t.finish('three',{text:'Final fallback',input_text:'Voice fallback'},'failed');
assert.equal(panel.children.length,5);assert.equal(panel.children.at(-1).dataset.state,'failed');
t.begin('four');t.chunk(packet('four','j','Unknown partial',1));t.finish('four',{},'unknown');
assert.equal(panel.children.at(-1).dataset.state,'unknown');
assert.ok(!t.finish('three',{text:'Wrong turn'}));
t.begin('late-input');t.chunk(packet('late-input','j','Model first',1));t.chunk(packet('late-input','u','Late user transcript',2));
assert.equal(panel.children.at(-2).children[0].textContent,'› Late user transcript');
assert.equal(panel.children.at(-1).children[0].textContent,'Model first');t.finish('late-input');
console.log('PASS incremental snapshots, one bubble, request/sequence guards, safe text, interrupted/unknown preservation');
