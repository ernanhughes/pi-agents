import { Box, Text } from "@earendil-works/pi-tui";

pi.registerEntryRenderer<GuardBlock>("guard.block", (entry, { expanded }, theme) => {
  const box = new Box(1, 1, (text) => theme.bg("customMessageBg", text));
  box.addChild(new Text(`${theme.fg("accent", "[guard]")} ${entry.data?.reason ?? "blocked"}`, 0, 0));
  if (expanded) {
    box.addChild(new Text(theme.fg("dim", new Date(entry.data?.at ?? Date.now()).toLocaleString()), 0, 0));
  }
  return box;
});
