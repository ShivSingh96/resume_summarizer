import React from 'react';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  return (
    <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700 py-12 px-6 mb-8 rounded-lg shadow-lg overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 w-full h-full opacity-10">
        <div className="absolute top-0 right-0 -mt-20 -mr-20 w-40 h-40 bg-white rounded-full opacity-20"></div>
        <div className="absolute bottom-0 left-0 -mb-10 -ml-10 w-60 h-60 bg-white rounded-full opacity-10"></div>
        <div className="absolute top-1/3 left-1/4 w-16 h-16 bg-white rounded-full opacity-20"></div>
        <div className="absolute bottom-1/4 right-1/4 w-24 h-24 bg-white rounded-full opacity-15"></div>
      </div>
      
      {/* Light grid overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/[0.05] to-transparent opacity-30 mix-blend-overlay"></div>
      
      {/* Content */}
      <div className="relative max-w-7xl mx-auto text-center">
        <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-3 tracking-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-3 text-xl text-blue-100 max-w-3xl mx-auto font-light">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
