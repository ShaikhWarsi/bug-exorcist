"use client";

import { useEffect, useState } from "react";

export default function SettingsPage() {
  const [mounted, setMounted] = useState(false);
  const [openaiKey, setOpenaiKey] = useState("");
  const [githubRepo, setGithubRepo] = useState("");

  useEffect(() => {
    setMounted(true);
    setOpenaiKey(localStorage.getItem("openai_api_key") || "");
    setGithubRepo(localStorage.getItem("github_repo_url") || "");
  }, []);

  const saveSettings = () => {
    if (!openaiKey.trim() || !githubRepo.trim()) {
      alert("Please fill in both the OpenAI API Key and GitHub Repository URL.");
      return;
    }
    localStorage.setItem("openai_api_key", openaiKey);
    localStorage.setItem("github_repo_url", githubRepo);
    alert("Settings saved successfully!");
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[#38ff14] neon-glow tracking-widest uppercase mb-2">Configuration</h1>
        <p className="text-[#38ff14]/60 text-sm font-mono italic">Adjust system parameters for optimal bug exorcism.</p>
      </div>

      <div className="space-y-6">
        {/* OpenAI API Key */}
        <div className="p-6 rounded-xl border border-[#2a3a27] bg-black/40 backdrop-blur-sm space-y-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-[#38ff14]">key</span>
            <label className="text-[#38ff14] text-xs font-bold uppercase tracking-widest">OpenAI API Key</label>
          </div>
          <input
            type="password"
            value={openaiKey}
            onChange={(e) => setOpenaiKey(e.target.value)}
            placeholder="sk-..."
            className="w-full bg-black/60 border border-[#2a3a27] rounded-lg px-4 py-3 text-[#38ff14] font-mono text-sm focus:outline-none focus:border-[#38ff14]/50 transition-colors placeholder:text-[#38ff14]/20"
          />
          <p className="text-[#38ff14]/40 text-[10px] uppercase leading-relaxed">
            Required for summoning GPT-4o to write patches and analyze logs.
          </p>
        </div>

        {/* GitHub Repository */}
        <div className="p-6 rounded-xl border border-[#2a3a27] bg-black/40 backdrop-blur-sm space-y-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-[#38ff14]">source</span>
            <label className="text-[#38ff14] text-xs font-bold uppercase tracking-widest">GitHub Repository URL</label>
          </div>
          <input
            type="text"
            value={githubRepo}
            onChange={(e) => setGithubRepo(e.target.value)}
            placeholder="https://github.com/user/repo"
            className="w-full bg-black/60 border border-[#2a3a27] rounded-lg px-4 py-3 text-[#38ff14] font-mono text-sm focus:outline-none focus:border-[#38ff14]/50 transition-colors placeholder:text-[#38ff14]/20"
          />
          <p className="text-[#38ff14]/40 text-[10px] uppercase leading-relaxed">
            The target codebase where bugs will be hunted and eliminated.
          </p>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4">
          <button 
            onClick={saveSettings}
            className="flex items-center gap-2 px-8 py-3 bg-[#38ff14]/10 border border-[#38ff14]/50 text-[#38ff14] rounded-lg hover:bg-[#38ff14]/20 transition-all font-bold text-sm tracking-widest uppercase group"
          >
            <span className="material-symbols-outlined text-xl group-hover:neon-glow transition-all">save</span>
            Save Configuration
          </button>
        </div>
      </div>

      {/* Danger Zone / System Info */}
      <div className="pt-10 border-t border-[#2a3a27]/50">
        <div className="p-4 rounded-lg border border-red-900/30 bg-red-900/5">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-red-500 text-sm">warning</span>
            <p className="text-red-500 text-[10px] font-bold uppercase tracking-widest">Security Protocol</p>
          </div>
          <p className="text-red-500/60 text-[10px] leading-relaxed">
            API keys are stored locally in your browser's session. Never share your private keys or repository credentials.
          </p>
        </div>
      </div>
    </div>
  );
}
