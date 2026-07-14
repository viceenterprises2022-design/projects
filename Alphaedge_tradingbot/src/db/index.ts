import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';
import * as schema from './schema';

const getDatabaseUrl = () => {
  if (process.env.DATABASE_URL) {
    return process.env.DATABASE_URL;
  }
  // If running in Vercel, use the /tmp directory which allows write access.
  if (process.env.VERCEL) {
    return 'file:/tmp/sqlite.db';
  }
  return 'file:sqlite.db';
};

const client = createClient({
  url: getDatabaseUrl(),
});

export const db = drizzle(client, { schema });
