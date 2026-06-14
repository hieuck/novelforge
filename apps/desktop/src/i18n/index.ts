import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import vi from './locales/vi.json'
import en from './locales/en.json'

const savedLang = typeof localStorage !== 'undefined' ? localStorage.getItem('novelforge:lang') : null

i18n.use(initReactI18next).init({
  resources: { vi: { translation: vi }, en: { translation: en } },
  lng: savedLang || 'vi',
  fallbackLng: 'vi',
  interpolation: { escapeValue: false },
  returnObjects: true,
})

export function setLanguage(lang: string) {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('novelforge:lang', lang)
  }
  i18n.changeLanguage(lang)
}

export default i18n
