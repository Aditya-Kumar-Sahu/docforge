'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { AuthChangeEvent } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import posthog from 'posthog-js';

const DEV_JWT_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiYXVkIjoiYXV0aGVudGljYXRlZCJ9.BsrZrfrMoEH3a-SEYp98swlcnIAZ3-6ZMntYBP9O1iw';

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isLoggedOut = params.get('logout') === 'true';

    if (!isLoggedOut) {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session) {
          router.push('/repos');
        } else if (typeof window !== 'undefined' && localStorage.getItem('docforge_dev_token')) {
          router.push('/repos');
        }
      });
    }

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event: AuthChangeEvent, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        posthog.identify(session.user.id, {
          email: session.user.email,
        });
        posthog.capture('auth_login', {
          method: session.user.app_metadata.provider || 'email',
        });
        router.push('/repos');
      }
    });

    return () => subscription.unsubscribe();
  }, [router]);

  const handleDevLogin = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('docforge_dev_token', DEV_JWT_TOKEN);
      router.push('/repos');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 p-8 bg-white border border-gray-200 rounded-xl shadow-lg space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900">Login to DocForge</h1>
        <p className="text-sm text-gray-500 mt-1">Sign in with Supabase or use Quick Dev Login</p>
      </div>

      {/* Quick Dev Login Button */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center space-y-2">
        <p className="text-xs text-blue-800 font-medium">⚡ Local Development / Instant Demo</p>
        <button
          onClick={handleDevLogin}
          type="button"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md transition text-sm shadow-sm"
        >
          Quick Dev Login →
        </button>
      </div>

      <div className="relative flex py-1 items-center">
        <div className="flex-grow border-t border-gray-200"></div>
        <span className="flex-shrink mx-3 text-gray-400 text-xs uppercase font-medium">Or Supabase Auth</span>
        <div className="flex-grow border-t border-gray-200"></div>
      </div>

      <Auth
        supabaseClient={supabase}
        appearance={{ theme: ThemeSupa }}
        providers={['github']}
      />
    </div>
  );
}
