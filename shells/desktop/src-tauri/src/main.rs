// Tauri 2 binary entry — forwards to the library so `cargo test` can
// exercise the Rust side headlessly. Keep this file empty of logic:
// everything substantive lives in `lib.rs` and the per-plugin modules.

// Prevents an additional console window from popping up on Windows in
// release builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    agent_generator_desktop::run()
}
