import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DropZone from '../components/upload/DropZone';
import ProgressBar from '../components/upload/ProgressBar';
import { uploadFile } from '../api/upload';
import type { UploadResponse } from '../api/upload';

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

export default function UploadPage() {
  const [state, setState] = useState<UploadState>('idle');
  const [progress, setProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const navigate = useNavigate();

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setState('uploading');
    setProgress(0);
    setErrorMsg('');

    try {
      const response = await uploadFile(file, setProgress);
      setResult(response);
      setState('success');
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        'Upload failed';
      setErrorMsg(message);
      setState('error');
    }
  };

  const handleAnalyze = () => {
    if (result) {
      navigate(`/dashboard/${result.file_id}`);
    }
  };

  const handleReset = () => {
    setState('idle');
    setProgress(0);
    setSelectedFile(null);
    setResult(null);
    setErrorMsg('');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Upload Log File</h1>

      <div className="bg-slate-800 rounded-lg p-6 shadow-lg">
        {state === 'idle' && (
          <DropZone onFileSelect={handleFileSelect} />
        )}

        {state === 'uploading' && (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent" />
              <span className="text-slate-300">Uploading & parsing {selectedFile?.name}...</span>
            </div>
            <ProgressBar percent={progress} label="Upload Progress" />
          </div>
        )}

        {state === 'success' && result && (
          <div className="space-y-4">
            <div className="p-4 bg-green-900/30 border border-green-700 rounded-lg">
              <h3 className="text-green-400 font-semibold mb-2">Upload Successful</h3>
              <div className="text-sm text-slate-300 space-y-1">
                <p>File: {result.original_filename}</p>
                <p>Entries parsed: {result.entry_count}</p>
                <p>Status: {result.upload_status}</p>
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleAnalyze}
                className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
              >
                View & Analyze
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-md transition-colors"
              >
                Upload Another
              </button>
            </div>
          </div>
        )}

        {state === 'error' && (
          <div className="space-y-4">
            <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg">
              <h3 className="text-red-400 font-semibold mb-1">Upload Failed</h3>
              <p className="text-sm text-red-300">{errorMsg}</p>
            </div>
            <button
              onClick={handleReset}
              className="w-full py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-md transition-colors"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
