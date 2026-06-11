export type Project = {
  id: string;
  title: string;
  description?: string;
  genre?: string;
  language?: string;
  style_guide?: string;
  summary?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
};

export type Chapter = {
  id: string;
  project_id: string;
  title: string;
  content?: string;
  word_count?: string;
  status?: string;
  scene_order?: string;
  summary?: string;
  notes?: string;
  is_deleted?: boolean;
  created_at?: string;
  updated_at?: string;
};
