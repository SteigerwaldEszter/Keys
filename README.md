
# Egyetemi Kulcs- és Teremnyilvántartó Rendszer

A Projekt Labor keretében fejlesztett webalkalmazás célja az egyetemi teremfoglalások és a kulcsok mozgásának digitális nyilvántartása. A rendszer a papíralapú kulcskiadási napló helyett egy közös felületen kezeli a foglalásokat, a kulcsok kiadását és visszavételét, valamint a fontosabb adminisztrációs műveleteket.

A projekt csapatmunkában készül; a frontend és a backend külön komponensként működik, közös adatbázissal.

## Főbb funkciók

- **Teremfoglalás:** foglalások létrehozása 45 perces idősávokban, hosszabb és ismétlődő foglalások kezelése, ütközések ellenőrzése.
- **Kulcskezelés:** kulcsok nyilvántartása, kiadás és visszavétel rögzítése, a kulcsállapotok követése.
- **Terem- és eszközkezelés:** termek, kapacitások, teremtípusok és felszerelések kezelése.
- **Hibajegyek:** termekkel kapcsolatos problémák bejelentése és a hibajegyek státuszának követése.
- **Felhasználók és jogosultságok:** szerepkörhöz kötött műveletek, JWT-alapú hitelesítés.
- **Riportok és auditnapló:** a fontosabb események visszakeresése, a műveletet végző felhasználó és a változások rögzítése.
- **Health API:** a backend működési állapotának ellenőrzésére szolgáló végpont; pontos elérhetősége az alkalmazásban regisztrált útvonalaktól függ.

## Felhasználói szerepkörök

A rendszer négy fő szerepkört különböztet meg:

- **Instructor (oktató):** saját teremfoglalások létrehozása és kezelése.
- **Receptionist (portás):** kulcsok kiadása és visszavétele, a kapcsolódó adminisztráció.
- **Admin:** felhasználók, jogosultságok, termek, eszközök és kulcsok kezelése.
- **Director (igazgató):** riportok és auditnaplók megtekintése.

A hozzáférési szabályokat a backend ellenőrzi, nem csak a felhasználói felület.

## Felhasznált technológiák

A backend **Python**, **Flask / APIFlask**, **SQLAlchemy** és **Authlib** használatával készült. Az adatokat **MySQL 8.0** tárolja, az adatbázis-migrációkat **Flask-Migrate / Alembic** kezeli.

A frontend **HTML**, **CSS** és **JavaScript** alapú; kiszolgálásához **Nginx** tartozik. A komponensek **Docker Compose** segítségével indíthatók. A kódellenőrzést **Ruff**, az automatizált Python-teszteket **Pytest** támogatja.

## Projektfelépítés

```text
Keys/
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   └── KulcskezeloApp/
│       ├── app/
│       │   ├── blueprints/
│       │   ├── models/
│       │   └── extensions.py
│       ├── migrations/
│       ├── .ssh/
│       ├── __init__db.py
│       ├── config.py
│       └── run.py
├── frontend/
├── tests/
├── compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

Az API-végpontok moduljai a `blueprints`, az adatbázismodellek a `models` mappában találhatók.

## Telepítés és indítás

### Előfeltételek

A futtatáshoz **Git** és **Docker Desktop** szükséges. A helyi Python-parancsokhoz Python 3.11 és a `requirements.txt` csomagjai ajánlottak.

### 1. A projekt letöltése

```bash
git clone https://github.com/SteigerwaldEszter/Keys.git
cd Keys
```

### 2. A JWT-aláíráshoz használt kulcs előkészítése

A backend a `backend/KulcskezeloApp/.ssh/private_key.pem` fájlból olvassa be a privát RSA-kulcsot. Ez bizalmas fájl, **nem szabad feltölteni a GitHubra**.

Ha még nincs kulcsod, hozd létre a `.ssh` mappát, majd OpenSSL-lel generálj helyi fejlesztői kulcsot:

```bash
openssl genpkey -algorithm RSA -out backend/KulcskezeloApp/.ssh/private_key.pem -pkeyopt rsa_keygen_bits:2048
```

A parancs előtt a `.ssh` mappának már léteznie kell. Windows PowerShellben például:

```powershell
New-Item -ItemType Directory -Force backend/KulcskezeloApp/.ssh
```

Az OpenSSL parancsához telepített OpenSSL szükséges. Ha a csapat más kulcselőkészítési eljárást használ, azzal is megfelelő RSA privát kulcs állítható elő.

### 3. A konténerek indítása

```bash
docker compose up -d --build
```

Az első indításkor a Docker letölti a szükséges képeket és felépíti a szolgáltatásokat. Az adatbázis indulása néhány másodperccel tovább tarthat.

A konténerek állapotának ellenőrzése:

```bash
docker compose ps
```

### 4. Az adatbázis előkészítése

A projekt tartalmaz Alembic-migrációkat. **Meglévő, már inicializált adatbázison** a migrációk állapota így ellenőrizhető:

```bash
docker compose exec backend flask db current
docker compose exec backend flask db heads
```

A hiányzó migrációk a megfelelően előkészített adatbázison ezzel alkalmazhatók:

```bash
docker compose exec backend flask db upgrade
```

**Figyelem:** a `backend/KulcskezeloApp/__init__db.py` tesztadat-feltöltő fájl jelenlegi változata `db.drop_all()` és `db.create_all()` hívásokat tartalmaz. Futtatása **törli és újralétrehozza az adatbázistáblákat**, ezért meglévő adatok mellett nem használható biztonságos migrációként.

A migrációs nyilvántartás és a már kézzel végrehajtott sémafrissítések összehangolása külön ellenőrzést igényel.

## Elérhetőségek

A helyi Dockeres környezetben:

- **Frontend:** http://localhost:8080/
- **Backend / Swagger dokumentáció:** http://localhost:5000/swagger
- **Backend API:** http://localhost:5000/api/
- **MySQL:** `localhost:3306` (adatbázis: `kulcskezelo`)

A fejlesztői adatbázis-kapcsolat alapértelmezett adatai a `compose.yml` fájlban vannak. Éles környezetben ezeket környezeti változókkal és biztonságos titokkezeléssel kell helyettesíteni.

A Health API pontos útvonala a jelenlegi alkalmazásban így kereshető meg:

```bash
docker compose exec backend flask routes
```

A listában keresd a `health` nevű végpontot. Egy sikeres egészségellenőrzés általában `200 OK` választ ad; az adatbázis állapotának vizsgálata a megvalósítástól függ.

## Auditnaplózás

A rendszer naplózza többek között a bejelentkezéseket, a foglalások és kulcsok kezelését, valamint az adminisztrációs változtatásokat.

A bejegyzések tartalmazhatják az esemény típusát, az érintett rekord azonosítóját, a műveletet végző felhasználót, az időpontot és a módosítás előtti, illetve utáni értékeket.

Az auditnapló célja, hogy a rendszerben történt műveletek utólag ellenőrizhetők legyenek. A különböző modulok auditálásának integrációs tesztelése a fejlesztés része.

## Tesztelés és CI

A backend egységtesztjeihez **Pytestet** használunk. A tesztek a projekt gyökérmappájában található `tests/` könyvtárba kerülnek, és többek között a foglalási szabályokat, a jogosultságokat és az auditnaplózás működését ellenőrzik.

A jelenlegi tesztcsomag a foglalások és az auditnaplózás ellenőrzésére koncentrál. A tesztek adatbázis-műveletei helyettesíthetők, így a tesztfuttatás nem módosítja a fejlesztői MySQL-adatbázist.

### Tesztek futtatása

A tesztek begyűjtése:

```bash
python -m pytest tests --collect-only -q
```

A tesztek futtatása:

```bash
python -m pytest tests -v
```

### Kódellenőrzés

A Python-kód ellenőrzésére Ruffot használunk.

```bash
python -m ruff check .
python -m ruff format --check .
```

Az importok sorrendjének automatikus javítása:

```bash
python -m ruff check --select I --fix .
```

### GitHub Actions

A GitHub Actions workflow konfigurációja a `.github/workflows/ci.yml` fájlban található.

A CI a `main` ágra történő feltöltéseknél és az oda irányuló Pull Requestek esetén indul el.

A Ruff ellenőrzi a Python-kódot és a formázását. A kibővített CI-folyamat a Pytest segítségével automatizált egységteszteket is futtat.

A tesztek CI-be integrálása a fejlesztési folyamat része, ezért a GitHub `main` ágán elérhető workflow tartalma eltérhet a helyi fejlesztői változattól.

A futtatások eredményei a [GitHub Actions](https://github.com/SteigerwaldEszter/Keys/actions) oldalon követhetők.

## Health API

A projekt Health API végpontot is tartalmaz, amely a backend működési állapotának ellenőrzésére szolgál.

A végpont segítségével egyszerű HTTP-kéréssel ellenőrizhető, hogy az alkalmazás elérhető-e és képes-e válaszolni a kérésekre.

A Health API elsősorban a rendszer felügyeletét, az automatizált ellenőrzéseket és a hibák gyorsabb felismerését segíti.

A sikeres állapotellenőrzés jellemzően `200 OK` HTTP-választ ad.

A pontos végpont a Swagger dokumentációban vagy a Flask útvonallistájában tekinthető meg.

A Health API működése automatizált tesztekkel is ellenőrizhető.

## Hasznos Docker-parancsok

A konténerek leállítása az adatbázis-kötet megtartásával:

```bash
docker compose stop
```

Újraindítás:

```bash
docker compose up -d
```

Backendnaplók megtekintése:

```bash
docker compose logs -f backend
```

**Vigyázat:** a `docker compose down -v` parancs a tárolt adatbáziskötetet is törli. Csak akkor használd, ha szándékosan teljesen új adatbázist szeretnél.

## Fejlesztési állapot

A projekt alapvető moduljai elkészültek, a fejlesztés jelenlegi szakaszában az integrációs tesztelés, a jogosultságok és a validációk ellenőrzése, valamint a frontend és backend összehangolása zajlik.

A fejlesztés során készülő funkciók és módosítások Pull Requesteken keresztül kerülnek a `main` ágba.
