export default function (pi: any) {
	pi.on("project_trust", async () => ({ trusted: "yes" }));
}
