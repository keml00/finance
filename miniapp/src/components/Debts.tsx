"use client";

import { motion } from "framer-motion";

const debts = [
  {
    id: 1,
    title: "Кредит Сбер",
    type: "credit",
    total: 500000,
    remaining: 320000,
    monthly: 15000,
    rate: 12.9,
    dueDate: "2027-06-15",
    icon: "🏦",
  },
  {
    id: 2,
    title: "Долг Петя",
    type: "i_owe",
    total: 30000,
    remaining: 30000,
    monthly: null,
    rate: 0,
    dueDate: null,
    icon: "👤",
  },
  {
    id: 3,
    title: "Рассрочка iPhone",
    type: "installment",
    total: 89990,
    remaining: 44995,
    monthly: 7499,
    rate: 0,
    dueDate: "2026-12-01",
    icon: "📱",
  },
];

export function Debts() {
  const totalDebt = debts.reduce((sum, d) => sum + d.remaining, 0);
  const monthlyPayments = debts.reduce((sum, d) => sum + (d.monthly || 0), 0);

  return (
    <div className="space-y-4">
      {/* Summary */}
      <motion.div
        className="glass-card p-4 neon-purple"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Общий долг</p>
        <h2 className="text-2xl font-bold text-white mb-3">
          {totalDebt.toLocaleString("ru-RU")} ₽
        </h2>
        <div className="flex gap-3">
          <div className="flex-1 bg-white/5 rounded-lg p-2">
            <p className="text-[10px] text-gray-500">Ежемесячно</p>
            <p className="text-sm font-semibold text-orange-400">
              {monthlyPayments.toLocaleString("ru-RU")} ₽
            </p>
          </div>
          <div className="flex-1 bg-white/5 rounded-lg p-2">
            <p className="text-[10px] text-gray-500">Активных</p>
            <p className="text-sm font-semibold text-white">{debts.length}</p>
          </div>
        </div>
      </motion.div>

      {/* Debt list */}
      <div className="space-y-3">
        {debts.map((debt, i) => {
          const progress = ((debt.total - debt.remaining) / debt.total) * 100;
          return (
            <motion.div
              key={debt.id}
              className="glass-card p-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-lg">
                  {debt.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-white">{debt.title}</h4>
                    {debt.rate > 0 && (
                      <span className="text-[10px] text-orange-400 bg-orange-500/10 px-1.5 py-0.5 rounded">
                        {debt.rate}%
                      </span>
                    )}
                  </div>

                  <div className="mt-2">
                    <div className="flex justify-between text-[10px] mb-1">
                      <span className="text-gray-500">
                        Выплачено: {(debt.total - debt.remaining).toLocaleString("ru-RU")} ₽
                      </span>
                      <span className="text-gray-400">{progress.toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-between mt-2">
                    <span className="text-xs text-gray-500">
                      Остаток: {debt.remaining.toLocaleString("ru-RU")} ₽
                    </span>
                    {debt.monthly && (
                      <span className="text-xs text-blue-400">
                        {debt.monthly.toLocaleString("ru-RU")} ₽/мес
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Add button */}
      <button className="w-full glass-card p-3 text-center text-sm text-blue-400 font-medium hover:bg-white/10 transition-all">
        + Добавить долг
      </button>
    </div>
  );
}
