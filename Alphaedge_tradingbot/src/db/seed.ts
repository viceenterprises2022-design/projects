import { db } from './index';
import { users, botTemplates } from './schema';

async function main() {
  console.log('Seeding database...');

  const defaultUser = {
    id: 'user_1',
    email: 'trader@alphaedge.io',
    kycStatus: 'verified',
    createdAt: Date.now(),
  };

  try {
    await db.insert(users).values(defaultUser).onConflictDoNothing();
    console.log('User seeded.');

    const templates = [
      {
        id: 'tmpl_1',
        code: 'HL-BREAKOUT-BTC',
        assetClass: 'BTC',
        status: 'live',
        minWinRate: 0.58,
        minExpectancy: 0.25,
      },
      {
        id: 'tmpl_2',
        code: 'HL-BREAKOUT-ETH',
        assetClass: 'ETH',
        status: 'live',
        minWinRate: 0.55,
        minExpectancy: 0.22,
      },
      {
        id: 'tmpl_3',
        code: 'GM-CORE-001',
        assetClass: 'XAUUSD',
        status: 'in_assay',
        minWinRate: 0.62,
        minExpectancy: 0.35,
      },
    ];

    for (const t of templates) {
      await db.insert(botTemplates).values(t).onConflictDoNothing();
    }
    console.log('Bot templates seeded.');
    console.log('Seeding finished.');
  } catch (error) {
    console.error('Error seeding database:', error);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
