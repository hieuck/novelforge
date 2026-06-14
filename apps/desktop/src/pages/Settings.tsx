import { useEffect, useRef, useState, useCallback } from 'react'
import { CheckCircle, XCircle, Loader2, RefreshCw, ChevronDown, Info, Trash2, AlertTriangle } from 'lucide-react'
import { useSettingsStore } from '../stores/settingsStore'
import { api } from '../lib/api'
import type { AISettings } from '../types'

const PROVIDERS = [
  { value: 'ollama',        label: 'Ollama (local)',     defaultUrl: 'http://localhost:11434' },
  { value: 'openai_compat', label: 'OpenAI-compatible',  defaultUrl: 'https://api.openai.com/v1' },
  { value: 'openrouter',    label: 'OpenRouter',         defaultUrl: 'https://openrouter.ai/api/v1' },
  { value: 'lmstudio',      label: 'LM Studio / vLLM',  defaultUrl: 'http://localhost:1234/v1' },
]
const TECH_STACK = ['Electron', 'React', 'Vite', 'Python FastAPI', 'SQLite']
type Tab = 'ai' | 'about' | 'danger'
interface AboutInfo { app:string;version:string;python:string;description:string;repo:string;error?:string }

export default function Settings() {
  const { settings, loaded, fetchSettings, saveSettings, testConnection } = useSettingsStore()
  const [form, setForm]       = useState<AISettings>(settings)
  const [status, setStatus]   = useState<{type:'success'|'error';msg:string}|null>(null)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving]   = useState(false)
  const [tab, setTab]         = useState<Tab>('ai')
  const [models, setModels]   = useState<string[]>([])
  const [loadingModels, setLoadingModels] = useState(false)
  const [showModelDrop, setShowModelDrop] = useState(false)
  const dropRef = useRef<HTMLDivElement>(null)
  const [about, setAbout]       = useState<AboutInfo|null>(null)
  const [checkingUpdate, setCheckingUpdate] = useState(false)
  const [updateMsg, setUpdateMsg] = useState<string|null>(null)
  const [dangerConfirm, setDangerConfirm] = useState('')
  const [clearing, setClearing] = useState(false)

  useEffect(() => { if (!loaded) fetchSettings() }, [])
  useEffect(() => { setForm(settings) }, [settings])
  useEffect(() => {
    const h = (e:MouseEvent) => { if (dropRef.current && !dropRef.current.contains(e.target as Node)) setShowModelDrop(false) }
    document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h)
  }, [])
  useEffect(() => {
    if (tab === 'about' && !about)
      api.get<AboutInfo>('/settings/about').then(setAbout).catch(() =>
        setAbout({app:'NovelForge',version:'?',python:'?',description:'',repo:'',error:'Failed to load'}))
  }, [tab])

  const setField = (k:keyof AISettings, v:string|number) => setForm(f => ({...f,[k]:v}))
  const onProviderChange = (provider:string) => {
    const p = PROVIDERS.find(x => x.value === provider)
    setForm(f => ({...f,provider,base_url:p?.defaultUrl??f.base_url}))
    setModels([]); setShowModelDrop(false)
  }
  const handleSave = async (e:React.FormEvent) => {
    e.preventDefault(); setSaving(true); setStatus(null)
    const res = await saveSettings(form)
    setStatus(res.ok ? {type:'success',msg:'Settings saved.'} : {type:'error',msg:res.error??'Failed to save.'})
    setSaving(false)
  }
  const handleTest = async () => {
    setTesting(true); setStatus(null)
    const res = await testConnection(form)
    setStatus(res.ok ? {type:'success',msg:'Connection successful'+(res.response?': '+res.response:'')} : {type:'error',msg:res.error??'Connection failed.'})
    setTesting(false)
  }
  const handleLoadModels = async () => {
    setLoadingModels(true); setStatus(null); setShowModelDrop(false)
    try {
      const p = new URLSearchParams({provider:form.provider,base_url:form.base_url})
      if (form.api_key) p.set('api_key', form.api_key)
      const data = await api.get<{models:string[];error?:string}>('/settings/models?'+p.toString())
      if (data.error) { setStatus({type:'error',msg:'Could not load models: '+data.error}); setModels([]) }
      else if (!data.models.length) { setStatus({type:'error',msg:'No models found on this provider.'}); setModels([]) }
      else { setModels(data.models); setShowModelDrop(true) }
    } catch (e:unknown) { setStatus({type:'error',msg:'Error: '+(e instanceof Error?e.message:'unknown')}); setModels([]) }
    setLoadingModels(false)
  }
  const handleCheckUpdate = useCallback(async () => {
    setCheckingUpdate(true); setUpdateMsg(null)
    try {
      const res = await api.get<{update_available:boolean;new_commits:number;latest_commit?:string;error?:string}>('/update/check')
      if (res.error) throw new Error(res.error)
      setUpdateMsg(res.update_available ? `Update available: ${res.new_commits} new commit(s).` : 'You are on the latest version.')
    } catch (e: unknown) {
      setUpdateMsg('Could not check for updates: ' + (e instanceof Error ? e.message : 'unknown'))
    } finally {
      setCheckingUpdate(false)
    }
  }, [])
  const handleApplyUpdate = useCallback(async () => {
    if (checkingUpdate) return
    setCheckingUpdate(true); setUpdateMsg(null)
    try {
      const res = await api.post<{success:boolean;message:string;commit?:string}>('/update/apply', {})
      if (!res.success) throw new Error(res.message)
      setUpdateMsg('Update applied. Please restart NovelForge.')
    } catch (e: unknown) {
      setUpdateMsg('Update failed: ' + (e instanceof Error ? e.message : 'unknown'))
    } finally {
      setCheckingUpdate(false)
    }
  }, [checkingUpdate])

  const handleClearAll = async () => {
    if (dangerConfirm !== 'DELETE ALL') return
    setClearing(true)
    try {
      await api.delete('/settings/data/all')
      setDangerConfirm(''); setTab('ai')
      setStatus({type:'success',msg:'All data deleted. Refresh the page to start fresh.'})
    } catch (e:unknown) { setStatus({type:'error',msg:'Error: '+(e instanceof Error?e.message:'unknown')}) }
    setClearing(false)
  }

  const inp = 'w-full rounded-md border border-slate-800 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-indigo-600 focus:outline-none'
  const lbl = 'block text-xs font-medium uppercase tracking-wide text-slate-500 mb-1.5'
  const statusEl = status && (
    <div className={`flex items-start gap-2 rounded-md p-3 text-sm ${status.type==='success'?'bg-green-950 text-green-300 border border-green-900':'bg-red-950 text-red-300 border border-red-900'}`}>
      {status.type==='success'?<CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0"/>:<XCircle className="h-4 w-4 mt-0.5 flex-shrink-0"/>}
      <span>{status.msg}</span>
    </div>
  )

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-0.5 text-xl font-bold text-slate-100">Settings</h1>
      <p className="mb-5 text-sm text-slate-500">Configure AI provider, view app info, manage data</p>
      <div className="flex border-b border-slate-800 mb-6">
        {(['ai','about','danger'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)} className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${tab===t?'border-indigo-500 text-indigo-400':'border-transparent text-slate-500 hover:text-slate-300'}`}>
            {t==='ai' && 'AI Provider'}
            {t==='about' && <><Info className="h-3.5 w-3.5"/>About</>}
            {t==='danger' && <><AlertTriangle className="h-3.5 w-3.5 text-red-400"/><span className="text-red-400">Danger Zone</span></>}
          </button>
        ))}
      </div>

      {tab==='ai' && (
        <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-800 bg-slate-900 p-5">
          <div><label className={lbl}>Provider</label>
            <select className={inp} value={form.provider} onChange={e=>onProviderChange(e.target.value)}>
              {PROVIDERS.map(p=><option key={p.value} value={p.value}>{p.label}</option>)}
            </select></div>
          <div><label className={lbl}>Base URL</label>
            <input className={inp} value={form.base_url} onChange={e=>setField('base_url',e.target.value)}/></div>
          <div><label className={lbl}>API Key <span className="normal-case text-slate-600">(stored locally, unencrypted)</span></label>
            <input type="password" className={inp} placeholder="Leave blank if not required" value={form.api_key??''} onChange={e=>setField('api_key',e.target.value)}/></div>
          <div>
            <label className={lbl}>Model</label>
            <div className="relative" ref={dropRef}>
              <div className="flex gap-2">
                <input className={inp+' flex-1'} placeholder="e.g. gemma3:4b, gpt-4o-mini"
                  value={form.model} onChange={e=>setField('model',e.target.value)} onFocus={()=>models.length>0&&setShowModelDrop(true)}/>
                {models.length>0&&<button type="button" onClick={()=>setShowModelDrop(v=>!v)} className="rounded-md border border-slate-700 px-2 text-slate-400 hover:border-slate-500 hover:text-slate-200">
                  <ChevronDown className={`h-4 w-4 transition-transform ${showModelDrop?'rotate-180':''}`}/></button>}
                <button type="button" onClick={handleLoadModels} disabled={loadingModels} title="Fetch available models"
                  className="flex items-center gap-1.5 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
                  {loadingModels?<Loader2 className="h-4 w-4 animate-spin"/>:<RefreshCw className="h-4 w-4"/>} Load
                </button>
              </div>
              {showModelDrop&&models.length>0&&(
                <div className="absolute left-0 right-0 top-full z-50 mt-1 max-h-52 overflow-y-auto rounded-md border border-slate-700 bg-slate-800 shadow-xl">
                  {models.map(m=>(
                    <button key={m} type="button" onClick={()=>{setField('model',m);setShowModelDrop(false)}}
                      className={`w-full px-3 py-2 text-left text-sm hover:bg-slate-700 transition-colors ${form.model===m?'bg-slate-700 text-indigo-300 font-medium':'text-slate-200'}`}>{m}</button>
                  ))}
                </div>
              )}
            </div>
            <p className="mt-1.5 text-xs text-slate-600">Click Load to fetch available models from the provider endpoint.</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className={lbl}>Temperature</label>
              <input type="number" step="0.1" min="0" max="2" className={inp} value={form.temperature} onChange={e=>setField('temperature',parseFloat(e.target.value))}/></div>
            <div><label className={lbl}>Max tokens</label>
              <input type="number" step="256" min="256" className={inp} value={form.max_tokens} onChange={e=>setField('max_tokens',parseInt(e.target.value))}/></div>
          </div>
          {statusEl}
          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={saving} className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
              {saving&&<Loader2 className="h-4 w-4 animate-spin"/>}{saving?'Saving…':'Save settings'}</button>
            <button type="button" onClick={handleTest} disabled={testing} className="flex items-center gap-2 rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-slate-600 hover:text-white disabled:opacity-50">
              {testing&&<Loader2 className="h-4 w-4 animate-spin"/>}{testing?'Testing…':'Test connection'}</button>
          </div>
        </form>
      )}

      {tab==='about' && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 space-y-4">
            {!about ? <div className="flex items-center gap-2 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin"/>Loading…</div>
            : about.error ? <div className="flex items-center gap-2 text-sm text-red-400"><XCircle className="h-4 w-4"/>{about.error}</div>
            : <>
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-indigo-600 p-2.5"><Info className="h-5 w-5 text-white"/></div>
                <div><div className="text-lg font-bold text-slate-100">{about.app}</div><div className="text-sm text-slate-400">{about.description}</div></div>
              </div>
              <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm border-t border-slate-800 pt-4">
                <div className="text-slate-500">Version</div><div className="font-mono text-slate-200">v{about.version}</div>
                <div className="text-slate-500">Python engine</div><div className="font-mono text-slate-200">{about.python}</div>
                <div className="text-slate-500">Repository</div>
                <a href={about.repo} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline truncate">{about.repo}</a>
              </div>
              <div className="border-t border-slate-800 pt-3">
                <div className="text-xs text-slate-500 mb-2">Tech stack</div>
                <div className="flex flex-wrap gap-2">{TECH_STACK.map(t=><span key={t} className="rounded-full border border-slate-700 px-2.5 py-0.5 text-xs text-slate-400">{t}</span>)}</div>
              </div>
              <div className="rounded-md border border-yellow-900/60 bg-yellow-950/30 px-3 py-2 text-xs text-yellow-500">
                ⚠ API keys are stored in plain text. Use OS keychain integration before distributing.
              </div>
            </>}
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 space-y-3">
            <div className="text-sm font-medium text-slate-300">Check for updates</div>
            <p className="text-xs text-slate-500">Checks the installed git checkout against the configured remote.</p>
            <div className="flex items-center gap-3 flex-wrap">
              <button onClick={handleCheckUpdate} disabled={checkingUpdate}
                className="flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
                {checkingUpdate?<Loader2 className="h-4 w-4 animate-spin"/>:<RefreshCw className="h-4 w-4"/>}
                {checkingUpdate?'Checking…':'Check now'}
              </button>
              <button onClick={handleApplyUpdate} disabled={checkingUpdate}
                className="flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
                {checkingUpdate?<Loader2 className="h-4 w-4 animate-spin"/>:<span>Apply update</span>}
                {checkingUpdate?'Updating…':'Apply update'}
              </button>
              {updateMsg&&<span className={`text-sm ${updateMsg.startsWith('Update available')?'text-green-400':updateMsg.startsWith('You')?'text-slate-400':'text-red-400'}`}>{updateMsg}</span>}
            </div>
          </div>
        </div>
      )}

      {tab==='danger' && (
        <div className="space-y-4">
          <div className="rounded-lg border border-red-900/60 bg-red-950/20 p-5 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0"/>
              <h2 className="text-sm font-semibold text-red-400">Delete all data</h2>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              This will <strong className="text-red-300">permanently delete</strong> all projects, chapters, characters, lore, timeline events, and jobs.
              The search index will also be cleared. <strong className="text-red-300">This cannot be undone.</strong>
            </p>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Type <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-red-300">DELETE ALL</code> to confirm
              </label>
              <input autoComplete="off"
                className="w-full rounded-md border border-red-900/60 bg-slate-800 px-3 py-2 text-sm font-mono text-slate-200 placeholder:text-slate-600 focus:border-red-600 focus:outline-none"
                placeholder="DELETE ALL" value={dangerConfirm} onChange={e=>setDangerConfirm(e.target.value)}/>
            </div>
            <button onClick={handleClearAll} disabled={dangerConfirm!=='DELETE ALL'||clearing}
              className="flex items-center gap-2 rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              {clearing?<Loader2 className="h-4 w-4 animate-spin"/>:<Trash2 className="h-4 w-4"/>}
              {clearing?'Deleting…':'Delete all data'}
            </button>
          </div>
          {statusEl}
        </div>
      )}
    </div>
  )
}
