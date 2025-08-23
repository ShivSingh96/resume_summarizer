import React from 'react';

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'outlined';
}

export default function Card({ title, children, className = '', variant = 'default' }: CardProps) {
  const variantClasses = {
    default: 'bg-white shadow-md hover:shadow-lg',
    elevated: 'bg-white shadow-xl hover:shadow-2xl hover:translate-y-[-2px]',
    outlined: 'bg-white border border-gray-200 shadow-sm hover:border-blue-300 hover:shadow-md'
  };

  return (
    <div className={`rounded-xl overflow-hidden transition-all duration-300 ${variantClasses[variant]} ${className}`}>
      {title && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        </div>
      )}
      <div className="p-6 md:p-8">{children}</div>
    </div>
  );
}
