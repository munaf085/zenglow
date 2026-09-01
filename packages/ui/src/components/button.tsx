import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:     "bg-brand-600 text-white hover:bg-brand-700 focus-visible:ring-brand-500",
        destructive: "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500",
        outline:     "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus-visible:ring-brand-500",
        secondary:   "bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-500",
        ghost:       "text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-500",
        link:        "text-brand-600 underline-offset-4 hover:underline focus-visible:ring-brand-500",
        success:     "bg-green-600 text-white hover:bg-green-700 focus-visible:ring-green-500",
        warning:     "bg-amber-500 text-white hover:bg-amber-600 focus-visible:ring-amber-400",
      },
      size: {
        default: "h-10 px-5 py-2.5",
        sm:      "h-8 px-3 py-1.5 text-xs",
        lg:      "h-12 px-8 py-3 text-base",
        xl:      "h-14 px-10 py-3.5 text-base",
        icon:    "h-10 w-10",
        "icon-sm": "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg
              className="h-4 w-4 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {children}
          </span>
        ) : children}
      </Comp>
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
