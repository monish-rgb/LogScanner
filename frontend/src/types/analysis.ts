import type { LogEntry } from './logEntry';

export interface Anomaly {
  id: number;
  log_file_id: number;
  log_entry_id: number | null;
  anomaly_type: string;
  confidence_score: number;
  explanation: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  log_entry?: LogEntry;
}

export interface AnalysisSummary {
  total_entries: number;
  total_anomalies: number;
  severity_breakdown: Record<string, number>;
  top_anomaly_types: Array<{ type: string; count: number }>;
  analysis_status: string;
  file: {
    id: number;
    original_filename: string;
    file_size: number;
    entry_count: number;
    upload_status: string;
    analysis_status: string;
    uploaded_at: string;
  };
}

export interface AnalysisResponse {
  anomalies: Anomaly[];
  total: number;
}

export interface AnalyzeTriggerResponse {
  status: string;
  anomalies_found: number;
}
