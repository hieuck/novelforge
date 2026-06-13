export interface Project {
  id: string
  title: string
  description?: string
  genre?: string
  language?: string
  style_guide?: string
  summary?: string
  created_at?: string
  updated_at?: string
}

export interface Chapter {
  id: string
  project_id: string
  title: string
  content?: string
  word_count?: number
  status?: string
  scene_order?: number
  summary?: string
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface Character {
  id: string
  project_id: string
  name: string
  alias?: string
  role?: string
  age?: string
  personality?: string
  appearance?: string
  goals?: string
  secrets?: string
  relationships?: Record<string, string>
  first_appearance?: string
  notes?: string
  summary?: string
  created_at?: string
  updated_at?: string
}

export interface LoreItem {
  id: string
  project_id: string
  lore_type: string
  name: string
  description?: string
  tags?: string[]
  related_chapters?: string[]
  related_characters?: string[]
  metadata?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface TimelineEvent {
  id: string
  project_id: string
  title: string
  event_date?: string
  relative_order?: string
  description?: string
  involved_characters?: string[]
  related_chapters?: string[]
  metadata?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface AISettings {
  provider: string
  base_url: string
  api_key?: string
  model: string
  temperature: number
  max_tokens: number
}

export const AI_ACTIONS = [
  { value: 'continue',          label: 'Tiếp tục viết',        group: 'Viết' },
  { value: 'rewrite',           label: 'Viết lại',             group: 'Viết' },
  { value: 'expand',            label: 'Mở rộng',              group: 'Viết' },
  { value: 'shorten',           label: 'Rút gọn',              group: 'Viết' },
  { value: 'dialogue',          label: 'Cải thiện hội thoại',  group: 'Viết' },
  { value: 'emotional',         label: 'Tăng cảm xúc',         group: 'Viết' },
  { value: 'cinematic',         label: 'Điện ảnh hóa',         group: 'Viết' },
  { value: 'fix_pacing',        label: 'Sửa nhịp độ',          group: 'Viết' },
  { value: 'add_sensory',       label: 'Thêm giác quan',       group: 'Viết' },
  { value: 'tension_build',     label: 'Tăng kịch tính',       group: 'Viết' },
  { value: 'perspective_shift', label: 'Đổi góc nhìn',         group: 'Viết' },
  { value: 'grammar',           label: 'Sửa ngữ pháp',         group: 'Viết' },
  { value: 'summarize_chapter', label: 'Tóm tắt chương',       group: 'Phân tích' },
  { value: 'summarize_project', label: 'Tóm tắt project',      group: 'Phân tích' },
  { value: 'continuity',        label: 'Kiểm tra nhất quán',   group: 'Phân tích' },
  { value: 'plot_holes',        label: 'Tìm plot holes',       group: 'Phân tích' },
  { value: 'next_scene',        label: 'Gợi ý cảnh tiếp',      group: 'Phân tích' },
  { value: 'character',         label: 'Tạo nhân vật',         group: 'Tạo mới' },
  { value: 'world',             label: 'Tạo lore',             group: 'Tạo mới' },
  { value: 'premise',           label: 'Tạo premise',          group: 'Tạo mới' },
  { value: 'outline',           label: 'Tạo dàn ý',            group: 'Tạo mới' },
  { value: 'translate_vi_en',   label: 'Dịch VI → EN',         group: 'Dịch' },
  { value: 'translate_en_vi',   label: 'Dịch EN → VI',         group: 'Dịch' },
] as const

export type AIAction = typeof AI_ACTIONS[number]['value']
