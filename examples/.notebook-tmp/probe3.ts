import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import reviewScope from "../ch15-first-extension/review-scope.ts";

const h = await makeSession({ extensions: [reviewScope] });
h.faux.appendResponses([
  (ctx: any) => {
    const sys: any = ctx.messages.find((m: any) => m.role === "system");
    console.error("system keys:", Object.keys(sys));
    console.error(JSON.stringify(sys.tools ?? null, null, 1)?.slice(0, 3000));
    return fauxAssistantMessage([fauxText("ok")]);
  },
]);
await h.session.prompt("go");
console.error("active:", JSON.stringify(h.session.getActiveToolNames()));
h.dispose();
