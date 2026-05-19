"use client";

import { useState } from "react";
import { Dashboard } from "@/components/Dashboard";
import { Analytics } from "@/components/Analytics";
import { Debts } from "@/components/Debts";
import { Goals } from "@/components/Goals";
import { Navigation } from "@/components/Navigation";

type Tab = "dashboard" | "analytics" | "debts" | "goals";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");

  return (
    <main className="min-h-screen pb-20">
      {/* Header */}
      <header className="sticky top-0 z-50 px-4 pt-4 pb-3 backdrop-blur-xl bg-dark-950/80 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold gradient-text">FinAI</h1>
            <p className="text-xs text-gray-500">Personal Finance</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold">
            F
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="px-4 pt-4 animate-fade-in">
        {activeTab === "dashboard" && <Dashboard />}
        {activeTab === "analytics" && <Analytics />}
        {activeTab === "debts" && <Debts />}
        {activeTab === "goals" && <Goals />}
      </div>

      {/* Bottom Navigation */}
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
    </main>
  );
}
