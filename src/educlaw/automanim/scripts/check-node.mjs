#!/usr/bin/env node
/** pi-coding-agent / pi-tui require Node 20+ (RegExp /v flag). */
const [major] = process.versions.node.split(".").map(Number);
if (major < 20) {
  console.error(
    `AutoManim requires Node.js 20 or newer (found ${process.versions.node}).\n` +
      "The pi-coding-agent stack uses modern JavaScript that Node 18 cannot parse.\n\n" +
      "Upgrade, then re-run from src/educlaw/automanim/:\n" +
      "  nvm install 22 && nvm use 22\n" +
      "  # or: fnm use 22 / mise use node@22\n" +
      "  node -v\n" +
      "  npm run generate -- --episodes 1 --output ./dataset-test"
  );
  process.exit(1);
}
