export default function HistoryPage() {
    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-[#38ff14] neon-glow tracking-widest uppercase">Exorcism History</h1>
            <div className="p-8 border border-[#2a3a27] bg-black/40 rounded-xl backdrop-blur-sm text-center">
                <span className="material-symbols-outlined text-6xl text-[#38ff14]/20 mb-4 block">history</span>
                <p className="text-[#38ff14]/60 font-mono">No previous exorcism records found in the database.</p>
            </div>
        </div>
    );
}
