import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded font-medium text-sm transition-all duration-fast ease-damay focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // PRIMARY — brand terracotta, one per view, the single most important action
        primary:
          "bg-brand text-white shadow-sm hover:bg-brand-hover active:bg-brand-hover",
        // SECONDARY — outlined, calm, supporting
        secondary:
          "border border-fg-base bg-transparent text-fg-base hover:bg-bg-subtle",
        // GHOST — tertiary, in-row, icon buttons
        ghost: "bg-transparent text-fg-muted hover:bg-bg-subtle hover:text-fg-base",
        // DESTRUCTIVE — close round, remove member
        destructive:
          "border border-danger bg-transparent text-danger hover:bg-danger/10",
        // ACCENT — for "View on Stellar Expert" linkish actions only
        accent: "bg-accent text-white hover:bg-accent-hover",
        // LINK — text-only inline action
        link: "text-accent underline-offset-4 hover:underline hover:text-accent-hover px-0",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-5 py-2",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
