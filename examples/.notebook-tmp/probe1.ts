import { fauxAssistantMessage, fauxText, getSystemMessageText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import reviewScope from "../ch15-first-extension/review-scope.ts";

const h = await makeSession({ extensions: [reviewScope] });
h.faux.appendResponses([
  (ctx: any) => {
    const sys = ctx.messages.filter((m: any) => m.role === "system");
    console.error("SYSTEM MESSAGES:", sys.length);
    for (const s of sys) {
      const t = getSystemMessageText(s);
      console.error("---- text ----");
      console.error(t.slice(0, 4000));
      console.error("---- has review_scope:", t.includes("review_scope"));
    }
    return fauxAssistantMessage([fauxText("ok")]);
  },
]);
await h.session.prompt("go");
console.log(JSON.stringify({ active: h.session.getActiveToolNames().includes("review_scope") }));
h.dispose();
