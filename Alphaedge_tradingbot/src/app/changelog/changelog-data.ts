// Product changelog shown to signed-in viewers at /changelog.
//
// Rules for adding entries:
//  - Publish DECISIONS, not commits. One entry per user-visible outcome —
//    if something was shipped and then reverted, say so as a single entry
//    describing what was learned, not two entries describing churn.
//  - Plain language. No internal jargon, table names or file paths.
//  - Ceiling language only: trading "pauses at +28%". Never phrase any
//    threshold as a promised, projected or expected return.
//  - Keep it coarse. A stale changelog is worse than none.

export type ChangeTag = 'New' | 'Improved' | 'Risk control' | 'Fixed' | 'Evaluated';

export interface ChangeEntry {
  date: string;   // ISO date, groups the entries
  tag: ChangeTag;
  title: string;
  body: string;
}

export const TAG_STYLE: Record<ChangeTag, string> = {
  'New': 'azure',
  'Improved': 'violet',
  'Risk control': 'gold',
  'Fixed': 'win',
  'Evaluated': 'dim',
};

export const CHANGELOG: ChangeEntry[] = [
  // ---------------------------------------------------------------- 25 Jul
  {
    date: '2026-07-25',
    tag: 'New',
    title: 'Daily profit ceiling of +28%',
    body: 'When a level gains 28% in a day it stops trading and holds the gain until the next reset, showing a TARGET HIT badge. This is a ceiling at which we stop — reaching it is never promised or guaranteed, and many days will not come close.',
  },
  {
    date: '2026-07-25',
    tag: 'New',
    title: 'GOLD lane replaces the Demo tile',
    body: 'The first tile is now GOLD: the uncapped lane, with no trade quota, no profit ceiling and no daily stop, running 24x7. Because it is uncapped it swings harder in both directions than Level 1-3, so treat it as a showcase of the raw engine rather than a preview of a subscription level.',
  },
  {
    date: '2026-07-25',
    tag: 'Risk control',
    title: 'Loss stop now reopens on a rolling 24 hours',
    body: 'A level that drops 15% pauses for exactly 24 hours instead of waiting for a fixed clock time, then resumes with its stop threshold recalculated from the new balance. That recalculation is what prevents repeated stops from compounding inside a single day.',
  },
  {
    date: '2026-07-25',
    tag: 'New',
    title: 'Strategy Analytics opened to everyone',
    body: 'The full performance page is now available to every signed-in user from the ANALYTICS button: hit rate, profit factor, expectancy, average win versus loss, maximum drawdown, win and loss streaks, and breakdowns by asset, by BUY/SELL and by level. Nothing is filtered — drawdowns and losing streaks sit next to the wins.',
  },
  {
    date: '2026-07-25',
    tag: 'Improved',
    title: 'Equity curve now readable point by point',
    body: 'Moving the pointer across the equity curve shows the exact cumulative position at that moment, plus the individual trade behind it — timestamp, asset, side, outcome and its own profit or loss.',
  },
  {
    date: '2026-07-25',
    tag: 'Improved',
    title: 'The trading day now rolls at 00:00 UTC',
    body: 'Previously 13:00 UTC. Trade quotas and the daily profit ceiling now reset together at midnight UTC, so every level starts each calendar day fresh.',
  },
  {
    date: '2026-07-25',
    tag: 'Fixed',
    title: 'Profit ceiling could release itself mid-day',
    body: 'A level that reached its daily ceiling could start trading again if positions already open then settled at a loss and pulled the day back under the threshold. Once a level reaches its ceiling it is now finished for the day, as intended.',
  },

  // ---------------------------------------------------------------- 24 Jul
  {
    date: '2026-07-24',
    tag: 'Risk control',
    title: 'Automatic daily loss stop on every level',
    body: 'If a level loses more than 15% of the balance it started the day with, it stops trading automatically and shows a countdown. It was added after a sharp market selloff, and it caps what any single bad run can cost without anyone needing to intervene.',
  },
  {
    date: '2026-07-24',
    tag: 'Risk control',
    title: 'Individual markets can now be paused',
    body: 'Gold, Bitcoin and Ethereum can each be halted independently while the others keep trading. A paused market shows a HALTED tag on its price card, and rounds it sits out are recorded with the reason, so nothing happens silently.',
  },
  {
    date: '2026-07-24',
    tag: 'Improved',
    title: 'Higher daily trade allowances',
    body: 'Level 1 moved to 50 trades a day, Level 2 to 100 and Level 3 to 250. More trades means more chances to compound — and with the profit ceiling in place, higher levels tend to reach their daily target sooner.',
  },
  {
    date: '2026-07-24',
    tag: 'Evaluated',
    title: 'Counter-trend entry filter — tested and rejected',
    body: 'After a losing run we tested a filter that would skip trades fighting the prevailing hourly move. On two days of data it looked like a clear improvement. Backtested properly across 30 days and roughly 23,000 trades covering both rising and falling markets, the trades it removed turned out to win at the same rate as everything else — adopting it would have cost about 20% of net profit. We did not ship it.',
  },

  // ---------------------------------------------------------------- 23 Jul
  {
    date: '2026-07-23',
    tag: 'Fixed',
    title: 'Service interruption resolved',
    body: 'The desk was unavailable for a period after our database hit a capacity limit. Service was restored on new infrastructure and the demo ledger restarted from a clean slate. The underlying cause — how much data each dashboard refresh was reading — has been addressed.',
  },
  {
    date: '2026-07-23',
    tag: 'Improved',
    title: 'Lighter, faster data layer',
    body: 'The dashboard now shares a single engine snapshot between viewers instead of every browser querying independently, and the ledger is indexed for the queries the desk actually runs. Same live data, a fraction of the load.',
  },

  // ---------------------------------------------------------------- 21 Jul
  {
    date: '2026-07-21',
    tag: 'Improved',
    title: 'BUY and SELL replace YES and NO',
    body: 'Positions now read BUY (settles above the strike) and SELL (settles at or below), matching standard trading terminology, and sells use the industry-standard red rather than a decorative colour. Existing history was relabelled too, so the whole ledger is consistent.',
  },
  {
    date: '2026-07-21',
    tag: 'New',
    title: 'Return on capital shown on every level',
    body: 'Each level tile now shows ROCE — realised profit or loss as a percentage of that level’s capital base — directly under the P&L figure, so the return on money actually deployed is visible at a glance.',
  },
  {
    date: '2026-07-21',
    tag: 'New',
    title: 'Self-service access requests',
    body: 'New users sign in with Google and complete a short form instead of waiting to be added manually. Requests reach the desk operator with the context needed to approve them quickly.',
  },
];
