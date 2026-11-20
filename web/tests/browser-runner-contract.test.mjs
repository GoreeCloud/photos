import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";
const runner=new URL("./browser-acceptance.mjs",import.meta.url);
test("opt-in real-browser acceptance refuses missing inspected binaries",()=>{
  const r=spawnSync(process.execPath,[fileURLToPath(runner)],{
    encoding:"utf8",timeout:5000,
    env:{...process.env,GC_PLAYWRIGHT_CORE_MODULE:"",GC_CHROMIUM_BIN:"",
      GC_FIREFOX_BIN:"",GC_WEBKIT_BIN:""}});
  assert.notEqual(r.status,0);
  assert.match(r.stderr,/must be an inspected, existing absolute file/);
});
test("browser acceptance is local-only and cannot install or submit login",()=>{
  const source=readFileSync(runner,"utf8");
  assert.match(source,/127\.0\.0\.1:/);
  assert.match(source,/return route\.abort\("blockedbyclient"\)/);
  assert.match(source,/serviceWorkers:"block"/);
  assert.match(source,/getByRole\("heading"/);
  assert.doesNotMatch(source,/\.fill\(|\.click\(|requestSubmit\(|npm\s+install|playwright\s+install/);
});
