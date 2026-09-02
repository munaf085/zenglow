import type { Metadata } from "next";
import Link from "next/link";
export const metadata: Metadata = {
  title: "About Us | Zenglow",
  description:
    "Learn more about Zenglow, our mission, vision, and commitment to helping you discover and book the best salons, spas, and wellness centres.",
  openGraph: {
    title: "About Us | Zenglow",
    description:
      "Learn more about Zenglow and our mission to make wellness discovery and booking simple.",
  },
};
export default function AboutPage() {
  return (
    <div className="bg-white text-gray-900">
      {/* Hero Section */}
      <section className="border-b border-gray-100 bg-gray-50">
        <div className="mx-auto max-w-7xl px-6 py-20 sm:px-8 lg:px-12">
          <div className="mx-auto max-w-3xl text-center">
            <p className="mb-4 text-sm font-semibold uppercase tracking-wide text-brand-600">
              About Zenglow
            </p>

            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl">
              Making beauty and wellness
              <span className="block text-brand-600">
                easier for everyone.
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-gray-500">
              Zenglow connects customers with salons, spas, and wellness
              centres while helping businesses manage their services,
              bookings, and customers with ease.
            </p>
          </div>
        </div>
      </section>

      {/* Introduction */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20 sm:px-8 lg:px-12">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div>
              <p className="mb-3 text-sm font-semibold text-brand-600">
                Who we are
              </p>

              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                Your ultimate platform for salons and spas
              </h2>
            </div>

            <div className="space-y-5 text-base leading-7 text-gray-600">
              <p>
                Zenglow is designed to make discovering and booking beauty
                and wellness services simple and convenient.
              </p>

              <p>
                From finding the right salon or spa to booking an appointment,
                Zenglow brings the experience together in one easy-to-use
                platform.
              </p>

              <p>
                For businesses, Zenglow provides tools that help simplify
                everyday operations, manage bookings, and build stronger
                relationships with customers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Mission & Vision */}
      <section className="bg-gray-50">
        <div className="mx-auto max-w-7xl px-6 py-20 sm:px-8 lg:px-12">
          <div className="mb-12 text-center">
            <p className="mb-3 text-sm font-semibold text-brand-600">
              What drives us
            </p>

            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              Our Mission & Vision
            </h2>
          </div>

          <div className="grid gap-8 md:grid-cols-2">
            {/* Mission */}
            <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50">
                <span className="text-xl font-bold text-brand-600">M</span>
              </div>

              <h3 className="mb-4 text-2xl font-bold text-gray-900">
                Our Mission
              </h3>

              <p className="leading-7 text-gray-600">
                Our mission is to simplify the way people discover and book
                beauty and wellness services while giving salons and spas the
                tools they need to grow and succeed.
              </p>
            </div>

            {/* Vision */}
            <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50">
                <span className="text-xl font-bold text-brand-600">V</span>
              </div>

              <h3 className="mb-4 text-2xl font-bold text-gray-900">
                Our Vision
              </h3>

              <p className="leading-7 text-gray-600">
                We envision a connected beauty and wellness ecosystem where
                customers can easily find trusted businesses and businesses
                can focus on delivering exceptional experiences.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20 sm:px-8 lg:px-12">
          <div className="mx-auto mb-12 max-w-2xl text-center">
            <p className="mb-3 text-sm font-semibold text-brand-600">
              What matters to us
            </p>

            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              Our Values
            </h2>

            <p className="mt-4 text-gray-500">
              The principles that guide how we build Zenglow.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {/* Excellence */}
            <div className="rounded-2xl border border-gray-200 bg-white p-7 transition-shadow hover:shadow-md">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50">
                <span className="font-bold text-brand-600">01</span>
              </div>

              <h3 className="mb-3 text-xl font-bold text-gray-900">
                Excellence
              </h3>

              <p className="leading-7 text-gray-600">
                We strive to create reliable, useful, and enjoyable
                experiences for every customer and business.
              </p>
            </div>

            {/* Innovation */}
            <div className="rounded-2xl border border-gray-200 bg-white p-7 transition-shadow hover:shadow-md">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50">
                <span className="font-bold text-brand-600">02</span>
              </div>

              <h3 className="mb-3 text-xl font-bold text-gray-900">
                Innovation
              </h3>

              <p className="leading-7 text-gray-600">
                We continuously improve our platform to make booking and
                business management simpler.
              </p>
            </div>

            {/* Customer Focus */}
            <div className="rounded-2xl border border-gray-200 bg-white p-7 transition-shadow hover:shadow-md">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50">
                <span className="font-bold text-brand-600">03</span>
              </div>

              <h3 className="mb-3 text-xl font-bold text-gray-900">
                Customer Focus
              </h3>

              <p className="leading-7 text-gray-600">
                We put our customers and business partners at the centre of
                everything we build.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why Zenglow */}
      <section className="bg-gray-50">
        <div className="mx-auto max-w-7xl px-6 py-20 sm:px-8 lg:px-12">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div>
              <p className="mb-3 text-sm font-semibold text-brand-600">
                Why Zenglow?
              </p>

              <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
                Everything you need in one place.
              </h2>

              <p className="mt-5 leading-7 text-gray-600">
                Whether you're looking for your next appointment or managing
                a growing salon or spa, Zenglow is built to make the
                experience easier.
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-4 rounded-xl bg-white p-5 shadow-sm">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50">
                  <span className="font-bold text-brand-600">✓</span>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900">
                    Easy appointment discovery
                  </h3>

                  <p className="mt-1 text-sm leading-6 text-gray-500">
                    Find salons, spas, and wellness services with ease.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 rounded-xl bg-white p-5 shadow-sm">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50">
                  <span className="font-bold text-brand-600">✓</span>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900">
                    Simple booking experience
                  </h3>

                  <p className="mt-1 text-sm leading-6 text-gray-500">
                    Book appointments through a straightforward experience.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 rounded-xl bg-white p-5 shadow-sm">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50">
                  <span className="font-bold text-brand-600">✓</span>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900">
                    Better business management
                  </h3>

                  <p className="mt-1 text-sm leading-6 text-gray-500">
                    Help salons and spas manage their daily operations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-brand-600">
        <div className="mx-auto max-w-4xl px-6 py-16 text-center sm:px-8">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ready to discover Zenglow?
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-brand-100">
            Discover salons, spas, and wellness centres near you and find
            your next appointment.
          </p>

          <Link
            href="/explore"
            className="mt-8 inline-flex rounded-lg bg-white px-7 py-3 font-semibold text-brand-600 transition-colors hover:bg-gray-100"
          >
            Explore Businesses
          </Link>
        </div>
      </section>
    </div>
  );
}