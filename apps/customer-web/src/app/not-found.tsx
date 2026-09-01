import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 bg-brand-50 rounded-3xl flex items-center justify-center mx-auto mb-6">
          <span className="text-5xl">🔍</span>
        </div>
        <h1 className="text-6xl font-bold text-gray-900 mb-2">404</h1>
        <h2 className="text-xl font-semibold text-gray-700 mb-3">Page not found</h2>
        <p className="text-gray-500 text-sm mb-8 leading-relaxed">
          The page you're looking for doesn't exist or may have been moved.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            Go home
          </Link>
          <Link
            href="/explore"
            className="border border-gray-300 hover:bg-gray-100 text-gray-700 font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            Explore businesses
          </Link>
        </div>
      </div>
    </div>
  );
}
