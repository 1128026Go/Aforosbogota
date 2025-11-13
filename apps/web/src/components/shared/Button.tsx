import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  ...props
}: ButtonProps) {
  const baseStyles = {
    padding: size === 'sm' ? '6px 12px' : size === 'lg' ? '12px 24px' : '8px 16px',
    fontSize: size === 'sm' ? '14px' : size === 'lg' ? '16px' : '14px',
    borderRadius: '6px',
    border: 'none',
    cursor: props.disabled ? 'not-allowed' : 'pointer',
    fontWeight: '500',
    transition: 'all 0.2s',
    opacity: props.disabled ? 0.5 : 1,
  };

  const variants = {
    primary: { backgroundColor: '#3b82f6', color: 'white' },
    secondary: { backgroundColor: '#e5e7eb', color: '#374151' },
    danger: { backgroundColor: '#ef4444', color: 'white' },
    success: { backgroundColor: '#10b981', color: 'white' },
  };

  return (
    <button
      {...props}
      className={className}
      style={{ ...baseStyles, ...variants[variant], ...props.style }}
    >
      {children}
    </button>
  );
}
