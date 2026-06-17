# PC Build PL — konfigurator komputerów

Aplikacja internetowa napisana w Django, służąca do składania zgodnej konfiguracji
komputera. Użytkownik wybiera podzespoły według kategorii, a system sprawdza ich
zgodność (socket, typ RAM, obudowa, zasilacz itp.), oblicza łączną cenę oraz
szacowany pobór mocy i pozwala zapisać zestawy na koncie.

---

## Technologie

- Python 3.12+
- Django 5.x
- Baza danych: SQLite (`db.sqlite3`)
- Frontend: HTML + CSS + czysty JavaScript (bez frameworków)

---

## Wymagania

- Zainstalowany **Python 3.12 lub nowszy** (podczas instalacji zaznacz
„Add Python to PATH").
- Internet jest potrzebny tylko przy pierwszej instalacji zależności (`pip install`).
- Sama aplikacja działa lokalnie, bez dostępu do Internetu.

Sprawdzenie wersji Pythona:

```powershell
python --version
```

---

## Uruchomienie (pierwszy raz)

Wszystkie komendy wykonujemy w terminalu (PowerShell w VS Code:
`Terminal -> New Terminal`).

### 1. Przejdź do katalogu projektu

```powershell
cd pc_builder
```

### 2. (Zalecane) Utwórz środowisko wirtualne

```powershell
python -m venv venv
venv\Scripts\activate
```

Po aktywacji na początku wiersza pojawi się `(venv)`.

### 3. Zainstaluj zależności

```powershell
python -m pip install -r requirements.txt
```

### 4. Utwórz strukturę bazy danych

```powershell
python manage.py migrate
```

### 5. Załaduj dane początkowe (katalog części)

```powershell
python manage.py loaddata initial_data
```

> Komenda wczytuje kategorie i komponenty z pliku
> `builder/fixtures/initial_data.json` do bazy danych.

### 6. (Opcjonalnie) Utwórz konto administratora

```powershell
python manage.py createsuperuser
```

Podaj nazwę użytkownika, e-mail (można pominąć) oraz hasło.

### 7. Uruchom serwer

```powershell
python manage.py runserver 8000
```

---

## Otwórz w przeglądarce

- Strona główna: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Konfigurator: [http://127.0.0.1:8000/konfigurator/](http://127.0.0.1:8000/konfigurator/)
- Panel administratora: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

> Ważne: adres musi zawierać port **8000**. Samo `127.0.0.1` (bez portu)
> się nie otworzy.

---

## Kolejne uruchomienia

Jeśli baza danych jest już utworzona, a dane załadowane, wystarczy:

```powershell
cd c:\Users\essensilety\Downloads\Projekt\pc_config
venv\Scripts\activate        # jeśli używasz środowiska wirtualnego
python manage.py runserver 8000
```

---

## Zatrzymanie serwera

W terminalu, w którym działa serwer, naciśnij **Ctrl + C**.

Przed zamknięciem VS Code / Cursor zatrzymaj serwer, w przeciwnym razie pojawi się
ostrzeżenie o działających terminalach w tle.

---

## Struktura projektu

```
Projekt/
├── README.md                 # ten plik
└── pc_config/
    ├── manage.py             # punkt wejścia komend Django
    ├── requirements.txt      # zależności (Django)
    ├── db.sqlite3            # baza danych (po migracji)
    ├── pc_config/            # ustawienia projektu (settings, urls, wsgi)
    └── builder/              # główna aplikacja
        ├── models.py         # modele: Category, Component, SavedBuild
        ├── views.py          # strony oraz API JSON
        ├── urls.py           # routing
        ├── compatibility.py  # logika zgodności i rekomendacji
        ├── forms.py          # formularz rejestracji
        ├── admin.py          # panel administratora
        ├── fixtures/initial_data.json   # dane początkowe (kategorie i komponenty)
        ├── templates/        # szablony HTML
        └── static/builder/   # CSS i JavaScript
```

---

## Gdzie przechowywane są dane

Wszystko znajduje się w lokalnym pliku `pc_config/db.sqlite3`:

- Użytkownicy — tabela `auth_user` (hasła przechowywane jako hash).
- Katalog części — `builder_category`, `builder_component`.
- Zapisane zestawy — `builder_savedbuild`.
- Logowanie i bieżący wybór części — `django_session`.

