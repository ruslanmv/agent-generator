// Native app menu — macOS menu bar, Windows/Linux Alt-menu.
//
// Keeps the structure consistent with the in-app web menu:
//   File   · New project · Open project · ─ · Settings · Quit
//   Edit   · Undo · Redo · ─ · Cut · Copy · Paste · Select all
//   View   · Toggle full screen · Toggle developer tools
//   Window · Minimize · Zoom
//   Help   · Documentation · Report an issue · About
//
// Menu-driven navigation emits a `navigate` event with the same shape
// the deep-link router uses, so the SPA can listen in one place.

use tauri::{
    menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem, SubmenuBuilder},
    AppHandle, Emitter, Manager, Runtime,
};

pub fn setup<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    // ─── File ─────────────────────────────────────────────────────
    let new_project = MenuItemBuilder::with_id("menu:new", "New project…")
        .accelerator("CmdOrCtrl+N")
        .build(app)?;
    let open_project = MenuItemBuilder::with_id("menu:open", "Open project…")
        .accelerator("CmdOrCtrl+O")
        .build(app)?;
    let settings = MenuItemBuilder::with_id("menu:settings", "Settings…")
        .accelerator("CmdOrCtrl+,")
        .build(app)?;
    let quit = PredefinedMenuItem::quit(app, None)?;

    let file = SubmenuBuilder::new(app, "File")
        .item(&new_project)
        .item(&open_project)
        .separator()
        .item(&settings)
        .separator()
        .item(&quit)
        .build()?;

    // ─── Edit ─────────────────────────────────────────────────────
    let edit = SubmenuBuilder::new(app, "Edit")
        .item(&PredefinedMenuItem::undo(app, None)?)
        .item(&PredefinedMenuItem::redo(app, None)?)
        .separator()
        .item(&PredefinedMenuItem::cut(app, None)?)
        .item(&PredefinedMenuItem::copy(app, None)?)
        .item(&PredefinedMenuItem::paste(app, None)?)
        .item(&PredefinedMenuItem::select_all(app, None)?)
        .build()?;

    // ─── View ─────────────────────────────────────────────────────
    let toggle_devtools = MenuItemBuilder::with_id("menu:devtools", "Toggle developer tools")
        .accelerator("CmdOrCtrl+Alt+I")
        .build(app)?;
    let toggle_fs = MenuItemBuilder::with_id("menu:fullscreen", "Toggle full screen")
        .accelerator("F11")
        .build(app)?;
    let view = SubmenuBuilder::new(app, "View")
        .item(&toggle_fs)
        .item(&toggle_devtools)
        .build()?;

    // ─── Window ───────────────────────────────────────────────────
    let window_menu = SubmenuBuilder::new(app, "Window")
        .item(&PredefinedMenuItem::minimize(app, None)?)
        .item(&PredefinedMenuItem::maximize(app, None)?)
        .item(&PredefinedMenuItem::close_window(app, None)?)
        .build()?;

    // ─── Help ─────────────────────────────────────────────────────
    let docs = MenuItemBuilder::with_id("menu:docs", "Documentation").build(app)?;
    let report = MenuItemBuilder::with_id("menu:report", "Report an issue").build(app)?;
    let about = MenuItemBuilder::with_id("menu:about", "About Agent Generator").build(app)?;
    let help = SubmenuBuilder::new(app, "Help")
        .item(&docs)
        .item(&report)
        .separator()
        .item(&about)
        .build()?;

    let menu = MenuBuilder::new(app)
        .items(&[&file, &edit, &view, &window_menu, &help])
        .build()?;
    app.set_menu(menu)?;

    app.on_menu_event(|app, event| match event.id().as_ref() {
        "menu:new" => navigate(app, "/generate?new=1"),
        "menu:open" => navigate(app, "/projects"),
        "menu:settings" => navigate(app, "/settings"),
        "menu:about" => emit(app, "about", ""),
        "menu:docs" => emit(app, "open-external", "https://github.com/ruslanmv/agent-generator#readme"),
        "menu:report" => emit(app, "open-external", "https://github.com/ruslanmv/agent-generator/issues/new"),
        "menu:fullscreen" => {
            if let Some(w) = app.get_webview_window("main") {
                let on = w.is_fullscreen().unwrap_or(false);
                let _ = w.set_fullscreen(!on);
            }
        }
        "menu:devtools" => {
            #[cfg(debug_assertions)]
            if let Some(w) = app.get_webview_window("main") {
                if w.is_devtools_open() {
                    w.close_devtools();
                } else {
                    w.open_devtools();
                }
            }
        }
        _ => {}
    });
    Ok(())
}

fn navigate<R: Runtime>(app: &AppHandle<R>, path: &str) {
    let _ = app.emit_to("main", "navigate", path.to_string());
}

fn emit<R: Runtime>(app: &AppHandle<R>, name: &str, payload: &str) {
    let _ = app.emit_to("main", name, payload.to_string());
}
