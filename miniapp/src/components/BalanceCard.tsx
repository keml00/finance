"use client";

export function BalanceCard() {
  return (
    <div className="glass-card p-5 neon-blue relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/20 rounded-full blur-3xl" />
      <div className="absolute -bottom-10 -left-10 w-24 h-24 bg-purple-500/20 rounded-full blur-3xl" />

      <div className="relative">
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Общий баланс</p>
        <h2 className="text-3xl font-bold text-white mb-4">
          ₽ 247,850
          <span className="text-sm text-emerald-400 ml-2 font-normal">+12.4%</span>
        </h2>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">
            <p className="text-[10px] text-emerald-400 uppercase tracking-wider">Доходы</p>
            <p className="text-lg font-semibold text-emerald-400">+185,000</p>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
            <p className="text-[10px] text-red-400 uppercase tracking-wider">Расходы</p>
            <p className="text-lg font-semibold text-red-400">-67,150</p>
          </div>
        </div>
      </div>
    </div>
  );
}
