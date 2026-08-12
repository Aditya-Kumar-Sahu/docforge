'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';

export default function NavAuth() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      const hasDevToken = typeof window !== 'undefined' && !!localStorage.getItem('docforge_dev_token');
      setIsLoggedIn(!!session || hasDevToken);
    };

    checkAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_, session) => {
      const hasDevToken = typeof window !== 'undefined' && !!localStorage.getItem('docforge_dev_token');
      setIsLoggedIn(!!session || hasDevToken);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('docforge_dev_token');
    }
    await supabase.auth.signOut();
    setIsLoggedIn(false);
    router.push('/login?logout=true');
  };

  if (isLoggedIn) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-xs bg-green-100 text-green-800 font-medium px-2.5 py-1 rounded-full border border-green-200">
          ● Signed In
        </span>
        <button
          onClick={handleLogout}
          className="text-sm border border-gray-300 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-100 transition font-medium"
        >
          Log Out
        </button>
      </div>
    );
  }

  return (
    <Link
      href="/login"
      className="bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-700 transition"
    >
      Login
    </Link>
  );
}
