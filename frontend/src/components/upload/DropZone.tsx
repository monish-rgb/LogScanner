import { useState, useRef, type DragEvent } from 'react';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

const ACCEPTED_EXTENSIONS = ['.log', '.txt', '.csv'];

export default function DropZone({ onFileSelect, disabled }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    const file = e.dataTransfer.files[0];
    if (file && isValidFile(file)) {
      onFileSelect(file);
    }
  };

  const handleClick = () => {
    if (!disabled) fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && isValidFile(file)) {
      onFileSelect(file);
    }
    if (e.target) e.target.value = '';
  };

  const isValidFile = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    return ACCEPTED_EXTENSIONS.includes(ext);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
        ${disabled ? 'opacity-50 cursor-not-allowed border-slate-700' : ''}
        ${isDragging
          ? 'border-blue-400 bg-blue-900/20'
          : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/50'
        }
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".log,.txt,.csv"
        onChange={handleFileChange}
        className="hidden"
      />
      <div className="text-5xl mb-4">
        {isDragging ? '\u{1F4E5}' : '\u{1F4C1}'}
      </div>
      <p className="text-lg text-slate-300 mb-2">
        {isDragging ? 'Drop your log file here' : 'Drag & drop your log file here'}
      </p>
      <p className="text-sm text-slate-500">
        or click to browse. Supports .log, .txt, .csv files
      </p>
      <p className="text-xs text-slate-600 mt-2">
        ZScaler Web Proxy Log format supported
      </p>
    </div>
  );
}
