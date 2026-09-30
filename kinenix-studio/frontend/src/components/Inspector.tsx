import React, { useState, useEffect } from 'react';
import { Sliders, Save, Code } from 'lucide-react';
import { Step } from '../types';

interface InspectorProps {
  step: Step | null;
  onSaveStep: (updatedStep: Step) => Promise<boolean>;
}

export const Inspector: React.FC<InspectorProps> = ({ step, onSaveStep }) => {
  const [formData, setFormData] = useState<Step | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (step) {
      setFormData(JSON.parse(JSON.stringify(step)));
    } else {
      setFormData(null);
    }
  }, [step]);

  if (!formData) {
    return (
      <main className="inspector-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#64748b' }}>
          <Sliders size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
          <h3 style={{ fontSize: '15px', color: '#94a3b8', marginBottom: '6px' }}>No Step Selected</h3>
          <p style={{ fontSize: '13px' }}>Select any step from the left timeline to inspect and tune its parameters.</p>
        </div>
      </main>
    );
  }

  const handleParamChange = (key: string, value: any) => {
    setFormData((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        parameters: {
          ...prev.parameters,
          [key]: value
        }
      };
    });
  };

  const handleSave = async () => {
    if (!formData) return;
    setIsSaving(true);
    await onSaveStep(formData);
    setIsSaving(false);
  };

  return (
    <main className="inspector-panel">
      <div className="inspector-card">
        <div className="inspector-header">
          <div className="inspector-headline">
            <Sliders size={20} color="#3b82f6" />
            <div>
              <h2 className="inspector-title">{formData.name}</h2>
              <span style={{ fontSize: '12px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                ID: {formData.id} &nbsp;|&nbsp; Action: {formData.action}
              </span>
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={isSaving}
          >
            <Save size={14} />
            <span>{isSaving ? 'Updating...' : 'Update This Step'}</span>
          </button>
        </div>

        {/* Step Name */}
        <div className="form-group">
          <label className="form-label">Step Name</label>
          <input
            type="text"
            className="form-input"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Step description or business name"
          />
        </div>

        {/* Dynamic Action Parameters Section */}
        <div className="params-section">
          <div className="params-header">
            <Code size={15} />
            <span>Action Parameters</span>
          </div>

          {Object.keys(formData.parameters || {}).length === 0 ? (
            <div style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic' }}>
              No parameters required for this action.
            </div>
          ) : (
            Object.entries(formData.parameters).map(([key, val]) => {
              const isBool = typeof val === 'boolean';
              const isObj = typeof val === 'object' && val !== null;

              return (
                <div key={key} className="form-group">
                  <label className="form-label">
                    <span>{key}</span>
                  </label>

                  {isBool ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <input
                        type="checkbox"
                        checked={val}
                        id={`param-${key}`}
                        onChange={(e) => handleParamChange(key, e.target.checked)}
                        style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                      />
                      <label htmlFor={`param-${key}`} style={{ fontSize: '13px', color: '#f1f5f9', cursor: 'pointer' }}>
                        {val ? 'Enabled (true)' : 'Disabled (false)'}
                      </label>
                    </div>
                  ) : isObj ? (
                    <textarea
                      className="form-textarea"
                      rows={3}
                      value={typeof val === 'string' ? val : JSON.stringify(val, null, 2)}
                      onChange={(e) => {
                        try {
                          handleParamChange(key, JSON.parse(e.target.value));
                        } catch {
                          handleParamChange(key, e.target.value);
                        }
                      }}
                    />
                  ) : (
                    <input
                      type="text"
                      className="form-input"
                      value={String(val ?? '')}
                      onChange={(e) => handleParamChange(key, e.target.value)}
                    />
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Output Variable */}
        <div className="form-group">
          <label className="form-label">Output Variable (Optional)</label>
          <input
            type="text"
            className="form-input"
            value={formData.output_var || ''}
            onChange={(e) => setFormData({ ...formData, output_var: e.target.value || undefined })}
            placeholder="Store return value into ${variable_name}"
          />
        </div>
      </div>
    </main>
  );
};
