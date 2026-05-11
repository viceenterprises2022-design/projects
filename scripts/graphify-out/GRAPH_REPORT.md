# Graph Report - /home/vreddy1/Desktop/Projects/scripts  (2026-05-09)

## Corpus Check
- 335 files · ~2,014,516 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4231 nodes · 11285 edges · 70 communities detected
- Extraction: 71% EXTRACTED · 29% INFERRED · 0% AMBIGUOUS · INFERRED: 3305 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]

## God Nodes (most connected - your core abstractions)
1. `Dashboard` - 220 edges
2. `test_dashboard()` - 105 edges
3. `StateStore` - 102 edges
4. `parse()` - 97 edges
5. `main()` - 92 edges
6. `run()` - 87 edges
7. `spawnSync()` - 76 edges
8. `test()` - 57 edges
9. `build_config()` - 53 edges
10. `output()` - 42 edges

## Surprising Connections (you probably didn't know these)
- `api_symbols()` --calls--> `list()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/scripts/api_server.py → /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/ecc2/src/worktree/mod.rs
- `gui()` --calls--> `main()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/src/llm/__init__.py → /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/ecc2/src/main.rs
- `runExternalCommand()` --calls--> `spawnSync()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/scripts/auto-update.js → /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/tests/lib/tmux-worktree-orchestrator.test.js
- `cloneJsonValue()` --calls--> `parse()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/scripts/lib/install-state.js → /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/ecc2/src/comms/mod.rs
- `resetAliases()` --calls--> `getAliasesPath()`  [INFERRED]
  /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/tests/lib/session-aliases.test.js → /home/vreddy1/Desktop/Projects/scripts/everything-claude-code/scripts/lib/session-aliases.js

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (357): runTests(), test(), run(), test(), extractTopLevelList(), run(), test(), runScript() (+349 more)

### Community 1 - "Community 1"
Cohesion: 0.01
Nodes (325): run(), active_session_count_only_counts_live_queue_states(), AggregateUsage, approval_queue_line(), approval_queue_preview_line(), approval_queue_preview_line_uses_target_session_and_preview(), approval_request_webhook_body(), attention_queue_keeps_conflicted_worktree_pressure_when_stabilized() (+317 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (355): coordinate_backlog_cycle(), maybe_auto_rebalance_noops_when_disabled(), maybe_auto_rebalance_reports_total_rerouted_work(), maybe_auto_rebalance_with(), aggregate_cost_summary_mentions_fifty_percent_alert(), aggregate_cost_summary_mentions_ninety_percent_alert(), aggregate_cost_summary_mentions_total_cost(), aggregate_cost_summary_uses_custom_threshold_labels() (+347 more)

### Community 3 - "Community 3"
Cohesion: 0.01
Nodes (236): build_legacy_env_connector(), build_legacy_migration_audit_report(), build_legacy_migration_next_steps(), build_legacy_migration_plan_report(), build_legacy_plugin_draft(), build_legacy_remote_add_command(), build_legacy_remote_dispatch_draft(), build_legacy_schedule_add_command() (+228 more)

### Community 4 - "Community 4"
Cohesion: 0.01
Nodes (304): get_conn(), init_db(), insert_macro(), insert_metric(), query_history(), query_latest(), Insert one macro snapshot row into macro_history., Return the most recent row per symbol + latest macro row. (+296 more)

### Community 5 - "Community 5"
Cohesion: 0.01
Nodes (233): buildAgentCatalog(), compressToCatalog(), compressToSummary(), extractSummary(), lazyLoadAgent(), loadAgent(), loadAgents(), parseFrontmatter() (+225 more)

### Community 6 - "Community 6"
Cohesion: 0.02
Nodes (178): hydrateSessionFromPath(), isSessionFileTarget(), parseClaudeTarget(), resolveSessionRecord(), main(), runTests(), test(), writeFile() (+170 more)

### Community 7 - "Community 7"
Cohesion: 0.02
Nodes (146): createProposalId(), proposeSkillAmendment(), summarizePatchPreview(), buildInstallApplyArgs(), deriveRepoRootFromState(), determineInstallCwd(), main(), parseArgs() (+138 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (56): ABC, adapt_messages_for_provider(), get_provider_builder(), PromptBuilder, PromptConfig, Prompt builder for normalizing prompts across providers., ClaudeProvider, Claude provider adapter. (+48 more)

### Community 9 - "Community 9"
Cohesion: 0.03
Nodes (92): makeRecord(), runTests(), test(), runTests(), test(), writeState(), main(), resolveCommand() (+84 more)

### Community 10 - "Community 10"
Cohesion: 0.03
Nodes (56): fmt(), fmtIN(), loadHistory(), loadLatest(), renderChartCard(), renderMacro(), renderSignalCard(), renderTicker() (+48 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (77): classify_events(), _parse_classification(), Classify tool calls against compliance steps using LLM., Classify which tool calls match which compliance steps.      Returns {step_id: [, Parse LLM classification output into {step_id: [event_indices]}., _check_temporal_order(), ComplianceResult, grade() (+69 more)

### Community 12 - "Community 12"
Cohesion: 0.03
Nodes (46): agent_profile_resolution_rejects_inheritance_cycles(), agent_profiles_resolve_inheritance_and_defaults(), AgentProfileConfig, BudgetAlertThresholds, ComputerUseDispatchConfig, Config, ConflictResolutionConfig, ConflictResolutionStrategy (+38 more)

### Community 13 - "Community 13"
Cohesion: 0.04
Nodes (58): askClaude(), branchSession(), buildPrompt(), compactSession(), estimateTokenCount(), exportSession(), getClawDir(), getSessionMetrics() (+50 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (39): agent_program(), config_detection_adds_custom_markers_to_detected_summary(), config_detection_preserves_custom_primary_label_and_appends_marker_matches(), ContextGraphCompactionStats, ContextGraphEntity, ContextGraphEntityDetail, ContextGraphObservation, ContextGraphRecallEntry (+31 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (55): bucketByDay(), formatPercent(), getTrendArrow(), groupRecordsBySkill(), horizontalBar(), panelBox(), renderAmendmentPanel(), renderDashboard() (+47 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (41): check_sessions(), coordinate_backlog_cycle_rebalances_first_after_unrecovered_deferred_pressure(), coordinate_backlog_cycle_records_recovery_dispatch_when_it_routes_work(), coordinate_backlog_cycle_records_recovery_when_rebalance_first_dispatch_routes_work(), coordinate_backlog_cycle_retries_after_rebalance_when_dispatch_deferred(), coordinate_backlog_cycle_skips_dispatch_during_chronic_cooloff_when_rebalance_does_not_help(), coordinate_backlog_cycle_skips_dispatch_when_persistent_saturation_streak_hits_cooloff(), coordinate_backlog_cycle_skips_rebalance_when_stabilized_and_dispatch_is_healthy() (+33 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (23): CompletionSummaryConfig, CompletionSummaryDelivery, DesktopNotificationConfig, DesktopNotifier, discord_webhook_payload_disables_mentions(), linux_notifications_use_notify_send(), macos_notifications_use_osascript(), notification_command() (+15 more)

### Community 18 - "Community 18"
Cohesion: 0.09
Nodes (38): build_batch_prompt(), build_html_table(), build_snippet(), calc_pivot_points(), calc_rsi(), call_claude_batch(), _chg_style(), determine_trend() (+30 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (36): analyzeTranscript(), atomicWriteJson(), buildRecommendation(), buildStatus(), extractToolResultIds(), extractToolUses(), findTranscriptPaths(), formatSignals() (+28 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (25): buildAggregates(), deriveClaudeWorkerId(), deriveDmuxSessionState(), deriveWorkerHealth(), ensureInteger(), ensureOptionalString(), ensureString(), getFallbackSessionRecordingPath() (+17 more)

### Community 21 - "Community 21"
Cohesion: 0.18
Nodes (24): extract_content(), format_feedback(), get_anomaly_attr(), main(), Append an audit event to the JSONL audit log.      Creates a new dict to avoid m, Get a field from an anomaly that may be a dict or an object.      The SDK's ``se, Format detected anomalies as feedback for Claude Code.      Returns:         A h, Entry point for the Claude Code PreToolUse hook. (+16 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (15): planOperations(), supportsAntigravitySourcePath(), getClaudeManagedDestinationPath(), createJsonMergeOperation(), readJsonObject(), buildValidationIssue(), createFlatFileOperations(), createFlatRuleOperations() (+7 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (17): buildCatalog(), createDocumentSpecs(), createDocumentSpecsForRoot(), evaluateExpectations(), formatExpectation(), listMatchingFiles(), readFileOrThrow(), renderMarkdown() (+9 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (18): assess_blast_radius(), assess_file_sensitivity(), assess_irreversibility(), base_tool_risk(), blocks_combined_high_risk_operations(), computes_blast_radius_risk(), computes_irreversible_risk(), computes_sensitive_file_risk() (+10 more)

### Community 25 - "Community 25"
Cohesion: 0.15
Nodes (7): OutputTimeFilter, OutputEvent, OutputLine, OutputStream, pushing_output_broadcasts_events(), ring_buffer_keeps_most_recent_lines(), SessionOutputStore

### Community 26 - "Community 26"
Cohesion: 0.23
Nodes (9): runCatalogValidator(), runSourceViaTempFile(), runTests(), runValidatorWithDir(), runValidatorWithDirs(), stripShebang(), test(), writeInstallComponentsManifest() (+1 more)

### Community 27 - "Community 27"
Cohesion: 0.23
Nodes (9): runTests(), test(), writeCatalogFixture(), writeCountedFiles(), writeEnglishAgents(), writeEnglishReadme(), writeZhAgents(), writeZhDocsReadme() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.32
Nodes (4): ConvertTo-HashtableRecursive(), Read-SettingsAsHashtable(), ConvertTo-HashtableRecursive(), Read-SettingsAsHashtable()

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (4): message_type_name(), MessageType, send(), TaskPriority

### Community 30 - "Community 30"
Cohesion: 0.5
Nodes (2): NetworkGraphExplainer, Scene

### Community 31 - "Community 31"
Cohesion: 0.67
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (2): toCursorAgentFileName(), toCursorAgentRelativePath()

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): comms::TaskPriority

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (0): 

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (0): 

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **307 isolated node(s):** `Fetch option chain and return only derived metrics (no raw strikes stored).`, `Return sorted list of expiry date strings.`, `Fetch full option chain for a given expiry.`, `Fetch option chain, filter to spot ±1000, compute:     - OI bars (call_oi, put_o`, `Factors:      1. Trend      (EMA 20/50/200)           weight ±2      2. Dow Jone` (+302 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 33`** (2 nodes): `validate-no-personal-paths.js`, `collectFiles()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `insaits-security-wrapper.js`, `isEnabled()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (2 nodes): `shell-split.js`, `splitShellSegments()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (2 nodes): `resolve-ecc-root.js`, `resolveEccRoot()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (2 nodes): `planOperations()`, `codebuddy-project.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `comms::TaskPriority`, `.from()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `patch_market_no_claude.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `patch_market_trending.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `patch_market.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `install.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `eslint.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `commitlint.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `__main__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `text-animations-word-highlight.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `charts-bar-chart.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `build-opencode.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `check-hook-enabled.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `pre-write-doc-warn.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `pre-bash-dispatcher.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `post-bash-dispatcher.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `check-console-log.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `post-edit-typecheck.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `post-edit-console-warn.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `utils.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `package-manager.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `session-aliases.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `session-manager.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `index.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `gemini-project.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `codex-home.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `opencode-home.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `conftest.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `mod.rs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 2` to `Community 1`, `Community 3`, `Community 5`, `Community 7`, `Community 8`, `Community 10`, `Community 12`, `Community 14`, `Community 21`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `parse()` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 6`, `Community 7`, `Community 9`, `Community 13`, `Community 15`, `Community 18`, `Community 19`, `Community 20`, `Community 22`, `Community 29`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `spawnSync()` connect `Community 0` to `Community 5`, `Community 6`, `Community 7`, `Community 9`, `Community 13`, `Community 15`, `Community 18`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `test_dashboard()` (e.g. with `.default()` and `.with_config_detection()`) actually correct?**
  _`test_dashboard()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 94 inferred relationships involving `parse()` (e.g. with `readJson()` and `readJson()`) actually correct?**
  _`parse()` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `main()` (e.g. with `gui()` and `run_main()`) actually correct?**
  _`main()` has 61 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Fetch option chain and return only derived metrics (no raw strikes stored).`, `Return sorted list of expiry date strings.`, `Fetch full option chain for a given expiry.` to the rest of the system?**
  _307 weakly-connected nodes found - possible documentation gaps or missing edges._