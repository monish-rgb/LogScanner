export interface LogEntry {
  id: number;
  log_file_id: number;
  line_number: number;
  timestamp: string | null;
  source_ip: string | null;
  destination_url: string | null;
  user: string | null;
  action: string | null;
  category: string | null;
  risk_score: number | null;
  bytes_transferred: number | null;
  response_time_ms: number | null;
  raw_line: string;
  is_anomalous: boolean;
}

export interface LogFile {
  id: number;
  user_id: number;
  original_filename: string;
  file_size: number;
  file_type: string;
  entry_count: number;
  upload_status: string;
  analysis_status: string;
  uploaded_at: string;
}

export interface PaginatedEntries {
  entries: LogEntry[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface PaginatedFiles {
  files: LogFile[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
