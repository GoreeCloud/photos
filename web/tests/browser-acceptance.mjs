#!/usr/bin/env node
// Opt-in real browser acceptance for the development photos login screen.
// Requires explicitly inspected local Playwright Core and engine binaries.
// No auto-install, authentication, test credentials or non-loopback requests.
import assert from "node:assert/strict";
import {existsSync, statSync} from "node:fs";
import {isAbsolute, join} from "node:path";
import {pathToFileURL} from "node:url";

const variables=["GC_PLAYWRIGHT_CORE_MODULE","GC_CHROMIUM_BIN","GC_FIREFOX_BIN","GC_WEBKIT_BIN"];
for(const name of variables){
  const value=process.env[name];
  if(!value||!isAbsolute(value)||!existsSync(value)||!statSync(value).isFile()){
    throw Error(name+" must be an inspected, existing absolute file. No software is downloaded.");
  }
}
const shots=process.env.GC_QA_SCREENSHOTS_DIR;
if(shots&&(!isAbsolute(shots)||!existsSync(shots)||!statSync(shots).isDirectory())){
  throw Error("GC_QA_SCREENSHOTS_DIR must already exist as an absolute directory.");
}
const core=await import(pathToFileURL(process.env.GC_PLAYWRIGHT_CORE_MODULE).href);
const base="http://127.0.0.1:18751/";
const cases=[["desktop-light",900,800,false],["mobile-dark",390,844,true],["compact-light",320,760,false]];
const engines=[["chromium","GC_CHROMIUM_BIN"],["firefox","GC_FIREFOX_BIN"],["webkit","GC_WEBKIT_BIN"]];
function luminance(c){
  return c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4})
    .reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
}
for(const [name,variable]of engines){
  const browser=await core[name].launch({executablePath:process.env[variable],headless:true,timeout:20000});
  try{
    for(const [scenario,width,height,dark]of cases){
      const context=await browser.newContext({viewport:{width,height},
        colorScheme:dark?"dark":"light",reducedMotion:"reduce",serviceWorkers:"block"});
      try{
        const page=await context.newPage();
        const errors=[],blocked=[];
        page.on("pageerror",e=>errors.push(String(e).slice(0,180)));
        await page.route("**/*",route=>{
          const uri=route.request().url();
          const sameOrigin=uri.startsWith(base);
          const isNonApiGet=route.request().method()==="GET"&&
            !/^\/(?:api|v1)\//.test(new URL(uri).pathname);
          if(sameOrigin&&isNonApiGet)return route.continue();
          blocked.push(uri.split("?")[0]);
          return route.abort("blockedbyclient");
        });
        const response=await page.goto(base,{waitUntil:"networkidle",timeout:15000});
        assert.equal(response?.status(),200,"Source app did not load");
        await page.getByRole("heading",{name:"GoreeCloud Photos"}).waitFor();
        const input=page.getByLabel("Library password");
        const action=page.getByRole("button",{name:"Unlock library"});
        await input.focus();
        assert.equal(await input.evaluate(el=>el===document.activeElement),true);
        await page.keyboard.press("Tab");
        assert.equal(await action.evaluate(el=>el===document.activeElement),true,
          "Next tab does not reach the primary action");
        const ui=await page.evaluate(()=>{
          const root=document.documentElement,btn=document.querySelector("button.primary");
          const card=document.querySelector(".login-card").getBoundingClientRect();
          const cs=getComputedStyle(btn);
          const rgb=s=>[...s.matchAll(/\d+(?:\.\d+)?/g)].slice(0,3).map(v=>Number(v[0]));
          return {client:root.clientWidth,scroll:root.scrollWidth,
            appearance:getComputedStyle(root).colorScheme,
            accent:root.dataset.gcAccent||"iris",
            foreground:rgb(cs.color),background:rgb(cs.backgroundColor),
            cardLeft:card.left,cardRight:card.right};
        });
        assert.ok(ui.scroll<=ui.client+1,
          "Horizontal overflow: "+JSON.stringify(ui));
        assert.ok(ui.cardLeft>=-1&&ui.cardRight<=ui.client+1,
          "Form card clipped: "+JSON.stringify(ui));
        assert.equal(ui.accent,"iris");
        assert.ok(ui.appearance.includes(dark?"dark":"light"),
          "OS appearance not reflected: "+JSON.stringify(ui));
        const fg=luminance(ui.foreground),bg=luminance(ui.background);
        const ratio=(Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05);
        assert.ok(ratio>=4.5,
          "Primary action contrast below 4.5:1: "+JSON.stringify(ui));
        assert.deepEqual(blocked,[],"External requests forbidden");
        assert.deepEqual(errors,[],"Uncaught browser error");
        if(shots){
          await page.screenshot({path:join(shots,"photos-"+name+"-"+scenario+".png")});
        }
        console.log("photos",name,browser.version(),scenario,
          "PASS; primary contrast "+ratio.toFixed(2)+":1; no overflow, errors, network or real credentials");
      }finally{await context.close()}
    }
  }finally{await browser.close()}
}
