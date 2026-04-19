import { useEffect } from 'react';
import type { Diary } from '../types/diary';
import './DiaryDetail.css';

interface DiaryDetailProps {
  diary: Diary | null;
  onClose: () => void;
}

export default function DiaryDetail({ diary, onClose }: DiaryDetailProps) {
  // ESCキーでモーダルを閉じる
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (diary) {
      document.addEventListener('keydown', handleEsc);
      // モーダル表示中はスクロールを無効化
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [diary, onClose]);

  if (!diary) return null;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    });
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="diary-detail-overlay" onClick={onClose}>
      <div className="diary-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="diary-detail-header">
          <h2 className="diary-detail-date">{formatDate(diary.date)}</h2>
          <button
            onClick={onClose}
            className="diary-detail-close"
            aria-label="閉じる"
          >
            ×
          </button>
        </div>

        <div className="diary-detail-content">
          <p>{diary.content}</p>
        </div>

        <div className="diary-detail-footer">
          <span className="diary-detail-created">
            作成日時: {formatDateTime(diary.created_at)}
          </span>
        </div>
      </div>
    </div>
  );
}
