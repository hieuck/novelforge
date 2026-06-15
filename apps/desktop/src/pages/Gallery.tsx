import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Trash2, Loader2, Image as ImageIcon } from 'lucide-react'
import { api } from '../lib/api'

interface GalleryImage {
  id: string
  filename: string
  url: string
  prompt: string
  entity_type: string | null
  mime: string
  file_size: string
  created_at: string | null
}

export default function Gallery() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const [images, setImages] = useState<GalleryImage[]>([])
  const [loading, setLoading] = useState(true)
  const [preview, setPreview] = useState<string | null>(null)

  const load = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const data = await api.get<GalleryImage[]>(`/projects/${projectId}/images`)
      setImages(data)
    } catch { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => { load() }, [projectId])

  const handleDelete = async (id: string) => {
    if (!confirm('Xóa ảnh này?')) return
    try {
      await fetch(`/api/projects/${projectId}/images/${id}`, { method: 'DELETE' })
      load()
    } catch { /* ignore */ }
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center gap-2 mb-6">
          <ImageIcon className="h-5 w-5 text-indigo-400" />
          <h1 className="text-xl font-bold text-slate-100">Image Gallery</h1>
        </div>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" />Loading...</div>
        ) : images.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-800 p-12 text-center text-sm text-slate-600">
            Chưa có ảnh nào. Tạo ảnh từ Character hoặc Chapter để xem ở đây.
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {images.map((img) => (
              <div key={img.id} className="group relative rounded-lg border border-slate-800 bg-slate-900 overflow-hidden">
                <button onClick={() => setPreview(img.url)} className="block w-full">
                  <img src={img.url} alt={img.prompt || ''} className="w-full h-48 object-cover" />
                </button>
                <div className="p-2">
                  <p className="text-[10px] text-slate-500 line-clamp-2">{img.prompt || '(no prompt)'}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[10px] text-slate-600">{img.entity_type || 'general'}</span>
                    <button onClick={() => handleDelete(img.id)} className="p-1 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Lightbox preview */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={() => setPreview(null)}>
          <img src={preview} className="max-h-[90vh] max-w-[90vw] object-contain" alt="preview" />
        </div>
      )}
    </div>
  )
}
