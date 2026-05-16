// Deep-link router for the `agent-generator://` scheme.
//
// Maps URL paths to SPA routes and forwards them as a `navigate` event
// to the main window. The SPA listens for that event and pushes to
// react-router; cold-launch URLs are buffered until the window is
// ready.
//
// Supported paths (mirrors the SPA's react-router config):
//
//   agent-generator://generate                    → /generate
//   agent-generator://generate?new=1              → /generate?new=1
//   agent-generator://run/{run_id}?project={pid}  → /run?project=<pid>&run=<rid>
//   agent-generator://docker/{project_id}         → /docker?project=<pid>
//   agent-generator://marketplace/{agent_id}      → /marketplace?agent=<id>
//   agent-generator://settings/{section}          → /settings#<section>
//   agent-generator://pair?code=<CODE>            → /settings?pair=<CODE>
//
// Unknown paths drop the user on /generate so a malformed link from
// the wild never breaks navigation.

use std::sync::Mutex;
use tauri::{AppHandle, Emitter, Manager, Runtime, State, Url};
use tauri_plugin_deep_link::DeepLinkExt;

/// Buffer for deep links that arrived before the main window finished
/// loading. The frontend drains this on startup via the
/// `deeplink_consume_pending` command.
#[derive(Default)]
pub struct PendingDeepLinks(pub Mutex<Vec<String>>);

pub fn setup<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    app.manage(PendingDeepLinks::default());

    // Cold-launch path: drain whatever URL booted the process.
    if let Ok(urls) = app.deep_link().get_current() {
        if let Some(list) = urls {
            for url in list {
                handle(app, url);
            }
        }
    }

    // Hot path: every subsequent deep link.
    let app_handle = app.clone();
    app.deep_link().on_open_url(move |event| {
        for url in event.urls() {
            handle(&app_handle, url);
        }
    });
    Ok(())
}

fn handle<R: Runtime>(app: &AppHandle<R>, url: Url) {
    let path = map_to_route(&url);
    log::info!("deep-link {} -> {}", url, path);

    // Focus / unhide the main window so the navigation lands somewhere
    // visible.
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }

    // Always buffer the URL — the SPA drains the queue on mount via
    // `deeplink_consume_pending` so we never miss a cold-launch URL.
    if let Some(state) = app.try_state::<PendingDeepLinks>() {
        if let Ok(mut q) = state.0.lock() {
            q.push(path.clone());
        }
    }

    // Fire the live event for hot deep links — the SPA listens for
    // this and bypasses the queue when the window is already up.
    let _ = app.emit_to("main", "navigate", path);
}

/// Returns the SPA route for a deep-link URL.
/// Pure function — exposed for unit tests.
pub fn map_to_route(url: &Url) -> String {
    // Tauri's deep-link plugin gives us URLs like
    //   agent-generator://run/abc?project=xyz
    // with `host="run"` and `path="/abc"`. We treat `host` as the
    // first segment for routing.
    let host = url.host_str().unwrap_or("").to_string();
    let segments: Vec<&str> = url
        .path()
        .trim_start_matches('/')
        .split('/')
        .filter(|s| !s.is_empty())
        .collect();
    let query = url.query().unwrap_or("");

    let with_query = |base: &str| {
        if query.is_empty() {
            base.to_string()
        } else {
            format!("{base}?{query}")
        }
    };
    let append_query = |base: String| -> String {
        if query.is_empty() {
            base
        } else if base.contains('?') {
            format!("{base}&{query}")
        } else {
            format!("{base}?{query}")
        }
    };

    match host.as_str() {
        "generate" => with_query("/generate"),
        "settings" => match segments.first() {
            Some(section) => with_query(&format!("/settings#{section}")),
            None => with_query("/settings"),
        },
        "run" => {
            let mut base = "/run".to_string();
            if let Some(run_id) = segments.first() {
                base.push_str(&format!("?run={run_id}"));
            }
            append_query(base)
        }
        "docker" => match segments.first() {
            Some(pid) => append_query(format!("/docker?project={pid}")),
            None => with_query("/generate"),
        },
        "marketplace" => match segments.first() {
            Some(agent) => append_query(format!("/marketplace?agent={agent}")),
            None => with_query("/marketplace"),
        },
        "pair" => with_query("/settings"),
        _ => "/generate".to_string(),
    }
}

#[tauri::command]
pub fn deeplink_consume_pending(state: State<'_, PendingDeepLinks>) -> Vec<String> {
    state
        .0
        .lock()
        .map(|mut q| std::mem::take(&mut *q))
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn route(input: &str) -> String {
        map_to_route(&Url::parse(input).unwrap())
    }

    #[test]
    fn generate() {
        assert_eq!(route("agent-generator://generate"), "/generate");
        assert_eq!(
            route("agent-generator://generate?new=1"),
            "/generate?new=1"
        );
    }

    #[test]
    fn run_with_project() {
        assert_eq!(
            route("agent-generator://run/abc?project=xyz"),
            "/run?run=abc&project=xyz"
        );
    }

    #[test]
    fn docker() {
        assert_eq!(
            route("agent-generator://docker/proj-1"),
            "/docker?project=proj-1"
        );
    }

    #[test]
    fn marketplace_detail() {
        assert_eq!(
            route("agent-generator://marketplace/research-assistant"),
            "/marketplace?agent=research-assistant"
        );
    }

    #[test]
    fn settings_section() {
        assert_eq!(
            route("agent-generator://settings/providers"),
            "/settings#providers"
        );
    }

    #[test]
    fn unknown_falls_back_to_generate() {
        assert_eq!(route("agent-generator://nope"), "/generate");
    }
}
