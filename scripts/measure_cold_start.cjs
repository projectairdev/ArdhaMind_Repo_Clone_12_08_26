const http = require("http");
const WebSocket = require("ws");

async function runSingleColdStartTest(testIndex) {
  return new Promise((resolve, reject) => {
    const t0 = Date.now();
    let tHtml = null;
    let tJs = null;
    let tRest = null;
    let tWsInit = null;
    let tWsOpen = null;
    let tWsSnapshot = null;

    // Step 1: GET / (HTML)
    const reqHtml = http.get("http://localhost:3000/", (res) => {
      let body = "";
      res.on("data", chunk => body += chunk);
      res.on("end", () => {
        tHtml = Date.now() - t0;

        // Step 2: GET /assets/index-DnLDseMX.js (JS)
        const reqJs = http.get("http://localhost:3000/assets/index-DnLDseMX.js", (resJs) => {
          resJs.on("data", () => {});
          resJs.on("end", () => {
            tJs = Date.now() - t0;
          });
        });

        // Step 3 (Concurrent): GET /api/workspace (REST)
        const reqRest = http.get("http://localhost:3000/api/workspace", (resRest) => {
          let rBody = "";
          resRest.on("data", chunk => rBody += chunk);
          resRest.on("end", () => {
            tRest = Date.now() - t0;
          });
        });

        // Step 4 (Concurrent): WebSocket /api/ws
        tWsInit = Date.now() - t0;
        const ws = new WebSocket("ws://localhost:3000/api/ws");

        ws.on("open", () => {
          tWsOpen = Date.now() - t0;
        });

        ws.on("message", (data) => {
          try {
            const msg = JSON.parse(data.toString());
            if (msg.type === "state") {
              tWsSnapshot = Date.now() - t0;
              ws.close();
              resolve({
                testIndex,
                tHtml,
                tJs,
                tRest,
                tWsInit,
                tWsOpen,
                tWsSnapshot,
                usable: tWsSnapshot + 150 // React render overhead ~150ms
              });
            }
          } catch (e) {
            ws.close();
            reject(e);
          }
        });

        ws.on("error", (err) => {
          reject(err);
        });
      });
    });

    reqHtml.on("error", reject);
  });
}

async function main() {
  console.log("Starting 5 Cold-Start Performance Measurements...");
  const results = [];
  for (let i = 1; i <= 5; i++) {
    const res = await runSingleColdStartTest(i);
    results.push(res);
    console.log(`Run ${i}: HTML=${res.tHtml}ms, JS=${res.tJs}ms, REST=${res.tRest}ms, WS_Open=${res.tWsOpen}ms, First_State=${res.tWsSnapshot}ms, Usable=${res.usable}ms`);
    await new Promise(r => setTimeout(r, 500));
  }

  const usables = results.map(r => r.usable).sort((a, b) => a - b);
  const snapshots = results.map(r => r.tWsSnapshot).sort((a, b) => a - b);

  const p50 = usables[2]; // 3rd of 5
  const p95 = usables[4]; // max of 5
  const worst = usables[4];

  console.log("\n--- SUMMARY ---");
  console.log(`p50 Usable Latency: ${p50}ms`);
  console.log(`p95 Usable Latency: ${p95}ms`);
  console.log(`Worst Case: ${worst}ms`);
  console.log(`First Canonical State p95: ${snapshots[4]}ms`);
}

main().catch(console.error);
