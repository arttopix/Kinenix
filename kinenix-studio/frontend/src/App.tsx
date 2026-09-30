import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Timeline } from './components/Timeline';
import { Inspector } from './components/Inspector';
import { ContextPanel } from './components/ContextPanel';
import { FlowSummary, FlowDetailResponse, Step, ActionMeta } from './types';
import { CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [flows, setFlows] = useState<FlowSummary[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>('');
  const [flowDetail, setFlowDetail] = useState<FlowDetailResponse | null>(null);
  const [activeStep, setActiveStep] = useState<Step | null>(null);
  const [actions, setActions] = useState<ActionMeta[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // 1. Fetch available flows and action catalog on mount
  useEffect(() => {
    fetchFlows();
    fetchActions();
  }, []);

  const fetchFlows = async () => {
    try {
      const res = await fetch('/api/flows');
      const data: FlowSummary[] = await res.json();
      setFlows(data);
      if (data.length > 0) {
        // Default to rpachallenge if found, otherwise first flow
        const defaultFlow = data.find(f => f.path.includes('rpachallenge')) || data[0];
        setSelectedPath(defaultFlow.path);
        loadFlow(defaultFlow.path);
      }
    } catch (err) {
      console.error('Failed to fetch flows:', err);
    }
  };

  const fetchActions = async () => {
    try {
      const res = await fetch('/api/actions');
      const data = await res.json();
      setActions(data.actions || []);
    } catch (err) {
      console.error('Failed to fetch actions:', err);
    }
  };

  const loadFlow = async (path: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/flow?path=${encodeURIComponent(path)}`);
      if (!res.ok) throw new Error('Failed to load flow');
      const data: FlowDetailResponse = await res.json();
      setFlowDetail(data);

      // Select first step by default
      if (data.flow.steps && data.flow.steps.length > 0) {
        setActiveStep(data.flow.steps[0]);
      } else {
        setActiveStep(null);
      }
    } catch (err) {
      console.error('Error loading flow:', err);
      showToast('Error loading flow from backend');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFlow = (path: string) => {
    setSelectedPath(path);
    loadFlow(path);
  };

  const handleSaveStep = async (updatedStep: Step): Promise<boolean> => {
    if (!selectedPath) return false;

    try {
      const res = await fetch('/api/flow/step', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: selectedPath,
          step_id: updatedStep.id,
          step: updatedStep
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Validation error');
      }

      showToast(`Step '${updatedStep.id}' updated successfully!`);
      // Reload flow state to reflect any downstream updates
      await loadFlow(selectedPath);
      setActiveStep(updatedStep);
      return true;
    } catch (err: any) {
      console.error('Failed to update step:', err);
      showToast(`Save Error: ${err.message || 'Unknown error'}`);
      return false;
    }
  };

  return (
    <div className="app-container">
      <Header
        flows={flows}
        selectedPath={selectedPath}
        onSelectFlow={handleSelectFlow}
        onRefresh={() => selectedPath && loadFlow(selectedPath)}
        isLoading={isLoading}
      />

      <div className="workspace-grid">
        <Timeline
          steps={flowDetail?.flow.steps || []}
          activeStepId={activeStep?.id || null}
          onSelectStep={(step) => setActiveStep(step)}
        />

        <Inspector
          step={activeStep}
          onSaveStep={handleSaveStep}
        />

        <ContextPanel
          config={flowDetail?.config || {}}
          variables={flowDetail?.flow.variables || {}}
          actions={actions}
          flowRawJson={flowDetail?.flow ? JSON.stringify(flowDetail.flow, null, 2) : '{}'}
        />
      </div>

      {toastMessage && (
        <div className="toast">
          <CheckCircle2 size={16} color="#10b981" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
};
export default App;
