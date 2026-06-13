import { contextBridge } from 'electron'

// Read the engine port injected via additionalArguments by the main process.
// Falls back to 9000 (the dev/default port).
const enginePort = (() => {
  const arg = process.argv.find((a) => a.startsWith('--engine-port='))
  return arg ? parseInt(arg.split('=')[1], 10) : 9000
})()

// Expose to renderer as window.__NOVELFORGE__.enginePort
// contextBridge ensures the value is trusted (set only by main process, not web content)
contextBridge.exposeInMainWorld('__NOVELFORGE__', {
  enginePort,
})
