import React from 'react';
import { Home, Cpu, GitMerge, Brain, Terminal, FileText, Settings, HelpCircle, ChevronLeft, ChevronRight } from 'lucide-react';

interface SidebarProps {
  isExpanded: boolean;
  setIsExpanded: (expanded: boolean) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const navItems = [
  { id: 'Overview', icon: Home, label: 'Overview' },
  { id: 'Agent Pipeline', icon: Cpu, label: 'Agent Pipeline' },
  { id: 'A2A Flows', icon: GitMerge, label: 'A2A Flows' },
  { id: 'LLM Usage', icon: Brain, label: 'LLM Usage', badge: 'New' },
  { id: 'Sandbox', icon: Terminal, label: 'Sandbox' },
  { id: 'Logs', icon: FileText, label: 'Logs' },
];

const bottomItems = [
  { id: 'Settings', icon: Settings, label: 'Settings' },
  { id: 'Support', icon: HelpCircle, label: 'Support' },
];

export const Sidebar: React.FC<SidebarProps> = ({ isExpanded, setIsExpanded, activeTab, setActiveTab }) => {
  return (
    <div 
      className={`bg-gray-900 text-gray-300 h-screen flex flex-col transition-all duration-300 ${
        isExpanded ? 'w-60' : 'w-16'
      }`}
    >
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-gray-800">
        <div className="flex items-center gap-3 overflow-hidden whitespace-nowrap">
          <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center font-bold text-white shrink-0">
            N
          </div>
          {isExpanded && <span className="font-semibold text-white tracking-wide">NitroNode</span>}
        </div>
      </div>

      {/* Main Nav */}
      <div className="flex-1 py-4 flex flex-col gap-1 px-2 overflow-y-auto overflow-x-hidden">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-3 px-2 py-2 rounded-md transition-colors w-full text-left
                ${isActive ? 'bg-gray-800 text-white' : 'hover:bg-gray-800/50 hover:text-white'}
              `}
              title={!isExpanded ? item.label : undefined}
            >
              <Icon size={20} className={`shrink-0 ${isActive ? 'text-blue-400' : 'text-gray-400'}`} />
              
              {isExpanded && (
                <div className="flex-1 flex justify-between items-center whitespace-nowrap">
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Nav & Toggle */}
      <div className="border-t border-gray-800 p-2 flex flex-col gap-1">
        {bottomItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className="flex items-center gap-3 px-2 py-2 rounded-md text-gray-400 hover:bg-gray-800 hover:text-white transition-colors w-full text-left"
              title={!isExpanded ? item.label : undefined}
            >
              <Icon size={20} className="shrink-0" />
              {isExpanded && <span className="whitespace-nowrap">{item.label}</span>}
            </button>
          );
        })}
        
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-3 px-2 py-2 mt-2 rounded-md text-gray-500 hover:bg-gray-800 hover:text-white transition-colors w-full justify-center"
        >
          {isExpanded ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>
    </div>
  );
};
