import { useEffect, useRef, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import i18n, { setLanguage } from '../i18n'
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
  const { t } = useTranslation()
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
    setStatus(res.ok ? {type:'success',msg:t('settings.saved_ok')} : {type:'error',msg:res.error??t('settings.saved_fail')})
    setSaving(false)
  }
  const handleTest = async () => {
    setTesting(true); setStatus(null)
    const res = await testConnection(form)
    setStatus(res.ok ? {type:'success',msg:t('settings.test_ok')+(res.response?': '+res.response:'')} : {type:'error',msg:res.error??t('settings.test_fail')})
    setTesting(false)
  }
  const handleLoadModels = async () => {
    setLoadingModels(true); setStatus(null); setShowModelDrop(false)
    try {
      const p = new URLSearchParams({provider:form.provider,base_url:form.base_url})
      if (form.api_key) p.set('api_key', form.api_key)
      const data = await api.get<{models:string[];error?:string}>('/settings/models?'+p.toString())
      if (data.error) { setStatus({type:'error',msg:t('settings.models_error',{error:data.error})}); setModels([]) }
      else if (!data.models.length) { setStatus({type:'error',msg:t('settings.models_empty')}); setModels([]) }
      else { setModels(data.models); setShowModelDrop(true) }
    } catch (e:unknown) { setStatus({type:'error',msg:t('settings.data_error',{msg:e instanceof Error?e.message:'unknown'})}); setModels([]) }
    setLoadingModels(false)
  }
  const handleCheckUpdate = useCallback(async () => {
    setCheckingUpdate(true); setUpdateMsg(null)
    try {
      const res = await api.get<{update_available:boolean;new_commits:number;latest_commit?:string;error?:string}>('/update/check')
      if (res.error) throw new Error(res.error)
      setUpdateMsg(res.update_available ? t('settings.update_available',{count:res.new_commits}) : t('settings.update_current'))
    } catch (e: unknown) {
      setUpdateMsg(t('settings.update_error',{msg:e instanceof Error?e.message:'unknown'}))
    } finally {
      setCheckingUpdate(false)
    }
  }, [t])
  const handleApplyUpdate = useCallback(async () => {
    if (checkingUpdate) return
    setCheckingUpdate(true); setUpdateMsg(null)
    try {
      const res = await api.post<{success:boolean;message:string;commit?:string}>('/update/apply', {})
      if (!res.success) throw new Error(res.message)
      setUpdateMsg(t('settings.update_applied'))
    } catch (e: unknown) {
      setUpdateMsg(t('settings.update_failed',{msg:e instanceof Error?e.message:'unknown'}))
    } finally {
      setCheckingUpdate(false)
    }
  }, [checkingUpdate, t])

  const handleClearAll = async () => {
    if (dangerConfirm !== 'DELETE ALL') return
    setClearing(true)
    try {
      await api.delete('/settings/data/all')
      setDangerConfirm(''); setTab('ai')
      setStatus({type:'success',msg:t('settings.data_deleted')})
    } catch (e:unknown) { setStatus({type:'error',msg:t('settings.data_error',{msg:e instanceof Error?e.message:'unknown'})}) }
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
      <h1 className="mb-0.5 text-xl font-bold text-slate-100">{t('settings.title')}</h1>
      <p className="mb-5 text-sm text-slate-500">{t('settings.subtitle')}</p>
      <div className="flex border-b border-slate-800 mb-6">
        {(['ai','about','danger'] as Tab[]).map((tabName) => (
          <button key={tabName} onClick={() => setTab(tabName)} className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${tab===tabName?'border-indigo-500 text-indigo-400':'border-transparent text-slate-500 hover:text-slate-300'}`}>
            {tabName==='ai' && t('settings.tab_ai')}
            {tabName==='about' && <><Info className="h-3.5 w-3.5"/>{t('settings.tab_about')}</>}
            {tabName==='danger' && <><AlertTriangle className="h-3.5 w-3.5 text-red-400"/><span className="text-red-400">{t('settings.tab_danger')}</span></>}
          </button>
        ))}
      </div>

      {tab==='ai' && (
        <form onSubmit={handleSave} className="space-y-4 rounded-lg border border-slate-800 bg-slate-900 p-5">
          <div><label className={lbl}>{t('settings.provider')}</label>
            <select className={inp} value={form.provider} onChange={e=>onProviderChange(e.target.value)}>
              {PROVIDERS.map(p=><option key={p.value} value={p.value}>{p.label}</option>)}
            </select></div>
          <div><label className={lbl}>{t('settings.base_url')}</label>
            <input className={inp} value={form.base_url} onChange={e=>setField('base_url',e.target.value)}/></div>
          <div><label className={lbl}>{t('settings.api_key')} <span className="normal-case text-slate-600">{t('settings.api_key_hint')}</span></label>
            <input type="password" className={inp} placeholder={t('settings.api_key_placeholder')} value={form.api_key??''} onChange={e=>setField('api_key',e.target.value)}/></div>
          <div>
            <label className={lbl}>{t('settings.model')}</label>
            <div className="relative" ref={dropRef}>
              <div className="flex gap-2">
                <input className={inp+' flex-1'} placeholder={t('settings.model_placeholder')}
                  value={form.model} onChange={e=>setField('model',e.target.value)} onFocus={()=>models.length>0&&setShowModelDrop(true)}/>
                {models.length>0&&<button type="button" onClick={()=>setShowModelDrop(v=>!v)} className="rounded-md border border-slate-700 px-2 text-slate-400 hover:border-slate-500 hover:text-slate-200">
                  <ChevronDown className={`h-4 w-4 transition-transform ${showModelDrop?'rotate-180':''}`}/></button>}
                <button type="button" onClick={handleLoadModels} disabled={loadingModels} title={t('settings.load_models_tooltip')}
                  className="flex items-center gap-1.5 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
                  {loadingModels?<Loader2 className="h-4 w-4 animate-spin"/>:<RefreshCw className="h-4 w-4"/>} {t('settings.load_models')}
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
            <p className="mt-1.5 text-xs text-slate-600">{t('settings.model_helper')}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className={lbl}>{t('settings.temperature')}</label>
              <input type="number" step="0.1" min="0" max="2" className={inp} value={form.temperature} onChange={e=>setField('temperature',parseFloat(e.target.value))}/></div>
            <div><label className={lbl}>{t('settings.max_tokens')}</label>
              <input type="number" step="256" min="256" className={inp} value={form.max_tokens} onChange={e=>setField('max_tokens',parseInt(e.target.value))}/></div>
          </div>
          {statusEl}
          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={saving} className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
              {saving&&<Loader2 className="h-4 w-4 animate-spin"/>}{saving?t('settings.saving'):t('settings.save')}</button>
            <button type="button" onClick={handleTest} disabled={testing} className="flex items-center gap-2 rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-slate-600 hover:text-white disabled:opacity-50">
              {testing&&<Loader2 className="h-4 w-4 animate-spin"/>}{testing?t('settings.testing'):t('settings.test')}</button>
          </div>
        </form>
      )}

      {tab==='about' && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 space-y-4">
            {!about ? <div className="flex items-center gap-2 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin"/>{t('settings.about_loading')}</div>
            : about.error ? <div className="flex items-center gap-2 text-sm text-red-400"><XCircle className="h-4 w-4"/>{about.error}</div>
            : <>
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-indigo-600 p-2.5"><Info className="h-5 w-5 text-white"/></div>
                <div><div className="text-lg font-bold text-slate-100">{about.app}</div><div className="text-sm text-slate-400">{about.description}</div></div>
              </div>
              <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm border-t border-slate-800 pt-4">
                <div className="text-slate-500">{t('settings.about_version')}</div><div className="font-mono text-slate-200">v{about.version}</div>
                <div className="text-slate-500">{t('settings.about_engine')}</div><div className="font-mono text-slate-200">{about.python}</div>
                <div className="text-slate-500">{t('settings.about_repo')}</div>
                <a href={about.repo} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline truncate">{about.repo}</a>
              </div>
              <div className="border-t border-slate-800 pt-3">
                <div className="text-xs text-slate-500 mb-2">{t('settings.about_tech_stack')}</div>
                <div className="flex flex-wrap gap-2">{TECH_STACK.map(t=><span key={t} className="rounded-full border border-slate-700 px-2.5 py-0.5 text-xs text-slate-400">{t}</span>)}</div>
              </div>
              <div className="border-t border-slate-800 pt-3 flex items-center gap-3">
                <span className="text-xs text-slate-500">Language / Ngôn ngữ</span>
                <select
                  className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200 focus:outline-none"
                  value={i18n.language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="vi">Tiếng Việt</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div className="rounded-md border border-yellow-900/60 bg-yellow-950/30 px-3 py-2 text-xs text-yellow-500">
                {t('settings.about_security_warning')}
              </div>
            </>}
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 space-y-3">
            <div className="text-sm font-medium text-slate-300">{t('settings.check_updates')}</div>
            <p className="text-xs text-slate-500">{t('settings.check_updates_desc')}</p>
            <div className="flex items-center gap-3 flex-wrap">
              <button onClick={handleCheckUpdate} disabled={checkingUpdate}
                className="flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
                {checkingUpdate?<Loader2 className="h-4 w-4 animate-spin"/>:<RefreshCw className="h-4 w-4"/>}
                {checkingUpdate?t('settings.checking'):t('settings.check_now')}
              </button>
              <button onClick={handleApplyUpdate} disabled={checkingUpdate}
                className="flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white disabled:opacity-40">
                {checkingUpdate?<Loader2 className="h-4 w-4 animate-spin"/>:<span>{t('settings.apply_update')}</span>}
                {checkingUpdate?t('settings.updating'):t('settings.apply_update')}
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
              <h2 className="text-sm font-semibold text-red-400">{t('settings.danger_title')}</h2>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              {t('settings.danger_desc')}
            </p>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                {t('settings.danger_confirm_label')}
              </label>
              <input autoComplete="off"
                className="w-full rounded-md border border-red-900/60 bg-slate-800 px-3 py-2 text-sm font-mono text-slate-200 placeholder:text-slate-600 focus:border-red-600 focus:outline-none"
                placeholder={t('settings.danger_confirm_placeholder')} value={dangerConfirm} onChange={e=>setDangerConfirm(e.target.value)}/>
            </div>
            <button onClick={handleClearAll} disabled={dangerConfirm!=='DELETE ALL'||clearing}
              className="flex items-center gap-2 rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              {clearing?<Loader2 className="h-4 w-4 animate-spin"/>:<Trash2 className="h-4 w-4"/>}
              {clearing?t('settings.deleting'):t('settings.delete_button')}
            </button>
          </div>
          {statusEl}
        </div>
      )}
    </div>
  )
}
