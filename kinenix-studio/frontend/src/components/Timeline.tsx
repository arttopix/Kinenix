import React from 'react';
import { ListOrdered, Globe, FileSpreadsheet, GitBranch, Cpu, Mail, ArrowRight } from 'lucide-react';
import { Step } from '../types';

interface TimelineProps {
  steps: Step[];
  activeStepId: string | null;
  onSelectStep: (step: Step) => void;
}

const getActionClass = (action: string) => {
  if (action.startsWith('web.')) return 'action-badge web';
  if (action.startsWith('excel.') || action.startsWith('csv.')) return 'action-badge excel';
  if (action.startsWith('logic.')) return 'action-badge logic';
  if (action.startsWith('ai.')) return 'action-badge ai';
  return 'action-badge';
};

const getActionIcon = (action: string) => {
  if (action.startsWith('web.')) return <Globe size={13} />;
  if (action.startsWith('excel.')) return <FileSpreadsheet size={13} />;
  if (action.startsWith('logic.')) return <GitBranch size={13} />;
  if (action.startsWith('ai.')) return <Cpu size={13} />;
  if (action.startsWith('email.')) return <Mail size={13} />;
  return <ArrowRight size={13} />;
};

export const Timeline: React.FC<TimelineProps> = ({
  steps,
  activeStepId,
  onSelectStep
}) => {
  const renderStep = (step: Step, isNested: boolean = false) => {
    const isActive = activeStepId === step.id;

    return (
      <div key={step.id} style={{ display: 'flex', flexDirection: 'column' }}>
        <div
          className={`${isNested ? 'sub-step-card' : 'step-card'} ${isActive ? 'active' : ''}`}
          onClick={() => onSelectStep(step)}
        >
          <div className="step-card-top">
            <span className={getActionClass(step.action)} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              {getActionIcon(step.action)}
              <span>{step.action}</span>
            </span>
            <span className="step-id">{step.id}</span>
          </div>
          <div className="step-name">{step.name}</div>
        </div>

        {/* Nested Sub-steps (for logic.loop or logic.if) */}
        {step.sub_steps && step.sub_steps.length > 0 && (
          <div className="sub-steps-container">
            {step.sub_steps.map((sub) => renderStep(sub, true))}
          </div>
        )}

        {/* Else Steps */}
        {step.else_steps && step.else_steps.length > 0 && (
          <div className="sub-steps-container" style={{ borderLeftColor: 'rgba(244, 63, 94, 0.3)' }}>
            <div style={{ fontSize: '10px', color: '#f43f5e', fontWeight: 600, padding: '2px 6px' }}>ELSE</div>
            {step.else_steps.map((els) => renderStep(els, true))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside className="timeline-panel">
      <div className="panel-header">
        <div className="panel-title">
          <ListOrdered size={15} color="#3b82f6" />
          <span>Steps Timeline</span>
        </div>
        <span className="panel-count-badge">{steps.length} Steps</span>
      </div>

      <div className="steps-list">
        {steps.map((step) => renderStep(step, false))}
      </div>
    </aside>
  );
};
