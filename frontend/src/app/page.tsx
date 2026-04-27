"use client";

import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from '@/components/Sidebar';
import Stats from '@/components/Stats';
import UploadForm from '@/components/UploadForm';
import JobList from '@/components/JobList';
import api from '@/lib/api';
import { Bell, Search, User } from 'lucide-react';

export default function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchJobs = useCallback(async () => {
    try {
      const response = await api.get('/api/jobs');
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    // 5초마다 자동 새로고침 (진행 중인 작업이 있을 경우)
    const interval = setInterval(() => {
      fetchJobs();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  const handleUploadSuccess = () => {
    fetchJobs();
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      
      <main className="flex-1 ml-64 p-10">
        {/* Header Bar */}
        <header className="flex items-center justify-between mb-10">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">강의 제작 대시보드</h1>
            <p className="text-slate-500 font-medium">환영합니다, 강사님! 오늘 제작할 강의는 무엇인가요?</p>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder="강의 검색..." 
                className="pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all w-64"
              />
            </div>
            <button className="bg-white p-2.5 rounded-xl border border-slate-200 text-slate-500 hover:text-primary transition-colors">
              <Bell size={20} />
            </button>
            <div className="flex items-center gap-3 bg-white p-1.5 pr-4 rounded-2xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition-all">
              <div className="bg-primary/10 text-primary p-2 rounded-xl">
                <User size={20} />
              </div>
              <span className="text-sm font-bold text-slate-700">관리자 계정</span>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <Stats jobs={jobs} />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <JobList jobs={jobs} onRefresh={fetchJobs} />
          </div>
          <div>
            <UploadForm onUploadSuccess={handleUploadSuccess} />
            
            {/* Promotion / Info Card */}
            <div className="bg-gradient-to-br from-indigo-600 to-violet-700 p-6 rounded-2xl text-white shadow-xl shadow-indigo-200">
              <h4 className="font-bold mb-2">프리미엄 팁 💡</h4>
              <p className="text-indigo-100 text-sm leading-relaxed mb-4">
                PPT의 '슬라이드 노트' 섹션에 스크립트를 작성해두면, AI가 더욱 정확하게 강의를 생성합니다.
              </p>
              <button className="text-xs font-bold bg-white/20 hover:bg-white/30 px-3 py-2 rounded-lg transition-all">
                자세히 알아보기
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
