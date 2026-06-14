import { initReactI18next } from 'react-i18next'
import { i18n, getSavedLanguage, setLanguage as sharedSetLanguage } from '@novelforge/shared'

i18n.use(initReactI18next).init()

if (typeof localStorage !== 'undefined') {
  i18n.changeLanguage(getSavedLanguage())
}

export function setLanguage(lang: string) {
  sharedSetLanguage(lang)
}

export default i18n
