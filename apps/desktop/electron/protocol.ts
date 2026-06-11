export function registerProtocol(): void {
  if (process.defaultApp) {
    if (process.argv.length >= 2) {
      app.setAsDefaultProtocolClient('novelforge', process.execPath, [
        ...(process.argv.slice(1) as any),
      ]);
    }
  } else {
    app.setAsDefaultProtocolClient('novelforge');
  }
}
