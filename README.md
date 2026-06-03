# RAG Chatbot API + Frontend

Prosty chatbot RAG oparty o:

- FastAPI jako backend HTTP
- LangGraph jako logike agenta
- Chroma jako baze wektorowa
- Ollama jako lokalny model LLM i embeddingi
- prosty frontend HTML/CSS/JS

## Struktura projektu

```text
komplet_api_bot_html/
  agent_grph.py              # graf agenta, RAG, Chroma, funkcja chat_with_agent
  main.py                    # FastAPI i endpoint /chat
  index.html                 # prosty frontend
  script.js                  # komunikacja frontendu z API
  style.css                  # wyglad frontendu
  test_agent.py              # szybki test agenta bez API
  stock_market_guide_full.pdf
  .env.example
  requirements.txt
```

## Co trzeba miec lokalnie

1. Python 3.11+.
2. Uruchomiona Ollama.
3. Pobrane modele Ollama:

```powershell
ollama pull gemma4:e4b
ollama pull nomic-embed-text
```

4. Skonfigurowany connection string do SQL Server/Azure SQL w pliku `.env`.

## Instalacja

Wejdz do folderu projektu:

```powershell
cd "D:\LG CR\komplet_api_bot_html"
```

Zainstaluj zaleznosci:

```powershell
pip install -r requirements.txt
```

Skopiuj `.env.example` do `.env` i uzupelnij connection string:

```powershell
copy .env.example .env
```

## Plik .env

Przykladowy format:

```text
SQLSERVER_CONN_STR=Driver={ODBC Driver 18 for SQL Server};Server=YOUR_SERVER;Database=YOUR_DATABASE;Encrypt=yes;TrustServerCertificate=yes;Trusted_Connection=yes
OLLAMA_EMBED_MODEL=nomic-embed-text
```


## Baza wektorowa

Kod szuka bazy Chroma tutaj:

```text
komplet_api_bot_html/stock_market_db
```

Jesli baza juz istnieje, zostanie wczytana.

Jesli baza nie istnieje, kod sprobuje utworzyc ja z pliku:

```text
komplet_api_bot_html/stock_market_guide_full.pdf
```

Folder `stock_market_db` jest ignorowany przez Git, bo jest generowany automatycznie.

## Test agenta bez API

```powershell
python test_agent.py
```

Jesli test zwroci odpowiedz modelu, mozna uruchomic API.

## Uruchomienie API

```powershell
uvicorn main:app --reload
```

Backend bedzie dostepny pod:

```text
http://127.0.0.1:8000
```

Dokumentacja FastAPI:

```text
http://127.0.0.1:8000/docs
```

## Endpoint /chat

Request:

```json
{
  "user_message": "What can I ask you about the database?",
  "thread_id": "frontend_user_1"
}
```

Response:

```json
{
  "response": "Odpowiedz modelu..."
}
```

## Frontend

Najprosciej otworz:

```text
index.html
```

w przegladarce.

Backend FastAPI musi byc wtedy uruchomiony, bo frontend wysyla zapytania do:

```text
http://127.0.0.1:8000/chat
```

Mozesz tez uruchomic prosty serwer frontendu:

```powershell
python -m http.server 5500
```

i wejsc na:

```text
http://127.0.0.1:5500
```

