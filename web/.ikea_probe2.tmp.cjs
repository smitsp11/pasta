const {chromium, devices}=require('@playwright/test');
const OUT='/Users/smit/conductor/workspaces/pasta/houston/.context/research/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function dismiss(p){ for(const t of ['Ok','Accept all']){ const b=p.locator('#onetrust-banner-sdk button',{hasText:t}).first(); if(await b.count()){ try{await b.click({timeout:3000}); await sleep(800);}catch(e){} } } }
async function flow(b, cc, invalidCode, validCode, dev){
  const ctx=await b.newContext(dev?{...dev}:{viewport:{width:1366,height:900}});
  const p=await ctx.newPage(); const r={cc, dev:!!dev};
  const base=`https://www.ikea.com/${cc}/en/`;
  // category
  await p.goto(base+'cat/beds-mattresses-bm001/',{timeout:45000,waitUntil:'domcontentloaded'}); await sleep(3000); await dismiss(p);
  r.cat={url:p.url(), title:await p.title()};
  // first product link
  const prod=await p.evaluate(()=>{const a=[...document.querySelectorAll('a[href*="/p/"]')].find(a=>a.getAttribute('href')&&/\/p\/[a-z0-9-]+\/?$/.test(a.getAttribute('href'))); return a?{href:a.href,text:(a.innerText||'').replace(/\s+/g,' ').slice(0,80)}:null});
  r.firstProduct=prod;
  await p.goto(prod.href,{timeout:45000,waitUntil:'domcontentloaded'}); await sleep(3500); await dismiss(p);
  r.product={url:p.url(), title:await p.title()};
  r.productButtons=await p.evaluate(()=>[...document.querySelectorAll('button')].map(b=>(b.innerText||b.getAttribute('aria-label')||'').trim().replace(/\s+/g,' ')).filter(t=>/cart|bag|postal|zip|postcode|store|delivery|availab|check/i.test(t)).slice(0,20));
  r.productAvailText=await p.evaluate(()=>{const e=[...document.querySelectorAll('div,section')].find(e=>/availability|delivery/i.test(e.className)); return e?(e.innerText||'').replace(/\s+/g,' ').slice(0,500):null});
  // add to cart
  const add=p.locator('button',{hasText:/add to (cart|bag)/i}).first();
  if(await add.count()){ await add.click({timeout:5000}); await sleep(3000); r.addedClicked=true; r.afterAddText=await p.evaluate(()=>(document.querySelector('[role="dialog"],[class*="toast"],[class*="modal"]')?.innerText||'').replace(/\s+/g,' ').slice(0,300)); }
  await p.screenshot({path:OUT+`ikea-${cc}-product${dev?'-mobile':''}.png`});
  // cart
  await p.goto(base+'shoppingcart/',{timeout:45000,waitUntil:'domcontentloaded'}); await sleep(4000); await dismiss(p);
  r.cart={url:p.url(), title:await p.title(), text:await p.evaluate(()=>(document.querySelector('main')?.innerText||document.body.innerText).replace(/\s+/g,' ').slice(0,900))};
  r.cartButtons=await p.evaluate(()=>[...document.querySelectorAll('button,a')].map(b=>(b.innerText||b.getAttribute('aria-label')||'').trim().replace(/\s+/g,' ')).filter(t=>/checkout|postal|zip|postcode|delivery|continue/i.test(t)).slice(0,15));
  await p.screenshot({path:OUT+`ikea-${cc}-cart${dev?'-mobile':''}.png`});
  // postal gate: try button in cart or header
  let gate=p.locator('button',{hasText:/postal code|postcode|zip/i}).first();
  if(!(await gate.count())) gate=p.locator('button',{hasText:/delivery|check/i}).first();
  if(await gate.count()){ await gate.click({timeout:5000}); await sleep(2000);
    r.gateDialog=await p.evaluate(()=>{const d=document.querySelector('[role="dialog"], .modal, [class*="modal"]'); if(!d) return null; const inp=d.querySelector('input'); return {text:(d.innerText||'').replace(/\s+/g,' ').slice(0,500), input:inp?{label:inp.getAttribute('aria-label'),placeholder:inp.placeholder,id:inp.id,labelText:(inp.labels&&inp.labels[0]?.innerText)||null}:null, buttons:[...d.querySelectorAll('button')].map(b=>(b.innerText||b.getAttribute('aria-label')||'').trim()).filter(Boolean)}});
    const inp=p.locator('[role="dialog"] input, [class*="modal"] input').first();
    if(await inp.count()){
      await inp.fill(invalidCode); await sleep(300); await inp.press('Enter'); await sleep(3500);
      r.invalidResult=await p.evaluate(()=>{const d=document.querySelector('[role="dialog"], [class*="modal"]')||document.body; return {text:(d.innerText||'').replace(/\s+/g,' ').slice(0,600), errors:[...document.querySelectorAll('[role="alert"],[class*="error"],[aria-invalid="true"],[class*="helper"]')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean).slice(0,6)}});
      await p.screenshot({path:OUT+`ikea-${cc}-postal-invalid${dev?'-mobile':''}.png`});
      await inp.fill(validCode); await sleep(300); await inp.press('Enter'); await sleep(4000);
      r.validResult=await p.evaluate(()=>({header:(document.querySelector('header')?.innerText||'').replace(/\s+/g,' ').slice(0,200), main:(document.querySelector('main')?.innerText||'').replace(/\s+/g,' ').slice(0,700)}));
    }
  }
  // checkout
  const co=p.locator('button,a',{hasText:/continue to checkout|checkout/i}).first();
  if(await co.count()){ try{await co.click({timeout:5000}); await sleep(5000); r.checkout={url:p.url(), title:await p.title(), text:await p.evaluate(()=>(document.body.innerText||'').replace(/\s+/g,' ').slice(0,900)), inputs:await p.evaluate(()=>[...document.querySelectorAll('input')].map(i=>({label:i.getAttribute('aria-label')||i.labels?.[0]?.innerText||null,ph:i.placeholder,name:i.name})).slice(0,12))}; await p.screenshot({path:OUT+`ikea-${cc}-checkout${dev?'-mobile':''}.png`});}catch(e){r.checkoutErr=e.message.slice(0,200)} }
  console.log(JSON.stringify(r,null,1)); await ctx.close();
}
(async()=>{ const b=await chromium.launch();
  for(const [cc,inv,val,dev] of [['ca','Z9Z 9Z9','M5V 3L9',null],['gb','ZZ99 9ZZ','SW1A 1AA',null],['ca','Z9Z 9Z9','M5V 3L9',devices['iPhone 13']]]){ try{await flow(b,cc,inv,val,dev)}catch(e){console.log('ERR',cc,!!dev,e.message.slice(0,300))} }
  await b.close(); })();
