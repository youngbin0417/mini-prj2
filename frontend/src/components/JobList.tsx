"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Play, Download, MoreVertical, FileVideo, Loader2, AlertCircle, CheckCircle2, Trash2 } from 'lucide-react';
import api from '@/lib/api';

interface Job {
  job_id: string;
  status: string;
  message: string;
  video_url: string | null;
  filename: string;
  created_at: number;
  summary?: string | null;
  summary_img?: string | null;
}

const JobList = ({ jobs, onRefresh }: { jobs: Job[], onRefresh: () => void }) => {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDelete = async (jobId: string) => {
    const inputPasscode = window.prompt('삭제를 위해 관리자 암호를 입력하세요:');
    if (inputPasscode !== 'aivle202609') {
      alert('암호가 올바르지 않습니다.');
      return;
    }

    if (window.confirm('정말 이 강의 기록과 파일을 삭제하시겠습니까?')) {
      try {
        await api.delete(`/api/jobs/${jobId}`);
        setOpenDropdown(null);
        onRefresh();
      } catch (error) {
        console.error('Failed to delete job:', error);
        alert('삭제에 실패했습니다.');
      }
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="p-1.5 bg-green-100 text-green-700 rounded-full flex items-center justify-center w-fit" title="완료"><CheckCircle2 size={14} /></span>;
      case 'processing':
        return <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit"><Loader2 size={12} className="animate-spin" /> 제작 중...</span>;
      case 'pending':
        return <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit">대기 중</span>;
      case 'failed':
        return <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit"><AlertCircle size={12} /> 실패</span>;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden h-full flex flex-col">
      <div className="p-6 border-b border-slate-50 flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">제작 기록</h2>
        <button onClick={onRefresh} className="text-blue-600 text-sm font-medium hover:underline">새로고침</button>
      </div>
      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-slate-50/50 text-slate-500 text-xs font-bold uppercase tracking-wider">
              <th className="px-4 py-4">강의명</th>
              <th className="px-4 py-4">시간</th>
              <th className="px-4 py-4">상태</th>
              <th className="px-4 py-4">진행</th>
              <th className="px-4 py-4 text-right">관리</th>
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
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                        <FileVideo size={18} />
                      </div>
                      <span className="font-semibold text-slate-700 truncate max-w-[200px]">{job.filename}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(job.created_at * 1000).toLocaleString('ko-KR')}
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(job.status)}
                  </td>
                  <td className="px-4 py-3">
                    {job.status !== 'completed' && (
                      <>
                        <p className="text-xs text-slate-500 mb-1.5 truncate max-w-[150px]">{job.message}</p>
                        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-500 ${job.status === 'failed' ? 'bg-red-400' : 'bg-primary'}`}
                            style={{ width: `${job.status === 'processing' ? 60 : 10}%` }}
                          />
                        </div>
                      </>
                    )}
                  </td>

                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {job.status === 'completed' && (
                        <>
                          {(job.summary_img || job.summary) && (
                            <button
                              onClick={() => setSelectedSummary(job.summary_img || job.summary || null)}
                              className="p-2 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                              title="핵심 요약 보기"
                            >
                              <CheckCircle2 size={18} />
                            </button>
                          )}
                          {job.video_url && (
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
                        </>
                      )}
                      <div className="relative" ref={openDropdown === job.job_id ? dropdownRef : null}>
                        <button
                          onClick={() => setOpenDropdown(openDropdown === job.job_id ? null : job.job_id)}
                          className={`p-2 rounded-lg transition-colors ${openDropdown === job.job_id ? 'bg-slate-100 text-slate-900' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}
                        >
                          <MoreVertical size={18} />
                        </button>

                        {openDropdown === job.job_id && (
                          <div className="absolute right-0 mt-2 w-36 bg-white rounded-xl shadow-lg border border-slate-100 py-1 z-10">
                            <button
                              onClick={() => handleDelete(job.job_id)}
                              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors"
                            >
                              <Trash2 size={14} />
                              삭제하기
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Summary Modal */}
      {selectedSummary && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="bg-amber-50 p-8 text-center">
              <div className="bg-amber-100 text-amber-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 size={32} />
              </div>
              <h3 className="text-xl font-bold text-slate-900">강의 핵심 요약</h3>
              <p className="text-amber-700/70 text-sm font-medium">AI가 분석한 강의의 가장 중요한 포인트입니다.</p>
            </div>
            <div className="p-8">
              <div className="space-y-4">
                {selectedSummary.split('\n').filter(line => line.trim()).map((line, i) => (
                  <div key={i} className="flex gap-4 group">
                    <span className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center font-bold text-sm group-hover:bg-primary group-hover:text-white transition-colors">
                      {i + 1}
                    </span>
                    <p className="text-slate-600 leading-relaxed font-medium pt-1">{line.replace(/^[-\d]\s*/, '')}</p>
                  </div>
                ))}
              </div>
              <button
                onClick={() => setSelectedSummary(null)}
                className="w-full mt-10 bg-slate-900 text-white font-bold py-4 rounded-2xl hover:bg-slate-800 transition-all shadow-lg shadow-slate-200 active:scale-[0.98]"
              >
                확인했습니다
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobList;
