import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {readFileSync} from "node:fs";
const base=new URL("../src/",import.meta.url);
const get=p=>readFileSync(new URL(p,base),"utf8");
const meta=JSON.parse(get("gc-ui-provenance.json"));
test("Photos GC UI token snapshot is immutable and source attributed",()=>{
  assert.equal(meta.upstream,"https://github.com/GoreeCloud/gc-ui");
  assert.equal(meta.originalSourceCommit,"79949b3db58f2214e8d4c4eb2b647f75e1cfc724");
  assert.equal(meta.latestByteComparison,"be8b819748d1ef0f6b2d3e786f4b22864cb3d07d");
  const paths={"gc-ui-tokens.css":new URL("../src/gc-ui-tokens.css",import.meta.url),
    LICENSE:new URL("../../LICENSE",import.meta.url)};
  assert.deepEqual(Object.keys(meta.sha256).sort(),Object.keys(paths).sort());
  for(const [name,p]of Object.entries(paths)){
    assert.equal(createHash("sha256").update(readFileSync(p)).digest("hex"),meta.sha256[name]);
  }
  assert.match(readFileSync(paths.LICENSE,"utf8"),/MIT License/);
});
test("Photos owns its gallery CSS while GC UI controls semantic tokens",()=>{
  const entry=get("main.tsx"),css=get("styles.css"),tokens=get("gc-ui-tokens.css");
  assert.ok(entry.indexOf('import "./gc-ui-tokens.css";')>=0);
  assert.ok(entry.indexOf('import "./styles.css";')>entry.indexOf('import "./gc-ui-tokens.css";'));
  for(const name of [".photo-grid", ".photo-card", ".thumbnail", ".album-commands", ".security-settings"])
    assert.ok(css.includes(name),"missing Photos-specific surface: "+name);
  for(const role of ["--gc-canvas","--gc-text","--gc-brand","--gc-on-brand","--gc-focus-ring"])
    assert.ok(css.includes("var("+role+")"),"missing shared semantic role: "+role);
  assert.doesNotMatch(tokens,/@import\s+(?:url\()?\s*["']?https?:\/\//i);
});

test("Photos login form honors compact mobile min-content boundaries",()=>{
  const css=get("styles.css");
  assert.match(css,/\.login-card \{ min-width:0;/);
  assert.match(css,/\.login-card form \{ display:grid; grid-template-columns:minmax\(0,1fr\)/);
  assert.match(css,/\.login-card input \{ width:100%; min-width:0;/);
});
