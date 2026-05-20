import React from 'react';

interface Column<T> {
  header: string;
  accessor: keyof T;
  render?: (value: T[keyof T], item: T) => React.ReactNode;
}

interface DataTableProps<T extends Record<string, unknown>> {
  columns: Column<T>[];
  data: T[];
}

export function DataTable<T extends Record<string, unknown>>({ columns, data }: DataTableProps<T>) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-gray-600">
          <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b border-gray-200">
            <tr>
              {columns.map((col, i) => (
                <th key={i} className="px-6 py-3 font-medium tracking-wider">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50/50 transition-colors bg-white">
                {columns.map((col, j) => (
                  <td key={j} className="px-6 py-4 whitespace-nowrap">
                    {col.render
                      ? col.render(row[col.accessor], row)
                      : String(row[col.accessor] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
