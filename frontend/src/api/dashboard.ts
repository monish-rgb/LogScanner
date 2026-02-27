import apiClient from './client';
import type { PaginatedEntries, PaginatedFiles } from '../types/logEntry';
import type { AnalysisResponse, AnalysisSummary, AnalyzeTriggerResponse } from '../types/analysis';

export async function getFiles(page = 1, perPage = 10): Promise<PaginatedFiles> {
  const response = await apiClient.get<PaginatedFiles>('/dashboard/files', {
    params: { page, per_page: perPage },
  });
  return response.data;
}

export async function getFileDetail(fileId: number) {
  const response = await apiClient.get(`/dashboard/files/${fileId}`);
  return response.data;
}

export async function getEntries(
  fileId: number,
  page = 1,
  perPage = 50,
  anomalousOnly = false
): Promise<PaginatedEntries> {
  const response = await apiClient.get<PaginatedEntries>(
    `/dashboard/files/${fileId}/entries`,
    { params: { page, per_page: perPage, anomalous_only: anomalousOnly } }
  );
  return response.data;
}

export async function getAnomalies(fileId: number): Promise<AnalysisResponse> {
  const response = await apiClient.get<AnalysisResponse>(
    `/dashboard/files/${fileId}/anomalies`
  );
  return response.data;
}

export async function triggerAnalysis(fileId: number): Promise<AnalyzeTriggerResponse> {
  const response = await apiClient.post<AnalyzeTriggerResponse>(
    `/dashboard/files/${fileId}/analyze`
  );
  return response.data;
}

export async function getSummary(fileId: number): Promise<AnalysisSummary> {
  const response = await apiClient.get<AnalysisSummary>(
    `/dashboard/files/${fileId}/summary`
  );
  return response.data;
}
