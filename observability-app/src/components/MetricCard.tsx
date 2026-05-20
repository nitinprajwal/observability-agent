import React, { type ReactNode } from 'react';

interface MetricCardProps {
  title: string;
  children: ReactNode;
  value?: string | number;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export const MetricCard: React.FC<MetricCardProps> = ({ title, children, value, trend }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex flex-col h-full">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        {value !== undefined && (
          <div className="text-right">
            <span className="text-xl font-semibold text-gray-900">{value}</span>
            {trend && (
              <span className={`text-xs ml-2 ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
            )}
          </div>
        )}
      </div>
      <div className="flex-1 min-h-[160px] w-full">
        {children}
      </div>
    </div>
  );
};
