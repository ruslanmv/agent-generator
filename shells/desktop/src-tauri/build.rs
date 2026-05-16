// Tauri build script. Re-runs the icon + capability generation step on
// every build. Keep it minimal — anything specific to the Rust side
// (codegen, env exports) belongs in `lib.rs`, not here.

fn main() {
    tauri_build::build()
}
