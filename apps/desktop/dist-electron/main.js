import { app as e, BrowserWindow as n } from "electron";
import * as i from "path";
const l = process.env.NODE_ENV !== "production";
let o = null;
function t() {
  o = new n({
    width: 1440,
    height: 900,
    title: "NovelForge",
    backgroundColor: "#06080f",
    show: !1
  }), l ? (o.loadURL("http://127.0.0.1:5173"), o.webContents.openDevTools()) : o.loadFile(i.join(__dirname, "../dist/index.html")), o.once("ready-to-show", () => o == null ? void 0 : o.show()), o.on("closed", () => {
    o = null;
  });
}
e.on("ready", t);
e.on("window-all-closed", () => {
  process.platform !== "darwin" && e.quit();
});
e.on("activate", () => {
  o || t();
});
