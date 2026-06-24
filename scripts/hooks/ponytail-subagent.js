#!/usr/bin/env node
// ponytail — Claude Code SubagentStart hook

const { getPonytailInstructions } = require('./ponytail-instructions');
const { readMode, writeHookOutput } = require('./ponytail-runtime');

const mode = readMode();

if (!mode || mode === 'off') {
  process.exit(0);
}

try {
  writeHookOutput('SubagentStart', mode, getPonytailInstructions(mode));
} catch (e) {}
