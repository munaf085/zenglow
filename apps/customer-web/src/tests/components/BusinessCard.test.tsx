import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BusinessCard } from "@/components/business/BusinessCard";
import type { Business } from "@zenglow/types";

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <img alt={alt} />,
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

const mockBusiness: Business = {
  id: "biz-1",
  slug: "glow-studio",
  owner_id: "owner-1",
  name: "Glow Studio",
  category: "SALON",
  description: "Premium hair salon",
  logo_url: null,
  cover_image_url: null,
  email: "hello@glowstudio.com",
  phone: "+91 98765 43210",
  website: null,
  status: "ACTIVE",
  is_verified: true,
  is_featured: true,
  booking_advance_days: 60,
  cancellation_hours: 24,
  cancellation_policy: null,
  deposit_required: false,
  deposit_percentage: null,
  branches: [
    {
      id: "branch-1",
      business_id: "biz-1",
      name: "Main Branch",
      is_primary: true,
      is_active: true,
      city: "Mumbai",
      state: "Maharashtra",
      country: "India",
      postal_code: "400001",
      created_at: new Date().toISOString(),
    },
  ],
  created_at: new Date().toISOString(),
};

describe("BusinessCard", () => {
  it("renders business name", () => {
    render(<BusinessCard business={mockBusiness} />);
    expect(screen.getByText("Glow Studio")).toBeInTheDocument();
  });

  it("renders category label", () => {
    render(<BusinessCard business={mockBusiness} />);
    expect(screen.getByText("Salon")).toBeInTheDocument();
  });

  it("renders city from primary branch", () => {
    render(<BusinessCard business={mockBusiness} />);
    expect(screen.getByText("Mumbai")).toBeInTheDocument();
  });

  it("renders verified badge when is_verified is true", () => {
    render(<BusinessCard business={mockBusiness} />);
    const badge = screen.getByLabelText("Verified");
    expect(badge).toBeInTheDocument();
  });

  it("renders featured badge when is_featured is true", () => {
    render(<BusinessCard business={mockBusiness} />);
    expect(screen.getByText("Featured")).toBeInTheDocument();
  });

  it("renders a link to business detail page", () => {
    render(<BusinessCard business={mockBusiness} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/business/glow-studio");
  });

  it("renders description", () => {
    render(<BusinessCard business={mockBusiness} />);
    expect(screen.getByText("Premium hair salon")).toBeInTheDocument();
  });

  it("does not show verified badge when not verified", () => {
    render(<BusinessCard business={{ ...mockBusiness, is_verified: false }} />);
    expect(screen.queryByLabelText("Verified")).not.toBeInTheDocument();
  });

  it("does not show featured badge when not featured", () => {
    render(<BusinessCard business={{ ...mockBusiness, is_featured: false }} />);
    expect(screen.queryByText("Featured")).not.toBeInTheDocument();
  });
});
