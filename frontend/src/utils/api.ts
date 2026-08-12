import { supabase } from '@/lib/supabase';

export async function authFetch(url: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession();
  let token = session?.access_token;

  if (!token && typeof window !== 'undefined') {
    token = localStorage.getItem('docforge_dev_token') || undefined;
  }

  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  return fetch(url, {
    ...options,
    headers,
  });
}
