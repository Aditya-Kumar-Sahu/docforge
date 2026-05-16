'use client';

import { useEffect } from 'react';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { createClient, AuthChangeEvent } from '@supabase/supabase-js';
import posthog from 'posthog-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder-url.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key';
const supabase = createClient(supabaseUrl, supabaseKey);

export default function LoginPage() {
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event: AuthChangeEvent, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        posthog.identify(session.user.id, {
          email: session.user.email,
        });
        posthog.capture('auth_login', {
          method: session.user.app_metadata.provider || 'email',
        });
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <div className="max-w-md mx-auto mt-20 p-8 bg-white border rounded shadow-lg">
      <h1 className="text-2xl font-bold mb-6 text-center">Login to DocForge</h1>
      <Auth
        supabaseClient={supabase}
        appearance={{ theme: ThemeSupa }}
        providers={['github']}
      />
    </div>
  );
}
