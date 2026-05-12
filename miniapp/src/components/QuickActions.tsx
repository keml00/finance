"use client";

const actions = [
  { icon: "💰", label: "Доход", color: "from-emerald-500/20 to-emerald-600/10" },
  { icon: "💸", label: "Расход", color: "from-red-500/20 to-red-600/10" },
  { icon: "🔄", label: "Перевод", color: "from-blue-500/20 to-blue-600/10" },
  { icon: "🧾", label: "Чек", color: "from-purple-500/20 to-purple-600/10" },
];

export function QuickActions() {
  return (
    <div className="grid grid-cols-4 gap-2">
      {actions.map((action) => (
        <button
          key={action.label}
          className={`flex flex-col items-center gap-1.5 p-3 rounded-xl bg-gradient-to-b ${action.color} border border-white/5 hover:border-white/20 transition-all active:scale-95`}
        >
          <span className="text-xl">{action.icon}</span>
          <span className="text-[10px] text-gray-400 font-medium">{action.label}</span>
        </button>
      ))}
    </div>
  );
}
