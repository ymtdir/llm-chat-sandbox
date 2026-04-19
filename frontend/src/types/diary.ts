export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface Diary {
  id: number;
  user_id: number;
  date: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface DiaryListResponse {
  diaries: Diary[];
  total: number;
}
