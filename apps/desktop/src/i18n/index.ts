// Re-export shared i18n — single source of truth for locales
import { i18n as sharedI18n, setLanguage as sharedSetLanguage, getSavedLanguage as sharedGetSavedLanguage } from '@novelforge/shared'

export default sharedI18n
export const i18n = sharedI18n
export const setLanguage = sharedSetLanguage
export const getSavedLanguage = sharedGetSavedLanguage
