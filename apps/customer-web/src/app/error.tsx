"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to error reporting service in production
    console.error("[CustomerWeb Error]", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 bg-red-50 rounded-3xl flex items-center justify-center mx-auto mb-6">
          <AlertTriangle className="w-10 h-10 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h1>
        <p className="text-gray-500 text-sm mb-8 leading-relaxed">
          An unexpected error occurred. Please try again, or return to the home page.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try again
          </button>
          <Link
            href="/"
            className="border border-gray-300 hover:bg-gray-100 text-gray-700 font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            Go home
          </Link>
        </div>
        {error.digest && (
          <p className="mt-6 text-xs text-gray-400 font-mono">
            Error ID: {error.digest}
          </p>
        )}
      </div>
    </div>
  );
}
