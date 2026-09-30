export interface Step {
  id: string;
  name: string;
  action: string;
  parameters: Record<string, any>;
  output_var?: string;
  condition?: string;
  sub_steps?: Step[];
  else_steps?: Step[];
}

export interface FlowDefinition {
  name: string;
  description?: string;
  version?: string;
  variables: Record<string, any>;
  steps: Step[];
}

export interface FlowSummary {
  name: string;
  description?: string;
  version?: string;
  path: string;
  bundle_dir: string;
  steps_count: number;
  has_config: boolean;
}

export interface FlowDetailResponse {
  path: string;
  bundle_dir: string;
  flow: FlowDefinition;
  config: Record<string, any>;
  is_valid: boolean;
  validation_error?: string | null;
}

export interface ActionMeta {
  type: string;
  class_name: string;
  module: string;
  description: string;
  docstring: string;
}
