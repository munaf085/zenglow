import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SearchBar } from "@/components/search/SearchBar";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(),
}));

describe("SearchBar", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("renders search input and city input", () => {
    render(<SearchBar />);
    expect(screen.getByPlaceholderText(/search salons/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/city/i)).toBeInTheDocument();
  });

  it("renders the search button", () => {
    render(<SearchBar />);
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  it("navigates to explore with query on submit", async () => {
    render(<SearchBar />);
    const input = screen.getByPlaceholderText(/search salons/i);
    fireEvent.change(input, { target: { value: "haircut" } });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));
    expect(mockPush).toHaveBeenCalledWith(expect.stringContaining("q=haircut"));
  });

  it("navigates to explore with city on submit", () => {
    render(<SearchBar />);
    const cityInput = screen.getByPlaceholderText(/city/i);
    fireEvent.change(cityInput, { target: { value: "Mumbai" } });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));
    expect(mockPush).toHaveBeenCalledWith(expect.stringContaining("city=Mumbai"));
  });

  it("includes both query and city in url", () => {
    render(<SearchBar />);
    fireEvent.change(screen.getByPlaceholderText(/search salons/i), {
      target: { value: "spa" },
    });
    fireEvent.change(screen.getByPlaceholderText(/city/i), {
      target: { value: "Delhi" },
    });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));
    const call = mockPush.mock.calls[0][0] as string;
    expect(call).toContain("q=spa");
    expect(call).toContain("city=Delhi");
  });
});
