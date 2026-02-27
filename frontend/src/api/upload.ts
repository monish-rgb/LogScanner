import apiClient from './client';

export interface UploadResponse {
  file_id: number;
  original_filename: string;
  entry_count: number;
  upload_status: string;
  analysis_status: string;
}

export interface UploadStatusResponse {
  file_id: number;
  upload_status: string;
  analysis_status: string;
  entry_count: number;
}

export async function uploadFile(
  file: File,
  onProgress: (percent: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });

  return response.data;
}

export async function getUploadStatus(fileId: number): Promise<UploadStatusResponse> {
  const response = await apiClient.get<UploadStatusResponse>(`/upload/${fileId}/status`);
  return response.data;
}
