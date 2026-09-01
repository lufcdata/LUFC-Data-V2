import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;

export const supabaseConfigError = !url || !key
  ? 'Missing Supabase environment variables in the Render build.'
  : null;

export const supabase = url && key ? createClient(url, key) : null;
