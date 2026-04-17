import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Diary } from '../types/diary';
import './Diaries.css';

export default function Diaries() {
  const [diaries, setDiaries] = useState<Diary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const loadDiaries = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getDiaries(50, 0);
      setDiaries(response.diaries);
    } catch (err) {
      setError('Failed to load diaries');
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
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="diaries-page">
      <header className="diaries-header">
        <div className="container">
          <h1>My Diaries</h1>
          <div className="header-actions">
            <button
              onClick={() => navigate('/chat')}
              className="button-primary"
            >
              New Entry
            </button>
            <button onClick={handleLogout} className="button-dark">
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="diaries-main">
        <div className="container">
          {loading && (
            <div className="diaries-loading">
              <p>Loading your diaries...</p>
            </div>
          )}

          {error && (
            <div className="diaries-error">
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && diaries.length === 0 && (
            <div className="diaries-empty">
              <h3>No diaries yet</h3>
              <p>Start a conversation to create your first diary entry</p>
              <button
                onClick={() => navigate('/chat')}
                className="button-primary"
              >
                Start Writing
              </button>
            </div>
          )}

          {!loading && !error && diaries.length > 0 && (
            <div className="diaries-grid">
              {diaries.map((diary) => (
                <div key={diary.id} className="diary-card">
                  <div className="diary-date">{formatDate(diary.date)}</div>
                  <div className="diary-content">{diary.content}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
