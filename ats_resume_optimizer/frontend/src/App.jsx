import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import {
  Upload,
  FileText,
  Zap,
  Download,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import ScoreGauge from "./components/ScoreGauge";
import KeywordBadges from "./components/KeywordBadges";

const API = "";

function DropZone({ onFile, file }) {
  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) onFile(accepted[0]);
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"], "text/plain": [".txt"] },
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
        isDragActive ? "border-violet-500 bg-violet-900/20" : "border-gray-700 hover:border-violet-500 hover:bg-gray-800/50"
      }`}
    >
      <input {...getInputProps()} />
      <Upload className="mx-auto mb-2 text-violet-400" size={28} />
      {file ? (
        <div className="flex items-center justify-center gap-2 text-sm text-green-400">
          <CheckCircle2 size={16} />
          <span>{file.name}</span>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-300">Drop your resume here</p>
          <p className="text-xs text-gray-500 mt-1">PDF, DOCX, or TXT</p>
        </div>
      )}
    </div>
  );
}

function ProgressBar({ value, colorClass }) {
  return (
    <div className="w-full bg-gray-800 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all duration-700 ${colorClass}`}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

export default function App() {
  const [file, setFile] = useState(null);
  const [jd, setJd] = useState("");
  const [analyzeResult, setAnalyzeResult] = useState(null);
  const [optimizeResult, setOptimizeResult] = useState(null);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [loadingOptimize, setLoadingOptimize] = useState(false);
  const [error, setError] = useState("");
  const [showOriginal, setShowOriginal] = useState(false);
  const [showOptimized, setShowOptimized] = useState(true);

  const reset = () => {
    setFile(null);
    setJd("");
    setAnalyzeResult(null);
    setOptimizeResult(null);
    setError("");
  };

  const handleAnalyze = async () => {
    if (!file || !jd.trim()) {
      setError("Upload a resume and paste a job description first.");
      return;
    }
    setError("");
    setLoadingAnalyze(true);
    try {
      const fd = new FormData();
      fd.append("resume", file);
      fd.append("job_description", jd);
      const { data } = await axios.post(`${API}/api/analyze`, fd);
      setAnalyzeResult(data);
      setOptimizeResult(null);
    } catch (e) {
      setError(e.response?.data?.detail || "Analysis failed. Is the backend running?");
    } finally {
      setLoadingAnalyze(false);
    }
  };

  const handleOptimize = async () => {
    if (!analyzeResult) return;
    setError("");
    setLoadingOptimize(true);
    try {
      const fd = new FormData();
      fd.append("resume_text_input", analyzeResult.resume_text);
      fd.append("job_description", jd);
      const { data } = await axios.post(`${API}/api/optimize`, fd);
      setOptimizeResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || "Optimization failed.");
    } finally {
      setLoadingOptimize(false);
    }
  };

  const downloadText = (text, filename) => {
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const scoreColor = (s) => {
    if (s >= 75) return "bg-green-500";
    if (s >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="text-violet-400" size={22} />
            <span className="font-bold text-lg tracking-tight">ATS Resume Optimizer</span>
          </div>
          {(analyzeResult || optimizeResult) && (
            <button
              onClick={reset}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
            >
              <RotateCcw size={14} />
              Start Over
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {/* Input Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800 space-y-4">
            <h2 className="font-semibold text-gray-200 flex items-center gap-2">
              <FileText size={18} className="text-violet-400" />
              Your Resume
            </h2>
            <DropZone onFile={setFile} file={file} />
          </div>

          <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800 space-y-4">
            <h2 className="font-semibold text-gray-200 flex items-center gap-2">
              <FileText size={18} className="text-violet-400" />
              Job Description
            </h2>
            <textarea
              className="w-full h-40 bg-gray-800 border border-gray-700 rounded-xl p-3 text-sm text-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500 placeholder-gray-600"
              placeholder="Paste the full job description here..."
              value={jd}
              onChange={(e) => setJd(e.target.value)}
            />
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 bg-red-900/30 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleAnalyze}
            disabled={loadingAnalyze || !file || !jd.trim()}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-2.5 rounded-xl transition-all text-sm"
          >
            {loadingAnalyze ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
            {loadingAnalyze ? "Analyzing..." : "Analyze Resume"}
          </button>

          {analyzeResult && (
            <button
              onClick={handleOptimize}
              disabled={loadingOptimize}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-2.5 rounded-xl transition-all text-sm"
            >
              {loadingOptimize ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
              {loadingOptimize ? "Optimizing with AI..." : "✨ Optimize with AI"}
            </button>
          )}
        </div>

        {/* Analysis Results */}
        {analyzeResult && (
          <div className="space-y-6">
            {/* Score Cards */}
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
              <h2 className="font-bold text-xl mb-6 text-gray-100">ATS Analysis Report</h2>

              <div className="flex flex-wrap items-center justify-around gap-6 mb-6">
                <ScoreGauge score={analyzeResult.overall_score} label="Overall ATS Score" size={120} />
                <ScoreGauge score={analyzeResult.keyword_score} label="Keyword Match" size={100} />
                <ScoreGauge score={analyzeResult.semantic_score} label="Semantic Similarity" size={100} />
              </div>

              {/* Verdict */}
              <div className="text-center text-lg font-semibold mb-4 py-2 px-4 rounded-xl bg-gray-800 inline-block w-full">
                {analyzeResult.verdict}
              </div>

              {/* Progress Bars */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Keyword Match Score</span>
                    <span>{analyzeResult.keyword_score}%</span>
                  </div>
                  <ProgressBar value={analyzeResult.keyword_score} colorClass={scoreColor(analyzeResult.keyword_score)} />
                </div>
                <div>
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Semantic Similarity Score</span>
                    <span>{analyzeResult.semantic_score}%</span>
                  </div>
                  <ProgressBar value={analyzeResult.semantic_score} colorClass={scoreColor(analyzeResult.semantic_score)} />
                </div>
                <div>
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>JD Keywords Identified</span>
                    <span>{analyzeResult.jd_keyword_count}</span>
                  </div>
                  <ProgressBar
                    value={(analyzeResult.resume_keyword_count / Math.max(analyzeResult.jd_keyword_count, 1)) * 100}
                    colorClass="bg-violet-500"
                  />
                </div>
              </div>
            </div>

            {/* Keywords */}
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
              <h2 className="font-bold text-lg mb-4">Keyword Analysis</h2>
              <KeywordBadges
                matched={analyzeResult.matched_keywords}
                missing={analyzeResult.missing_keywords}
              />
            </div>

            {/* Original Resume Toggle */}
            <div className="bg-gray-900 rounded-2xl border border-gray-800">
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-gray-300 hover:text-white"
              >
                <span>📄 Original Resume Text</span>
                {showOriginal ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              {showOriginal && (
                <div className="px-5 pb-5">
                  <pre className="bg-gray-800 rounded-xl p-4 text-xs text-gray-300 whitespace-pre-wrap max-h-80 overflow-y-auto scrollbar-thin">
                    {analyzeResult.resume_text}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Optimized Resume */}
        {optimizeResult && (
          <div className="space-y-6">
            {/* Score Comparison */}
            <div className="bg-gray-900 rounded-2xl p-6 border border-emerald-800/50">
              <h2 className="font-bold text-xl mb-2 text-emerald-400">✨ AI-Optimized Resume</h2>
              <p className="text-xs text-gray-400 mb-6">
                New score after optimization (content wrapped in [[ ]] was added/changed by AI — review before using)
              </p>

              <div className="flex flex-wrap items-center justify-around gap-6 mb-4">
                <ScoreGauge score={optimizeResult.overall_score} label="New ATS Score" size={120} />
                <ScoreGauge score={optimizeResult.keyword_score} label="Keyword Match" size={100} />
                <ScoreGauge score={optimizeResult.semantic_score} label="Semantic Similarity" size={100} />
              </div>

              <div className="text-center text-lg font-semibold py-2 px-4 rounded-xl bg-gray-800 w-full">
                {optimizeResult.verdict}
              </div>
            </div>

            {/* Optimized Text */}
            <div className="bg-gray-900 rounded-2xl border border-gray-800">
              <div className="flex items-center justify-between px-5 py-4">
                <button
                  onClick={() => setShowOptimized(!showOptimized)}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-300 hover:text-white"
                >
                  <span>📝 Optimized Resume</span>
                  {showOptimized ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                <button
                  onClick={() => downloadText(optimizeResult.optimized_resume, "optimized_resume.txt")}
                  className="flex items-center gap-1.5 text-xs bg-emerald-700 hover:bg-emerald-600 text-white px-3 py-1.5 rounded-lg transition-colors"
                >
                  <Download size={13} />
                  Download
                </button>
              </div>
              {showOptimized && (
                <div className="px-5 pb-5">
                  <pre className="bg-gray-800 rounded-xl p-4 text-xs text-gray-300 whitespace-pre-wrap max-h-[500px] overflow-y-auto scrollbar-thin">
                    {optimizeResult.optimized_resume}
                  </pre>
                </div>
              )}
            </div>

            {/* Updated Keywords */}
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
              <h2 className="font-bold text-lg mb-4">Updated Keyword Analysis</h2>
              <KeywordBadges
                matched={optimizeResult.matched_keywords}
                missing={optimizeResult.missing_keywords}
              />
            </div>
          </div>
        )}
      </main>

      <footer className="text-center text-xs text-gray-600 py-8">
        ATS Resume Optimizer · Personal Use Only
      </footer>
    </div>
  );
}
