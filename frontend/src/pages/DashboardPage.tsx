import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getFiles, getEntries, getAnomalies, getSummary, triggerAnalysis } from '../api/dashboard';
import type { LogFile, LogEntry } from '../types/logEntry';
import type { Anomaly, AnalysisSummary } from '../types/analysis';
import SummaryStats from '../components/dashboard/SummaryStats';
import LogTable from '../components/dashboard/LogTable';
import AnomalyCard from '../components/dashboard/AnomalyCard';

type Tab = 'entries' | 'anomalies';

export default function DashboardPage() {
  const { fileId } = useParams<{ fileId: string }>();
  const navigate = useNavigate();

  const [files, setFiles] = useState<LogFile[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(
    fileId ? parseInt(fileId) : null
  );

  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [anomalousOnly, setAnomalousOnly] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('entries');

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [loading, setLoading] = useState(false);

  // Load file list
  useEffect(() => {
    getFiles(1, 50).then((data) => setFiles(data.files)).catch(() => {});
  }, []);

  // Load file data when selected
  const loadFileData = useCallback(async (fId: number) => {
    setLoading(true);
    try {
      const [entryData, summaryData] = await Promise.all([
        getEntries(fId, 1, 50, anomalousOnly),
        getSummary(fId),
      ]);
      setEntries(entryData.entries);
      setPage(entryData.page);
      setTotalPages(entryData.pages);
      setSummary(summaryData);

      if (summaryData.analysis_status === 'completed') {
        const anomalyData = await getAnomalies(fId);
        setAnomalies(anomalyData.anomalies);
      } else {
        setAnomalies([]);
      }
    } catch {
      // handle silently
    } finally {
      setLoading(false);
    }
  }, [anomalousOnly]);

  useEffect(() => {
    if (selectedFileId) loadFileData(selectedFileId);
  }, [selectedFileId, loadFileData]);

  const handleFileSelect = (fId: number) => {
    setSelectedFileId(fId);
    setPage(1);
    setAnomalousOnly(false);
    setActiveTab('entries');
    navigate(`/dashboard/${fId}`);
  };

  const handlePageChange = async (newPage: number) => {
    if (!selectedFileId) return;
    setLoading(true);
    try {
      const data = await getEntries(selectedFileId, newPage, 50, anomalousOnly);
      setEntries(data.entries);
      setPage(data.page);
      setTotalPages(data.pages);
    } catch {
      // handle silently
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAnomalous = async () => {
    if (!selectedFileId) return;
    const newVal = !anomalousOnly;
    setAnomalousOnly(newVal);
    setPage(1);
    setLoading(true);
    try {
      const data = await getEntries(selectedFileId, 1, 50, newVal);
      setEntries(data.entries);
      setPage(data.page);
      setTotalPages(data.pages);
    } catch {
      // handle silently
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFileId) return;
    setIsAnalyzing(true);
    setAnalysisError('');
    try {
      await triggerAnalysis(selectedFileId);
      await loadFileData(selectedFileId);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        'Analysis failed';
      setAnalysisError(message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // File list sidebar + main content
  return (
    <div className="flex gap-6">
      {/* File list sidebar */}
      <div className="w-64 flex-shrink-0">
        <h2 className="text-lg font-semibold text-white mb-3">Uploaded Files</h2>
        <div className="space-y-2">
          {files.length === 0 && (
            <p className="text-sm text-slate-500">No files uploaded yet</p>
          )}
          {files.map((file) => (
            <button
              key={file.id}
              onClick={() => handleFileSelect(file.id)}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selectedFileId === file.id
                  ? 'bg-blue-900/30 border-blue-700'
                  : 'bg-slate-800 border-slate-700 hover:border-slate-600'
              }`}
            >
              <p className="text-sm text-slate-200 truncate">{file.original_filename}</p>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-slate-500">{file.entry_count} entries</span>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    file.analysis_status === 'completed'
                      ? 'bg-green-900/50 text-green-400'
                      : file.analysis_status === 'analyzing'
                      ? 'bg-yellow-900/50 text-yellow-400'
                      : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {file.analysis_status}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {!selectedFileId ? (
          <div className="text-center py-16 text-slate-500">
            <p className="text-lg">Select a file to view its analysis</p>
            <p className="text-sm mt-2">Or upload a new file from the Upload page</p>
          </div>
        ) : loading && !entries.length ? (
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto" />
            <p className="text-slate-400 mt-4">Loading...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary stats */}
            {summary && <SummaryStats summary={summary} />}

            {/* Analysis controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {summary?.analysis_status !== 'completed' && (
                  <button
                    onClick={handleAnalyze}
                    disabled={isAnalyzing}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md transition-colors flex items-center space-x-2"
                  >
                    {isAnalyzing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                        <span>Analyzing with AI...</span>
                      </>
                    ) : (
                      <span>Analyze with AI</span>
                    )}
                  </button>
                )}
                {summary?.analysis_status === 'completed' && (
                  <button
                    onClick={handleAnalyze}
                    disabled={isAnalyzing}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:cursor-not-allowed text-slate-300 text-sm rounded-md transition-colors"
                  >
                    Re-analyze
                  </button>
                )}
              </div>
              {analysisError && (
                <span className="text-sm text-red-400">{analysisError}</span>
              )}
            </div>

            {/* Tabs */}
            <div className="border-b border-slate-700">
              <div className="flex space-x-4">
                <button
                  onClick={() => setActiveTab('entries')}
                  className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'entries'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-slate-400 hover:text-slate-300'
                  }`}
                >
                  Log Entries
                </button>
                <button
                  onClick={() => setActiveTab('anomalies')}
                  className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'anomalies'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-slate-400 hover:text-slate-300'
                  }`}
                >
                  Anomalies ({anomalies.length})
                </button>
              </div>
            </div>

            {/* Tab content */}
            {activeTab === 'entries' && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                <div className="p-3 border-b border-slate-700 flex items-center justify-between">
                  <span className="text-sm text-slate-400">
                    {anomalousOnly ? 'Showing anomalous entries only' : 'Showing all entries'}
                  </span>
                  <button
                    onClick={handleToggleAnomalous}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${
                      anomalousOnly
                        ? 'bg-red-900/50 text-red-300 hover:bg-red-900/70'
                        : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                    }`}
                  >
                    {anomalousOnly ? 'Show All' : 'Anomalous Only'}
                  </button>
                </div>
                <LogTable
                  entries={entries}
                  page={page}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              </div>
            )}

            {activeTab === 'anomalies' && (
              <div className="space-y-4">
                {anomalies.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    {summary?.analysis_status === 'completed'
                      ? 'No anomalies detected in this file'
                      : 'Run AI analysis to detect anomalies'}
                  </div>
                ) : (
                  anomalies.map((anomaly) => (
                    <AnomalyCard key={anomaly.id} anomaly={anomaly} />
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
