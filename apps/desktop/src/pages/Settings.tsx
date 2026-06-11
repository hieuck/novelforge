import { useState } from 'react'
import { useSettingsStore } from '../stores/settingsStore'

export default function Settings() {
  const { settings, updateSettings } = useSettingsStore()
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<string | null>(null)

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await fetch('/api/settings/test', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          provider: settings.provider,
          base_url: settings.base_url,
          api_key: settings.api_key,
          model: settings.model,
          temperature: Number(settings.temperature),
          max_tokens: Number(settings.max_tokens),
        }),
      })
      const data = await res.json()
      setTestResult(data.ok ? 'Kết nối thành công' : 'Kết nối thất bại')
    } catch (e) {
      setTestResult('Không thể kết nối đến backend')
    } finally {
      setTesting(false)
    }
  }

  const onChange = (key: string, value: string) => updateSettings({ [key]: value })

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Cài đặt AI</h1>
      <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <div className="grid gap-4">
          <label className="block text-sm text-slate-300">
            Nhà cung cấp
            <select
              className="mt-1 w-full rounded-md bg-slate-800 p-2"
              value={settings.provider}
              onChange={(e) => onChange('provider', e.target.value)}
            >
              <option value="ollama">Ollama</option>
              <option value="openai_compat">OpenAI-compatible</option>
              <option value="openrouter">OpenRouter</option>
              <option value="lmstudio">LM Studio / vLLM</option>
            </select>
          </label>

          <label className="block text-sm text-slate-300">
            Base URL
            <input
              className="mt-1 w-full rounded-md bg-slate-800 p-2"
              value={settings.base_url}
              onChange={(e) => onChange('base_url', e.target.value)}
            />
          </label>

          <label className="block text-sm text-slate-300">
            API Key <span className="text-slate-500">(lưu cục bộ, chưa mã hóa)</span>
            <input
              className="mt-1 w-full rounded-md bg-slate-800 p-2"
              value={settings.api_key || ''}
              onChange={(e) => onChange('api_key', e.target.value)}
            />
          </label>

          <label className="block text-sm text-slate-300">
            Model
            <input
              className="mt-1 w-full rounded-md bg-slate-800 p-2"
              value={settings.model}
              onChange={(e) => onChange('model', e.target.value)}
            />
          </label>

          <div className="grid grid-cols-2 gap-4">
            <label className="block text-sm text-slate-300">
              Temperature
              <input
                type="number"
                step="0.1"
                className="mt-1 w-full rounded-md bg-slate-800 p-2"
                value={settings.temperature}
                onChange={(e) => onChange('temperature', e.target.value)}
              />
            </label>
            <label className="block text-sm text-slate-300">
              Max tokens
              <input
                type="number"
                className="mt-1 w-full rounded-md bg-slate-800 p-2"
                value={settings.max_tokens}
                onChange={(e) => onChange('max_tokens', e.target.value)}
              />
            </label>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleTest}
            disabled={testing}
            className="rounded-md bg-slate-800 px-3 py-2 text-sm text-slate-100"
          >
            {testing ? 'Đang test...' : 'Test connection'}
          </button>
          {testResult && <span className="text-sm text-slate-300">{testResult}</span>}
        </div>
      </div>
    </div>
  )
}
