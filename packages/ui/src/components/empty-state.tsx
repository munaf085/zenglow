import * as React from "react";
import { cn } from "../lib/utils";

interface EmptyStateProps {
  icon?: React.ReactNode;
  emoji?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

function EmptyState({ icon, emoji, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center text-center py-16 px-4", className)}>
      {emoji && <p className="text-5xl mb-4">{emoji}</p>}
      {icon && (
        <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mb-4 text-gray-400">
          {icon}
        </div>
      )}
      <h3 className="font-semibold text-gray-900 text-base mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 max-w-sm leading-relaxed mb-6">{description}</p>
      )}
      {action}
    </div>
  );
}

export { EmptyState };
