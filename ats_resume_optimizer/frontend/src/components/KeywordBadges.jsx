import React from "react";

export default function KeywordBadges({ matched = [], missing = [] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold text-green-400 mb-2">
          ✅ Matched Keywords ({matched.length})
        </h3>
        <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto scrollbar-thin">
          {matched.map((kw) => (
            <span
              key={kw}
              className="px-2 py-0.5 rounded-full text-xs bg-green-900/50 text-green-300 border border-green-700"
            >
              {kw}
            </span>
          ))}
          {matched.length === 0 && (
            <span className="text-xs text-gray-500">None found</span>
          )}
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold text-red-400 mb-2">
          ❌ Missing Keywords ({missing.length})
        </h3>
        <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto scrollbar-thin">
          {missing.map((kw) => (
            <span
              key={kw}
              className="px-2 py-0.5 rounded-full text-xs bg-red-900/50 text-red-300 border border-red-700"
            >
              {kw}
            </span>
          ))}
          {missing.length === 0 && (
            <span className="text-xs text-gray-500">None – great match!</span>
          )}
        </div>
      </div>
    </div>
  );
}
