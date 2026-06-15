/** Shared type definitions for NovelForge. */

export interface Project {
  id: string
  title: string
  description?: string | null
  genre?: string | null
  language?: string
  style_guide?: string | null
  summary?: string | null
  created_at?: string
  updated_at?: string
}

export interface Chapter {
  id: string
  project_id: string
  title?: string
  content?: string
  scene_order?: number
  status?: string
  word_count?: number
  summary?: string | null
  notes?: string | null
  illustration_url?: string | null
  created_at?: string
  updated_at?: string
}

export interface Character {
  id: string
  project_id: string
  name: string
  alias?: string | null
  gender?: string | null
  portrait_url?: string | null
  role?: string | null
  age?: string | null
  personality?: string | null
  appearance?: string | null
  goals?: string | null
  secrets?: string | null
  relationships?: Record<string, string> | null
  first_appearance?: string | null
  notes?: string | null
  illustration_url?: string | null
  summary?: string | null
}

export interface LoreItem {
  id: string
  project_id: string
  lore_type: string
  name: string
  description?: string | null
  tags?: string[] | null
  related_chapters?: string[] | null
  related_characters?: string[] | null
  metadata?: Record<string, any> | null
}

export interface TimelineEvent {
  id: string
  project_id: string
  title: string
  event_date?: string | null
  relative_order?: string | null
  description?: string | null
  involved_characters?: string[] | null
  related_chapters?: string[] | null
  metadata?: Record<string, any> | null
}

export interface AISettings {
  provider: string
  base_url: string
  api_key: string
  model: string
  temperature: number
  max_tokens: number
}

export interface AppInfo {
  app: string
  version: string
  python: string
  description: string
  repo: string
  error?: string
}



