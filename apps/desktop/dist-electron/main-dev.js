"use strict";
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const { app, BrowserWindow } = require('electron');
const path = require('path');
let mainWindow = null;
const port = process.env.PORT || 5173;
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
        },
    });
    mainWindow.loadURL(`http://localhost:${port}`);
    mainWindow.showDevTools();
}
app.whenReady().then(createWindow);
