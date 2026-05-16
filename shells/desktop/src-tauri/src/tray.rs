// Tray icon + tray menu.
//
// Right-clicking the tray icon shows: Open · New project · Settings ·
// Quit. Left-click (Linux/Windows) toggles the main window. macOS
// follows the platform convention (left-click always opens the menu).
//
// The icon is the same `icons/32x32.png` shipped in the bundle so
// designers don't have to manage a separate tray asset.

use tauri::{
    image::Image,
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager, Runtime,
};

const ICON_PNG: &[u8] = include_bytes!("../icons/32x32.png");

pub fn setup<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    let open = MenuItemBuilder::with_id("tray:open", "Open Agent Generator")
        .build(app)?;
    let new_project = MenuItemBuilder::with_id("tray:new", "New project…")
        .accelerator("CmdOrCtrl+N")
        .build(app)?;
    let settings = MenuItemBuilder::with_id("tray:settings", "Settings…")
        .accelerator("CmdOrCtrl+,")
        .build(app)?;
    let quit = MenuItemBuilder::with_id("tray:quit", "Quit")
        .accelerator("CmdOrCtrl+Q")
        .build(app)?;

    let menu = MenuBuilder::new(app)
        .item(&open)
        .item(&new_project)
        .item(&settings)
        .separator()
        .item(&quit)
        .build()?;

    let icon =
        Image::from_bytes(ICON_PNG).unwrap_or_else(|_| {
            // Fallback to a 1x1 transparent pixel so we never crash if
            // the icon failed to compile in (e.g. on first build before
            // `npx cap add` has populated the icons/ directory).
            Image::new_owned(vec![0u8; 4], 1, 1)
        });

    TrayIconBuilder::with_id("main")
        .icon(icon)
        .icon_as_template(true) // macOS: respect dark/light menubar
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id().as_ref() {
            "tray:open" => focus_main(app),
            "tray:new" => emit_route(app, "/generate?new=1"),
            "tray:settings" => emit_route(app, "/settings"),
            "tray:quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            // Left-click on Win/Linux toggles the window. macOS keeps
            // the platform default (always opens the menu).
            if cfg!(not(target_os = "macos")) {
                if let TrayIconEvent::Click {
                    button: MouseButton::Left,
                    button_state: MouseButtonState::Up,
                    ..
                } = event
                {
                    toggle_main(tray.app_handle());
                }
            }
        })
        .build(app)?;
    Ok(())
}

fn focus_main<R: Runtime>(app: &AppHandle<R>) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

fn toggle_main<R: Runtime>(app: &AppHandle<R>) {
    if let Some(w) = app.get_webview_window("main") {
        let visible = w.is_visible().unwrap_or(false);
        if visible {
            let _ = w.hide();
        } else {
            focus_main(app);
        }
    }
}

fn emit_route<R: Runtime>(app: &AppHandle<R>, path: &str) {
    focus_main(app);
    let _ = app.emit_to("main", "navigate", path.to_string());
}
