"use client";

import React from 'react';
import { LayoutDashboard, BookOpen, Settings, HelpCircle, LogOut, Video } from 'lucide-react';
import Link from 'next/link';

const Sidebar = () => {
  const menuItems = [
    { icon: LayoutDashboard, label: '대시보드', href: '/', active: true },
    { icon: BookOpen, label: '강의 관리', href: '#' },
    { icon: Video, label: '제작 기록', href: '#' },
    { icon: Settings, label: '설정', href: '#' },
    { icon: HelpCircle, label: '고객 센터', href: '#' },
  ];

  return (
    <div className="w-64 sidebar-gradient h-screen fixed left-0 top-0 text-white p-6 flex flex-col">
      <div className="flex items-center gap-3 mb-12">
        <div className="bg-primary p-2 rounded-xl">
          <BookOpen size={24} />
        </div>
        <h1 className="text-xl font-bold tracking-tight">AI LMS Admin</h1>
      </div>

      <nav className="flex-1">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.label}>
              <Link
                href={item.href}
                className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                  item.active 
                    ? 'bg-primary text-white shadow-lg shadow-primary/20' 
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <item.icon size={20} />
                <span className="font-medium">{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="mt-auto border-t border-white/10 pt-6">
        <button className="flex items-center gap-3 text-slate-400 hover:text-red-400 transition-colors w-full p-3">
          <LogOut size={20} />
          <span className="font-medium">로그아웃</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
