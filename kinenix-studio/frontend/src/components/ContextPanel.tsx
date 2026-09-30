import React, { useState } from 'react';
import { Database, BookOpen, Code2, Copy, Check } from 'lucide-react';
import { ActionMeta } from '../types';

interface ContextPanelProps {
  config: Record<string, any>;
  variables: Record<string, any>;
  actions: ActionMeta[];
  flowRawJson: string;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({
  config,
  variables,
  actions,
  flowRawJson
}) => {
  const [activeTab, setActiveTab] = useState<'config' | 'actions' | 'json'>('config');
  const [searchAction, setSearchAction] = useState('');
  const [copied, setCopied] = useState(false);

  const filteredActions = actions.filter((a) =>
    a.type.toLowerCase().includes(searchAction.toLowerCase()) ||
    a.description.toLowerCase().includes(searchAction.toLowerCase())
  );

  const handleCopy = () => {
    navigator.clipboard.writeText(flowRawJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <aside className="context-panel">
      <div className="tabs-header">
        <button
          className={`tab-btn ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          <Database size={13} style={{ display: 'inline', marginRight: '4px' }} />
          <span>Config & Vars</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'actions' ? 'active' : ''}`}
          onClick={() => setActiveTab('actions')}
        >
          <BookOpen size={13} style={{ display: 'inline', marginRight: '4px' }} />
          <span>Actions ({actions.length})</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'json' ? 'active' : ''}`}
          onClick={() => setActiveTab('json')}
        >
          <Code2 size={13} style={{ display: 'inline', marginRight: '4px' }} />
          <span>Raw JSON</span>
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'config' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <h4 style={{ fontSize: '12px', color: '#38bdf8', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' }}>
                Flow Config (${'{config.*}'})
              </h4>
              <div className="json-viewer">
                {Object.keys(config).length === 0
                  ? '// No config.json found in bundle'
                  : JSON.stringify(config, null, 2)}
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '12px', color: '#a855f7', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' }}>
                Initial Variables
              </h4>
              <div className="json-viewer">
                {Object.keys(variables).length === 0
                  ? '// No initial variables defined'
                  : JSON.stringify(variables, null, 2)}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'actions' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <input
              type="text"
              className="form-input"
              style={{ fontSize: '12px', padding: '8px 10px' }}
              placeholder="Filter actions (e.g. web, excel, ai)..."
              value={searchAction}
              onChange={(e) => setSearchAction(e.target.value)}
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {filteredActions.map((a) => (
                <div key={a.type} className="action-item">
                  <div className="action-item-title">{a.type}</div>
                  <div className="action-item-desc">{a.description || a.docstring.split('\n')[0]}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'json' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button className="btn btn-secondary btn-sm" onClick={handleCopy} style={{ alignSelf: 'flex-end' }}>
              {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
              <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
            </button>
            <div className="json-viewer" style={{ maxHeight: 'calc(100vh - 160px)', overflowY: 'auto' }}>
              {flowRawJson}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
