"use client";

import React from 'react';
import { Play, Download, MoreVertical, FileVideo, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

interface Job {
  job_id: string;
  status: string;
  message: string;
  video_url: string | null;
  filename: string;
  created_at: number;
}

const JobList = ({ jobs, onRefresh }: { jobs: Job[], onRefresh: () => void }) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit"><CheckCircle2 size={12} /> 제작 완료</span>;
      case 'processing':
        return <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit"><Loader2 size={12} className="animate-spin" /> 제작 중...</span>;
      case 'pending':
        return <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit">대기 중</span>;
      case 'failed':
        return <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit"><AlertCircle size={12} /> 생성 실패</span>;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
      <div className="p-6 border-b border-slate-50 flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">제작 기록</h2>
        <button onClick={onRefresh} className="text-blue-600 text-sm font-medium hover:underline">새로고침</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-slate-50/50 text-slate-500 text-xs font-bold uppercase tracking-wider">
              <th className="px-6 py-4">강의명</th>
              <th className="px-6 py-4">제작 시간</th>
              <th className="px-6 py-4">상태</th>
              <th className="px-6 py-4">진행 상황</th>
              <th className="px-6 py-4 text-right">관리</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-slate-400">제작 기록이 없습니다.</td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr key={job.job_id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                        <FileVideo size={18} />
                      </div>
                      <span className="font-semibold text-slate-700 truncate max-w-[200px]">{job.filename}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {new Date(job.created_at * 1000).toLocaleString('ko-KR')}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(job.status)}
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-xs text-slate-500 mb-1.5 truncate max-w-[150px]">{job.message}</p>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-500 ${job.status === 'failed' ? 'bg-red-400' : 'bg-primary'}`}
                        style={{ width: `${job.status === 'completed' ? 100 : (job.status === 'processing' ? 60 : 10)}%` }}
                      />
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {job.status === 'completed' && job.video_url && (
                        <>
                          <a 
                            href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job.video_url}`} 
                            target="_blank" 
                            className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="미리보기"
                          >
                            <Play size={18} />
                          </a>
                          <a 
                            href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job.video_url}`} 
                            download 
                            className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                            title="다운로드"
                          >
                            <Download size={18} />
                          </a>
                        </>
                      )}
                      <button className="p-2 text-slate-400 hover:text-slate-600 rounded-lg">
                        <MoreVertical size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default JobList;
