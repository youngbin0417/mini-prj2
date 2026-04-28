"use client";

import React, { useState } from 'react';
import { Upload, FileType, CheckCircle2, AlertCircle } from 'lucide-react';
import api from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';

const UploadForm = ({ onUploadSuccess }: { onUploadSuccess: () => void }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [passcode, setPasscode] = useState('');

  // 설정된 관리자 암호
  const ADMIN_PASSCODE = "aivle202609";

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    if (passcode !== ADMIN_PASSCODE) {
      setError('관리자 암호가 올바르지 않습니다.');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/api/jobs', formData);
      setFile(null);
      onUploadSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || '업로드 중 오류가 발생했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 mb-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">새 강의 제작</h2>
          <p className="text-slate-500 text-sm">PPTX 파일을 업로드하여 AI 강의 영상을 생성하세요.</p>
        </div>
        <div className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-semibold">
          Powered by AIVLE
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="relative group">
          <input
            type="file"
            accept=".pptx"
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          />
          <div className={`
            border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center transition-all
            ${file ? 'border-green-200 bg-green-50' : 'border-slate-200 group-hover:border-blue-400 group-hover:bg-blue-50/50'}
          `}>
            {file ? (
              <>
                <CheckCircle2 className="text-green-500 mb-4" size={48} />
                <p className="text-slate-700 font-medium">{file.name}</p>
                <p className="text-slate-400 text-xs mt-1">파일 선택 완료</p>
              </>
            ) : (
              <>
                <div className="bg-slate-100 p-4 rounded-full mb-4 group-hover:scale-110 transition-transform">
                  <Upload className="text-slate-400 group-hover:text-blue-500" size={32} />
                </div>
                <p className="text-slate-600 font-medium text-center">파일을 클릭하거나 드래그하여 업로드하세요</p>
                <p className="text-slate-400 text-sm mt-1">지원 형식: .pptx (최대 50MB)</p>
              </>
            )}
          </div>
        </div>

        <div className="mt-6">
          <label className="block text-sm font-semibold text-slate-700 mb-2">관리자 암호</label>
          <input
            type="password"
            placeholder="업로드를 위해 암호를 입력하세요"
            value={passcode}
            onChange={(e) => setPasscode(e.target.value)}
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm"
          />
        </div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 bg-red-50 text-red-600 rounded-xl flex items-center gap-3 text-sm"
            >
              <AlertCircle size={18} />
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <button
          type="submit"
          disabled={!file || isUploading}
          className={`
            w-full mt-6 py-4 rounded-xl font-bold text-white transition-all
            ${!file || isUploading
              ? 'bg-slate-200 cursor-not-allowed'
              : 'bg-primary hover:bg-primary-hover shadow-lg shadow-primary/25 active:scale-[0.98]'}
          `}
        >
          {isUploading ? (
            <div className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              업로드 중...
            </div>
          ) : '강의 영상 생성하기'}
        </button>
      </form>
    </div>
  );
};

export default UploadForm;
