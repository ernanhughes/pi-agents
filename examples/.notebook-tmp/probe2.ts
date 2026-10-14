import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import reviewScope from "../ch15-first-extension/review-scope.ts";

const h = await makeSession({ extensions: [reviewScope] });
h.faux.appendResponses([
  (ctx: any, opts: any, state: any) => {
    console.error("opts keys:", Object.keys(opts ?? {}));
    const tools = opts?.tools ?? (ctx as any).tools;
    console.error("tools:", JSON.stringify(tools, null, 1)?.slice(0, 2000));
    return fauxAssistantMessage([fauxText("ok")]);
  },
]);
await h.session.prompt("go");
h.dispose();
