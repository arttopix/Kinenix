import React from 'react';
import { Layers, RefreshCw, Zap, ChevronDown } from 'lucide-react';
import { FlowSummary } from '../types';

interface HeaderProps {
  flows: FlowSummary[];
  selectedPath: string;
  onSelectFlow: (path: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  flows,
  selectedPath,
  onSelectFlow,
  onRefresh,
  isLoading
}) => {
  return (
    <header className="top-header">
      <div className="brand-section">
        <div className="brand-logo">
          <Zap size={18} />
        </div>
        <div>
          <span className="brand-title">Kinenix Studio</span>
        </div>
        <span className="brand-badge">Engine v0.1.0a1</span>
      </div>

      <div className="header-center">
        <div className="flow-selector-group">
          <Layers size={15} color="#94a3b8" />
          <select
            className="flow-selector-select"
            value={selectedPath}
            onChange={(e) => onSelectFlow(e.target.value)}
          >
            {flows.map((f) => (
              <option key={f.path} value={f.path}>
                {f.name} ({f.bundle_dir})
              </option>
            ))}
          </select>
          <ChevronDown size={14} color="#64748b" />
        </div>

        <button
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={isLoading}
          title="Reload Flow from disk"
        >
          <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
          <span>Reload</span>
        </button>
      </div>

      <div className="header-actions">
        <div className="env-badge">
          <span className="env-dot"></span>
          <span>FastAPI Connected</span>
        </div>
      </div>
    </header>
  );
};
