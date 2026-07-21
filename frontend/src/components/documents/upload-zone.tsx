"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Hash } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Document } from "@/types/case";

interface UploadZoneProps {
  caseId: string;
  onUploadSuccess?: (doc: Document) => void;
}

export function UploadZone({ caseId, onUploadSuccess }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [computedHash, setComputedHash] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isCalculatingHash, setIsCalculatingHash] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculateSha256 = async (selectedFile: File) => {
    setIsCalculatingHash(true);
    try {
      const buffer = await selectedFile.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
      setComputedHash(hashHex);
    } catch {
      setComputedHash(null);
    } finally {
      setIsCalculatingHash(false);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    setError(null);
    setFile(selectedFile);
    calculateSha256(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const doc = await apiClient.upload<Document>(`/documents/upload/${caseId}`, formData);
      setFile(null);
      setComputedHash(null);
      if (onUploadSuccess) onUploadSuccess(doc);
    } catch (err: any) {
      setError(err.message || "Failed to upload document file.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all cursor-pointer ${
          isDragging
            ? "border-indigo-500 bg-indigo-500/10"
            : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
        }`}
      >
        <input
          type="file"
          accept=".pdf,.docx,.txt,.png,.jpg,.webp"
          className="absolute inset-0 opacity-0 cursor-pointer"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />

        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-3">
          <Upload className="h-6 w-6" />
        </div>

        <p className="text-sm font-medium text-white mb-1">
          Drag & drop your legal document here, or <span className="text-indigo-400">browse</span>
        </p>
        <p className="text-xs text-gray-500">
          Supports PDF, DOCX, TXT, PNG, JPG (Max 50MB) — Local File Storage
        </p>
      </div>

      {/* Selected File & SHA-256 Hash Preview */}
      {file && (
        <div className="glass rounded-xl p-4 border border-white/10 space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-indigo-400" />
              <div>
                <p className="text-sm font-medium text-white truncate max-w-xs">{file.name}</p>
                <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={isUploading || isCalculatingHash}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:bg-indigo-500 disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Uploading...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" /> Confirm Upload
                </>
              )}
            </button>
          </div>

          {/* SHA-256 Hash Display */}
          <div className="flex items-center gap-2 rounded-lg bg-black/40 p-2.5 text-xs font-mono text-gray-300 border border-white/5">
            <Hash className="h-4 w-4 text-cyan-400 flex-shrink-0" />
            <span className="text-gray-500">SHA-256:</span>
            {isCalculatingHash ? (
              <span className="text-gray-400 italic">Calculating hash...</span>
            ) : (
              <span className="text-cyan-300 truncate">{computedHash}</span>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
