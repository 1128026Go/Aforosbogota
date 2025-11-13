import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export function Badge({ children, variant = 'default' }: BadgeProps) {
  const variants = {
    default: { backgroundColor: '#e5e7eb', color: '#374151' },
    success: { backgroundColor: '#d1fae5', color: '#065f46' },
    warning: { backgroundColor: '#fef3c7', color: '#92400e' },
    danger: { backgroundColor: '#fee2e2', color: '#991b1b' },
  };

  return (
    <span
      style={{
        ...variants[variant],
        padding: '2px 8px',
        borderRadius: '9999px',
        fontSize: '12px',
        fontWeight: '500',
        display: 'inline-block',
      }}
    >
      {children}
    </span>
  );
}
