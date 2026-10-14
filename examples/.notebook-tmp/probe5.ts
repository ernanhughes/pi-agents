import { fauxAssistantMessage, fauxText } from "@earendil-works/pi-ai";
import { makeSession } from "../harness/session.ts";
import reviewScope from "../ch15-first-extension/review-scope.ts";

const h = await makeSession({ extensions: [reviewScope] });
h.faux.appendResponses([
  (ctx: any) => {
    const sys: any = ctx.messages.find((m: any) => m.role === "system");
    const t = (sys.toolsAdded ?? []).find((x: any) => x.name === "review_scope");
    console.error("declared:", JSON.stringify(t, null, 1));
    return fauxAssistantMessage([fauxText("ok")]);
  },
]);
await h.session.prompt("go");
h.dispose();
