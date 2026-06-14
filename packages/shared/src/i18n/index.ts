import i18n from 'i18next'
import vi from './locales/vi.json'
import en from './locales/en.json'

i18n.init({
  resources: { vi: { translation: vi }, en: { translation: en } },
  lng: 'vi',
  fallbackLng: 'vi',
  interpolation: { escapeValue: false },
  returnObjects: true,
  initImmediate: false,
})

export function setLanguage(lang: string) {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('novelforge:lang', lang)
  }
  i18n.changeLanguage(lang)
}

export function getSavedLanguage(): string {
  if (typeof localStorage !== 'undefined') {
    return localStorage.getItem('novelforge:lang') || 'vi'
  }
  return 'vi'
}

export default i18n
