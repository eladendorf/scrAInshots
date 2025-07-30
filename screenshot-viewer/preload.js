const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  getPlatform: () => ipcRenderer.invoke('get-platform'),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  onFolderSelected: (callback) => ipcRenderer.on('folder-selected', (event, path) => callback(path)),
  onFolderDetected: (callback) => ipcRenderer.on('folder-detected', (event, path) => callback(path))
})