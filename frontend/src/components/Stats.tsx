"use client";

import React from 'react';
import { Video, CheckCircle, Clock, BarChart3 } from 'lucide-react';

interface StatsProps {
  jobs: any[];
}

const Stats = ({ jobs }: StatsProps) => {
  const total = jobs.length;
  const completed = jobs.filter(j => j.status === 'completed').length;
  const processing = jobs.filter(j => j.status === 'processing' || j.status === 'pending').length;

  const cards = [
    { label: '전체 강의 영상', value: total, icon: BarChart3, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: '제작 완료', value: completed, icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
    { label: '제작 중', value: processing, icon: Clock, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: '잔여 작업', value: 0, icon: Video, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card) => (
        <div key={card.label} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-5 transition-transform hover:scale-[1.02]">
          <div className={`${card.bg} ${card.color} p-4 rounded-xl`}>
            <card.icon size={28} />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">{card.label}</p>
            <h3 className="text-2xl font-bold text-slate-900">{card.value}</h3>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Stats;
