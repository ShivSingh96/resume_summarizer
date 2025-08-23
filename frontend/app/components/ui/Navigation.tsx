import React from 'react';

interface NavTabProps {
  label: string;
  isActive: boolean;
  onClick: () => void;
  isFirst?: boolean;
  isLast?: boolean;
}

function NavTab({ label, isActive, onClick, isFirst, isLast }: NavTabProps) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-3 text-sm font-medium transition-all duration-300 ${
        isActive
          ? 'text-white bg-gradient-to-r from-blue-600 to-indigo-600 shadow-md'
          : 'bg-white text-gray-600 hover:text-blue-600 hover:bg-blue-50'
      } ${isFirst ? 'rounded-l-lg' : ''} ${isLast ? 'rounded-r-lg' : ''}`}
    >
      {label}
    </button>
  );
}

interface NavigationProps {
  activeView: string;
  onViewChange: (view: string) => void;
  views: { id: string; label: string }[];
}

export default function Navigation({ activeView, onViewChange, views }: NavigationProps) {
  return (
    <div className="flex justify-center mb-8">
      <div className="inline-flex rounded-lg shadow-md bg-white" role="group">
        {views.map((view, index) => (
          <NavTab
            key={view.id}
            label={view.label}
            isActive={activeView === view.id}
            onClick={() => onViewChange(view.id)}
            isFirst={index === 0}
            isLast={index === views.length - 1}
          />
        ))}
      </div>
    </div>
  );
}
