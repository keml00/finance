"use client";

import { motion } from "framer-motion";

type Tab = "dashboard" | "analytics" | "debts" | "goals";

interface NavigationProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const tabs = [
  { id: "dashboard" as Tab, label: "Главная", icon: "📊" },
  { id: "analytics" as Tab, label: "Аналитика", icon: "📈" },
  { id: "debts" as Tab, label: "Долги", icon: "🏦" },
  { id: "goals" as Tab, label: "Цели", icon: "🎯" },
];

export function Navigation({ activeTab, onTabChange }: NavigationProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 backdrop-blur-xl bg-dark-950/90 border-t border-white/5 px-2 pb-safe">
      <div className="flex items-center justify-around py-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className="relative flex flex-col items-center gap-0.5 px-4 py-2 rounded-xl transition-all"
          >
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 bg-white/5 rounded-xl"
                transition={{ type: "spring", duration: 0.5 }}
              />
            )}
            <span className="text-lg">{tab.icon}</span>
            <span
              className={`text-[10px] font-medium transition-colors ${
                activeTab === tab.id ? "text-blue-400" : "text-gray-500"
              }`}
            >
              {tab.label}
            </span>
          </button>
        ))}
      </div>
    </nav>
  );
}
