const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')
const os = require('os')

let mainWindow
let apiProcess

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'public', 'icon.png')
  })

  // In production, load the built app
  if (app.isPackaged) {
    mainWindow.loadFile(path.join(__dirname, '.next', 'export', 'index.html'))
  } else {
    // In development, load from localhost
    mainWindow.loadURL('http://localhost:3000')
  }

  // Create application menu
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Select Screenshots Folder',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow, {
              properties: ['openDirectory']
            })
            
            if (!result.canceled) {
              const folderPath = result.filePaths[0]
              // Update the Python processor with new path
              mainWindow.webContents.send('folder-selected', folderPath)
            }
          }
        },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    }
  ]

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

function startAPIServer() {
  // Start the Python API server
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3'
  const scriptPath = path.join(__dirname, '..', 'api_server.py')
  
  apiProcess = spawn(pythonPath, [scriptPath, 'server'], {
    cwd: path.join(__dirname, '..'),
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  })

  apiProcess.stdout.on('data', (data) => {
    console.log(`API Server: ${data}`)
  })

  apiProcess.stderr.on('data', (data) => {
    console.error(`API Server Error: ${data}`)
  })

  apiProcess.on('close', (code) => {
    console.log(`API Server exited with code ${code}`)
  })
}

function autoDetectScreenshotsFolder() {
  let screenshotsPath = null
  
  if (process.platform === 'darwin') {
    // macOS default screenshots location
    screenshotsPath = path.join(os.homedir(), 'Desktop')
    
    // Check for custom screenshots folder
    const customPath = path.join(os.homedir(), 'Pictures', 'Screenshots')
    if (fs.existsSync(customPath)) {
      screenshotsPath = customPath
    }
  } else if (process.platform === 'win32') {
    // Windows default screenshots location
    screenshotsPath = path.join(os.homedir(), 'Pictures', 'Screenshots')
  } else {
    // Linux
    screenshotsPath = path.join(os.homedir(), 'Pictures')
  }
  
  return screenshotsPath
}

app.whenReady().then(() => {
  createWindow()
  
  // Auto-detect screenshots folder
  const detectedPath = autoDetectScreenshotsFolder()
  if (detectedPath && mainWindow) {
    mainWindow.webContents.on('did-finish-load', () => {
      mainWindow.webContents.send('folder-detected', detectedPath)
    })
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  // Kill API server process
  if (apiProcess) {
    apiProcess.kill()
  }
  
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  // Ensure API server is killed
  if (apiProcess) {
    apiProcess.kill()
  }
})

// IPC handlers
ipcMain.handle('get-platform', () => {
  return process.platform
})

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  })
  
  if (!result.canceled) {
    return result.filePaths[0]
  }
  return null
})