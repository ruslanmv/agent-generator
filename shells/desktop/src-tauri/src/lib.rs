// Agent Generator desktop shell — Tauri 2 entry point.
//
// Responsibilities:
//   • Single-instance enforcement (a second `agent-generator://` deep
//     link wakes the existing window instead of spawning a duplicate).
//   • Register every plugin the frontend's `platform/tauri.ts` adapter
//     dynamic-imports.
//   • Tray icon + native menus + deep-link router (Batch 26).
//   • Forward `agent-generator://…` deep links to the frontend via
//     the `deeplink` module — both cold-launch and hot events.
//
// Submodules:
//   • tray      — tray icon + tray menu
//   • menu      — native app menu (macOS menu bar / Win/Linux Alt-menu)
//   • deeplink  — agent-generator:// URL router

mod deeplink;
mod menu;
mod tray;

use serde::Serialize;
use tauri::{Builder, Manager};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder: Builder<tauri::Wry> = tauri::Builder::default();

    // ─── Single-instance ──────────────────────────────────────────
    // First instance keeps running; subsequent launches with a deep
    // link forward the URL and focus the original window.
    builder = builder.plugin(tauri_plugin_single_instance::init(
        |app, _args, _cwd| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.show();
                let _ = w.set_focus();
            }
        },
    ));

    // ─── Plugins ─────────────────────────────────────────────────
    // Every plugin the frontend `platform/tauri.ts` adapter loads must
    // be initialised here. Skipping one results in a runtime "Plugin
    // not registered" error in the webview.
    builder = builder
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_stronghold::Builder::new(|password| {
            // Derive a 32-byte key from the OS-supplied password. This
            // string is only used to decrypt the user's local vault —
            // the actual JIT secrets come from the backend over HTTPS.
            use std::iter::FromIterator;
            let mut buf = Vec::<u8>::from_iter(password.as_bytes().iter().copied());
            buf.resize(32, 0);
            buf
        }).build());

    // Auto-updater is a compile-time feature so dev builds don't need
    // a signing key.
    #[cfg(feature = "updater")]
    {
        builder = builder.plugin(tauri_plugin_updater::Builder::new().build());
    }

    // ─── Setup hook ──────────────────────────────────────────────
    let app = builder
        .setup(|app| {
            let version = app.package_info().version.to_string();
            log::info!("agent-generator desktop {} starting", version);

            // Native menu + tray + deep-link router. Order matters:
            // deep-link setup may emit `navigate` events the menu /
            // tray listeners might also fire, so we wire all three
            // before returning from setup().
            menu::setup(app.handle())?;
            tray::setup(app.handle())?;
            deeplink::setup(app.handle())?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            ping,
            version_info,
            deeplink::deeplink_consume_pending,
        ]);

    app.run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// ─── Commands exposed to the frontend ───────────────────────────
// Mirrors the `info` field on the JS platform adapter, in case the
// frontend ever needs to ask the native side directly.
#[derive(Serialize)]
struct VersionInfo {
    name: String,
    version: String,
    tauri: String,
}

#[tauri::command]
fn version_info(app: tauri::AppHandle) -> VersionInfo {
    let pkg = app.package_info();
    VersionInfo {
        name: pkg.name.clone(),
        version: pkg.version.to_string(),
        tauri: tauri::VERSION.to_string(),
    }
}

/// Cheap liveness probe — used by the dev React Query setup to confirm
/// the IPC bridge is alive before issuing real commands.
#[tauri::command]
fn ping() -> &'static str {
    "pong"
}
