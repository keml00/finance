"use client";

const transactions = [
  { icon: "🛒", name: "Продукты", amount: -3200, time: "Сегодня, 14:30" },
  { icon: "💰", name: "Зарплата", amount: 185000, time: "Вчера, 10:00" },
  { icon: "🚗", name: "Такси", amount: -450, time: "Вчера, 22:15" },
  { icon: "🍽️", name: "Ресторан", amount: -2800, time: "2 дня назад" },
  { icon: "📱", name: "YouTube Premium", amount: -399, time: "3 дня назад" },
];

export function RecentTransactions() {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">Последние операции</h3>
        <button className="text-xs text-blue-400 hover:text-blue-300">Все</button>
      </div>

      <div className="space-y-3">
        {transactions.map((tx, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center text-sm">
              {tx.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{tx.name}</p>
              <p className="text-[10px] text-gray-500">{tx.time}</p>
            </div>
            <p
              className={`text-sm font-semibold ${
                tx.amount > 0 ? "text-emerald-400" : "text-white"
              }`}
            >
              {tx.amount > 0 ? "+" : ""}
              {tx.amount.toLocaleString("ru-RU")} ₽
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
