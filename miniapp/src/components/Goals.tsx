"use client";

import { motion } from "framer-motion";

const goals = [
  {
    id: 1,
    title: "Подушка безопасности",
    icon: "🛡️",
    target: 500000,
    current: 247850,
    deadline: "2026-12-31",
    color: "from-emerald-500 to-emerald-600",
  },
  {
    id: 2,
    title: "Отпуск в Турцию",
    icon: "✈️",
    target: 200000,
    current: 85000,
    deadline: "2026-07-01",
    color: "from-blue-500 to-blue-600",
  },
  {
    id: 3,
    title: "Новый MacBook",
    icon: "💻",
    target: 250000,
    current: 50000,
    deadline: "2026-09-01",
    color: "from-purple-500 to-purple-600",
  },
];

export function Goals() {
  return (
    <div className="space-y-4">
      {/* Total Savings */}
      <motion.div
        className="glass-card p-4 neon-green"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Общие накопления</p>
        <h2 className="text-2xl font-bold text-emerald-400">
          {(247850 + 85000 + 50000).toLocaleString("ru-RU")} ₽
        </h2>
        <p className="text-xs text-gray-500 mt-1">3 активных цели</p>
      </motion.div>

      {/* Goals list */}
      <div className="space-y-3">
        {goals.map((goal, i) => {
          const progress = (goal.current / goal.target) * 100;
          const remaining = goal.target - goal.current;
          const daysLeft = goal.deadline
            ? Math.max(0, Math.ceil((new Date(goal.deadline).getTime() - Date.now()) / 86400000))
            : null;
          const monthlyNeeded = daysLeft && daysLeft > 0
            ? remaining / (daysLeft / 30)
            : null;

          return (
            <motion.div
              key={goal.id}
              className="glass-card p-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-lg">
                  {goal.icon}
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-white">{goal.title}</h4>
                  <p className="text-[10px] text-gray-500">
                    {daysLeft !== null ? `${daysLeft} дней осталось` : "Без дедлайна"}
                  </p>
                </div>
                <span className="text-sm font-bold text-white">{progress.toFixed(0)}%</span>
              </div>

              {/* Progress bar */}
              <div className="h-2 bg-white/5 rounded-full overflow-hidden mb-2">
                <motion.div
                  className={`h-full bg-gradient-to-r ${goal.color} rounded-full`}
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 1, delay: i * 0.2 }}
                />
              </div>

              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">
                  {goal.current.toLocaleString("ru-RU")} / {goal.target.toLocaleString("ru-RU")} ₽
                </span>
                {monthlyNeeded && (
                  <span className="text-[10px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">
                    ~{Math.ceil(monthlyNeeded).toLocaleString("ru-RU")} ₽/мес
                  </span>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Add button */}
      <button className="w-full glass-card p-3 text-center text-sm text-emerald-400 font-medium hover:bg-white/10 transition-all">
        + Новая цель
      </button>
    </div>
  );
}
