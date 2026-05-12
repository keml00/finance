"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const data = [
  { name: "Продукты", value: 28000, color: "#10B981" },
  { name: "Транспорт", value: 12000, color: "#F59E0B" },
  { name: "Кафе", value: 15000, color: "#EF4444" },
  { name: "Подписки", value: 5000, color: "#8B5CF6" },
  { name: "Другое", value: 7150, color: "#6B7280" },
];

export function SpendingChart() {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold text-white mb-3">Расходы по категориям</h3>

      <div className="flex items-center gap-4">
        <div className="w-24 h-24">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={28}
                outerRadius={42}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="flex-1 space-y-1.5">
          {data.map((item) => (
            <div key={item.name} className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-gray-400 flex-1">{item.name}</span>
              <span className="text-xs text-white font-medium">
                {Math.round((item.value / total) * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
