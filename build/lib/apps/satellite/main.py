import logging
import sys
import io
import sounddevice as sd
import soundfile as sf
import numpy as np
from rich.console import Console
from core.remote_client import RemoteClient
from core import config
from datetime import datetime

console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_time():
    return f"[{datetime.now().strftime('%H:%M:%S')}]"

def record_audio_until_enter() -> bytes:
    sample_rate = 16000
    audio_data = []
    
    def _audio_callback(indata, frames, time, status):
        audio_data.append(indata.copy())

    stream = sd.InputStream(
        samplerate=sample_rate, 
        channels=1, 
        dtype='float32', 
        callback=_audio_callback
    )
    
    stream.start()
    input() # Czekaj na ENTER
    stream.stop()
    stream.close()
    
    if not audio_data:
        return None
        
    audio_np = np.concatenate(audio_data, axis=0)
    
    # Zapis w pamięci w formacie WAV
    buffer = io.BytesIO()
    sf.write(buffer, audio_np, sample_rate, format='WAV', subtype='PCM_16')
    buffer.seek(0)
    return buffer.read()

def main():
    console.print(f"[dim]{get_time()}[/dim] [bold blue]Regis Satellite (Mikrofon Sieciowy)[/bold blue]")
    
    settings = config.load_settings()
    server_url = settings.get("server_url", "http://127.0.0.1:8000")
    
    console.print(f"[dim]{get_time()} Łączenie z serwerem: {server_url}[/dim]")
    client = RemoteClient(base_url=server_url)
    
    console.print(f"[dim]{get_time()}[/dim] [green]System gotowy do nasłuchu i przesyłu audio.[/green]")
    
    while True:
        try:
            input(f"\n{get_time()} Naciśnij [ENTER], aby rozpocząć nagrywanie (lub Ctrl+C aby wyjść)...")
            console.print(f"[dim]{get_time()}[/dim] [red]Nagrywanie...[/red] Naciśnij [ENTER], aby zakończyć.")
            
            audio_bytes = record_audio_until_enter()
            
            if audio_bytes:
                console.print(f"[dim]{get_time()}[/dim] [yellow]Wysyłanie pliku dźwiękowego (WAV) do serwera Regis...[/yellow]")
                
                # Używamy mutable obiektu żeby śledzić stan wewnątrz zagnieżdżonych funkcji
                state = {"printed_prefix": False}
                
                def on_stt(token):
                    console.print(f"\n[dim]{get_time()}[/dim] [bold green]Rozpoznano (Serwer):[/bold green] {token}\n")
                
                def ensure_prefix():
                    if not state["printed_prefix"]:
                        console.print(f"[dim]{get_time()}[/dim] [bold magenta]Regis:[/bold magenta] ", end="")
                        state["printed_prefix"] = True
                
                def on_thought(token):
                    ensure_prefix()
                    console.print(f"{token}", end="", style="dim white")
                    sys.stdout.flush()
                
                def on_content(token):
                    ensure_prefix()
                    console.print(f"{token}", end="", style="bold cyan")
                    sys.stdout.flush()
                
                try:
                    client.generate_response_from_audio(
                        audio_bytes=audio_bytes,
                        on_stt_result=on_stt,
                        on_thought_token=on_thought,
                        on_content_token=on_content
                    )
                    console.print("\n")
                except Exception as e:
                    console.print(f"\n[dim]{get_time()}[/dim] [bold red]Błąd komunikacji z serwerem:[/bold red] {e}")
            else:
                console.print(f"[dim]{get_time()}[/dim] [dim]Brak zebranego materiału audio.[/dim]")
                
        except KeyboardInterrupt:
            console.print(f"\n[dim]{get_time()}[/dim] [red]Zamykanie Satellite...[/red]")
            break

if __name__ == "__main__":
    main()
