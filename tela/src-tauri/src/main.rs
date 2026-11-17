// Tela principal da Caixa de Ferramentas (v1.6.0).
//
// O visual é HTML/CSS (pasta ../src). Todo o resto continua no Python da Caixa:
// esta janela roda `Caixa.exe --ponte` uma vez e conversa com ele por stdin/stdout
// (uma linha JSON por pedido). Fora do instalador, CAIXA_PONTE="python;caminho\ponte_tela.py"
// aponta pra ponte de desenvolvimento.
//
// Extras: bandeja (fechar esconde), Ctrl+Espaço chama a janela de qualquer lugar,
// uma instância só (abrir de novo traz a janela que já existe), --bandeja inicia escondida.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader, Write};
use std::os::windows::process::CommandExt;
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;

use serde_json::Value;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Emitter, Manager, State, WindowEvent};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

const SEM_JANELA: u32 = 0x0800_0000; // CREATE_NO_WINDOW

struct Canal {
    filho: Child,
    entrada: ChildStdin,
    saida: BufReader<ChildStdout>,
    proximo: u64,
}

#[derive(Default)]
struct Ponte(Mutex<Option<Canal>>);

fn comando_ponte() -> Command {
    if let Ok(dev) = std::env::var("CAIXA_PONTE") {
        let mut partes = dev.split(';');
        let prog = partes.next().unwrap_or("python").to_string();
        let mut c = Command::new(prog);
        c.args(partes);
        return c;
    }
    let pasta = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|d| d.to_path_buf()))
        .unwrap_or_default();
    let mut c = Command::new(pasta.join("Caixa.exe"));
    c.arg("--ponte");
    c
}

fn abrir_canal() -> Result<Canal, String> {
    let mut filho = comando_ponte()
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .creation_flags(SEM_JANELA)
        .spawn()
        .map_err(|e| format!("não consegui ligar a ponte com a Caixa: {e}"))?;
    let entrada = filho.stdin.take().ok_or("ponte sem entrada")?;
    let saida = BufReader::new(filho.stdout.take().ok_or("ponte sem saída")?);
    Ok(Canal { filho, entrada, saida, proximo: 1 })
}

fn conversar(canal: &mut Canal, mut pedido: Value) -> Result<Value, String> {
    let id = canal.proximo;
    canal.proximo += 1;
    pedido["id"] = Value::from(id);
    let linha = serde_json::to_string(&pedido).map_err(|e| e.to_string())?;
    canal.entrada.write_all(linha.as_bytes()).map_err(|e| e.to_string())?;
    canal.entrada.write_all(b"\n").map_err(|e| e.to_string())?;
    canal.entrada.flush().map_err(|e| e.to_string())?;
    let mut resposta = String::new();
    loop {
        resposta.clear();
        let n = canal.saida.read_line(&mut resposta).map_err(|e| e.to_string())?;
        if n == 0 {
            return Err("a ponte fechou".into());
        }
        // ignora qualquer linha que não seja a resposta deste pedido
        if let Ok(v) = serde_json::from_str::<Value>(resposta.trim()) {
            if v.get("id").and_then(Value::as_u64) == Some(id) {
                return if v.get("ok").and_then(Value::as_bool) == Some(true) {
                    Ok(v.get("res").cloned().unwrap_or(Value::Null))
                } else {
                    Err(v.get("erro").and_then(Value::as_str).unwrap_or("erro na ponte").to_string())
                };
            }
        }
    }
}

#[tauri::command]
async fn ponte(app: AppHandle, pedido: Value) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let estado: State<Ponte> = app.state();
        let mut guarda = estado.0.lock().map_err(|_| "ponte travada".to_string())?;
        // tenta duas vezes: se a ponte tiver caído, liga de novo
        for tentativa in 0..2 {
            if guarda.is_none() {
                *guarda = Some(abrir_canal()?);
            }
            let canal = guarda.as_mut().unwrap();
            match conversar(canal, pedido.clone()) {
                Ok(v) => return Ok(v),
                Err(e) => {
                    let caiu = canal.filho.try_wait().map(|s| s.is_some()).unwrap_or(true)
                        || e == "a ponte fechou";
                    if caiu && tentativa == 0 {
                        *guarda = None;
                        continue;
                    }
                    return Err(e);
                }
            }
        }
        Err("a ponte não respondeu".into())
    })
    .await
    .map_err(|e| e.to_string())?
}

fn mostrar(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.unminimize();
        let _ = w.show();
        let _ = w.set_focus();
        let _ = w.emit("focar-busca", ());
    }
}

fn alternar(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let visivel = w.is_visible().unwrap_or(false) && !w.is_minimized().unwrap_or(false);
        let focada = w.is_focused().unwrap_or(false);
        if visivel && focada {
            let _ = w.hide();
        } else {
            mostrar(app);
        }
    }
}

fn main() {
    let ctrl_espaco = Shortcut::new(Some(Modifiers::CONTROL), Code::Space);
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| mostrar(app)))
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(move |app, atalho, evento| {
                    if atalho == &ctrl_espaco && evento.state() == ShortcutState::Pressed {
                        alternar(app);
                    }
                })
                .build(),
        )
        .manage(Ponte::default())
        .invoke_handler(tauri::generate_handler![ponte])
        .setup(move |app| {
            // Ctrl+Espaço: se outro programa já usa, a Caixa abre igual, só sem o atalho
            let _ = app.global_shortcut().register(ctrl_espaco);

            let abrir = MenuItem::with_id(app, "abrir", "Abrir a Caixa", true, None::<&str>)?;
            let classica = MenuItem::with_id(app, "classica", "Caixa clássica", true, None::<&str>)?;
            let sair = MenuItem::with_id(app, "sair", "Sair", true, None::<&str>)?;
            let sep = PredefinedMenuItem::separator(app)?;
            let menu = Menu::with_items(app, &[&abrir, &classica, &sep, &sair])?;
            TrayIconBuilder::with_id("caixa")
                .icon(app.default_window_icon().cloned().ok_or("sem ícone")?)
                .tooltip("Caixa de Ferramentas — Ctrl+Espaço")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, ev| match ev.id().as_ref() {
                    "abrir" => mostrar(app),
                    "classica" => {
                        let app = app.clone();
                        tauri::async_runtime::spawn(async move {
                            let _ = ponte(app, serde_json::json!({"op": "classica"})).await;
                        });
                    }
                    "sair" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, ev| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = ev {
                        mostrar(tray.app_handle());
                    }
                })
                .build(app)?;

            // teste automático: CAIXA_TELA_BUSCA="texto" digita na barra depois de abrir
            if let Ok(texto) = std::env::var("CAIXA_TELA_BUSCA") {
                let app2 = app.handle().clone();
                std::thread::spawn(move || {
                    std::thread::sleep(std::time::Duration::from_secs(6));
                    let _ = app2.emit("buscar", texto);
                });
            }

            if std::env::args().any(|a| a == "--bandeja") {
                if let Some(w) = app.get_webview_window("main") {
                    let _ = w.hide();
                }
            }
            Ok(())
        })
        .on_window_event(|janela, ev| {
            // fechar a janela só esconde na bandeja (Sair fica no menu da bandeja)
            if let WindowEvent::CloseRequested { api, .. } = ev {
                api.prevent_close();
                let _ = janela.hide();
            }
        })
        .build(tauri::generate_context!())
        .expect("erro ao iniciar a Caixa")
        .run(|app, ev| {
            if let tauri::RunEvent::Exit = ev {
                let estado: State<Ponte> = app.state();
                let canal = match estado.0.lock() {
                    Ok(mut g) => g.take(),
                    Err(_) => None,
                };
                if let Some(mut c) = canal {
                    let _ = c.filho.kill();
                }
            }
        });
}
