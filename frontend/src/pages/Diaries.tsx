import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Diary } from '../types/diary';
import DiaryDetail from '../components/DiaryDetail';
import './Diaries.css';

export default function Diaries() {
  const [diaries, setDiaries] = useState<Diary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDiary, setSelectedDiary] = useState<Diary | null>(null);
  const navigate = useNavigate();

  const loadDiaries = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getDiaries(50, 0);
      setDiaries(response.diaries);
    } catch (err) {
      setError('日記の読み込みに失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load diaries on component mount - this is the correct pattern for initial data fetching
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDiaries();
  }, []);

  const handleLogout = () => {
    apiClient.logout();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getContentPreview = (content: string, maxLength = 150) => {
    if (content.length <= maxLength) {
      return content;
    }
    return content.substring(0, maxLength) + '...';
  };

  const handleCardClick = (diary: Diary) => {
    setSelectedDiary(diary);
  };

  const handleCloseDetail = () => {
    setSelectedDiary(null);
  };

  return (
    <div className="diaries-page">
      <header className="diaries-header">
        <div className="container">
          <h1>マイ日記</h1>
          <div className="header-actions">
            <button
              onClick={() => navigate('/chat')}
              className="button-primary"
            >
              トーク画面へ
            </button>
            <button onClick={handleLogout} className="button-dark">
              ログアウト
            </button>
          </div>
        </div>
      </header>

      <main className="diaries-main">
        <div className="container">
          {loading && (
            <div className="diaries-loading">
              <p>日記を読み込んでいます...</p>
            </div>
          )}

          {error && (
            <div className="diaries-error">
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && diaries.length === 0 && (
            <div className="diaries-empty">
              <h3>まだ日記がありません</h3>
              <p>会話を始めて最初の日記を作成しましょう</p>
              <button
                onClick={() => navigate('/chat')}
                className="button-primary"
              >
                トーク画面へ
              </button>
            </div>
          )}

          {!loading && !error && diaries.length > 0 && (
            <div className="diaries-grid">
              {diaries.map((diary) => (
                <div
                  key={diary.id}
                  className="diary-card"
                  onClick={() => handleCardClick(diary)}
                >
                  <div className="diary-date">{formatDate(diary.date)}</div>
                  <div className="diary-content-preview">
                    {getContentPreview(diary.content)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <DiaryDetail diary={selectedDiary} onClose={handleCloseDetail} />
    </div>
  );
}
