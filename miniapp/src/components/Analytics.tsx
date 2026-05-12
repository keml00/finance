"use client";

import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

const monthlyData = [
  { month: "Янв", income: 150000, expense: 82000 },
  { month: "Фев", income: 160000, expense: 75000 },
  { month: "Мар", income: 155000, expense: 90000 },
  { month: "Апр", income: 185000, expense: 68000 },
  { month: "Май", income: 185000, expense: 67150 },
];

const dailyData = Array.from({ length: 14 }, (_, i) => ({
  day: `${i + 1}`,
  amount: Math.floor(Math.random() * 5000) + 1000,
}));

export function Analytics() {
  return (
    <div className="space-y-4">
      {/* Monthly Chart */}
      <motion.div
        className="glass-card p-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h3 className="text-sm font-semibold text-white mb-1">Доходы vs Расходы</h3>
        <p className="text-xs text-gray-500 mb-3">Последние 5 месяцев</p>

        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={monthlyData}>
              <defs>
                <linearGradient id="gradIncome" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10B981" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradExpense" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#EF4444" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#EF4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="month"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#6B7280", fontSize: 10 }}
              />
              <YAxis hide />
              <Area
                type="monotone"
                dataKey="income"
                stroke="#10B981"
                strokeWidth={2}
                fill="url(#gradIncome)"
              />
              <Area
                type="monotone"
                dataKey="expense"
                stroke="#EF4444"
                strokeWidth={2}
                fill="url(#gradExpense)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Daily Spending */}
      <motion.div
        className="glass-card p-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h3 className="text-sm font-semibold text-white mb-1">Расходы по дням</h3>
        <p className="text-xs text-gray-500 mb-3">Текущий месяц</p>

        <div className="h-28">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dailyData}>
              <XAxis
                dataKey="day"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#6B7280", fontSize: 9 }}
              />
              <Bar dataKey="amount" fill="#3B82F6" radius={[3, 3, 0, 0]} opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* KPIs */}
      <motion.div
        className="grid grid-cols-2 gap-3"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="glass-card p-3">
          <p className="text-[10px] text-gray-500 uppercase">Средний расход/день</p>
          <p className="text-lg font-bold text-white">4,797 ₽</p>
          <p className="text-[10px] text-red-400">+8% к прошлому мес.</p>
        </div>
        <div className="glass-card p-3">
          <p className="text-[10px] text-gray-500 uppercase">Накопления</p>
          <p className="text-lg font-bold text-emerald-400">117,850 ₽</p>
          <p className="text-[10px] text-emerald-400">64% от дохода</p>
        </div>
        <div className="glass-card p-3">
          <p className="text-[10px] text-gray-500 uppercase">Топ категория</p>
          <p className="text-lg font-bold text-white">🛒 Продукты</p>
          <p className="text-[10px] text-gray-400">28,000 ₽ (42%)</p>
        </div>
        <div className="glass-card p-3">
          <p className="text-[10px] text-gray-500 uppercase">Операций</p>
          <p className="text-lg font-bold text-white">47</p>
          <p className="text-[10px] text-gray-400">за этот месяц</p>
        </div>
      </motion.div>
    </div>
  );
}
