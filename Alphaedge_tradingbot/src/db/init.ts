import { db } from './index';
import { users, botTemplates } from './schema';
import { migrate } from 'drizzle-orm/libsql/migrator';
import path from 'path';

let isInitialized = false;

export async function initDb() {
  if (isInitialized) return;

  try {
    let exists = false;
    try {
      // Try querying the users table. If it succeeds, the schema is already created.
      await db.select().from(users).limit(1);
      exists = true;
      console.log('Database tables already exist. Skipping migrations.');
    } catch (err) {
      console.log('Database tables do not exist. Running database migrations...');
    }

    if (!exists) {
      const migrationsFolder = path.join(process.cwd(), 'drizzle');
      await migrate(db, { migrationsFolder });
      console.log('Database migrated successfully.');
    }

    // Auto-seed default user if not exists
    const userList = await db.select().from(users);
    if (userList.length === 0) {
      console.log('Seeding default user and templates...');
      await db.insert(users).values({
        id: 'user_1',
        email: 'trader@alphaedge.io',
        kycStatus: 'verified',
        createdAt: Date.now(),
      });

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
      console.log('Seeding finished.');
    }

    isInitialized = true;
  } catch (error) {
    console.error('Database initialization/seeding failed:', error);
    throw error;
  }
}
