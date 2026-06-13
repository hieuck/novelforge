"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerProtocol = registerProtocol;
function registerProtocol() {
    if (process.defaultApp) {
        if (process.argv.length >= 2) {
            app.setAsDefaultProtocolClient('novelforge', process.execPath, [
                ...process.argv.slice(1),
            ]);
        }
    }
    else {
        app.setAsDefaultProtocolClient('novelforge');
    }
}
