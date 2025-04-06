use parking_lot::Mutex;
use serde::Serialize;
use tauri::Emitter; // Needed for AppHandle::emit

// State definition
#[derive(Default, Debug)] // Default needed for initial state
pub struct AppState {
    pub count: i32,
}

// Wrapper struct to hold the state behind a Mutex
pub struct AppStateWrapper(pub Mutex<AppState>);

// Payload for the state_changed event
#[derive(Clone, Serialize)]
pub struct StatePayload {
    count: i32,
}

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn increment(
    state: tauri::State<'_, AppStateWrapper>,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    let mut app_state = state.0.lock();
    app_state.count += 1;
    println!("Incremented count to: {}", app_state.count); // Logging for debug
                                                           // Emit the state_changed event to all windows
    app_handle
        .emit(
            "state_changed",
            StatePayload {
                count: app_state.count,
            },
        )
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn decrement(
    state: tauri::State<'_, AppStateWrapper>,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    let mut app_state = state.0.lock();
    app_state.count -= 1;
    println!("Decremented count to: {}", app_state.count); // Logging for debug
                                                           // Emit the state_changed event to all windows
    app_handle
        .emit(
            "state_changed",
            StatePayload {
                count: app_state.count,
            },
        )
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_initial_state(state: tauri::State<'_, AppStateWrapper>) -> Result<i32, String> {
    let app_state = state.0.lock();
    println!("Returning initial state: {}", app_state.count); // Logging for debug
    Ok(app_state.count)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppStateWrapper(Mutex::new(AppState::default()))) // Add managed state
        .invoke_handler(tauri::generate_handler![
            greet, // Keep existing commands
            increment,
            decrement,
            get_initial_state
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
