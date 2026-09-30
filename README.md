\# Kulcskezelő Rendszer



A rendszer kulcsok igénylését, kiadását, visszavételét és jogosultságkezelését végző webes alkalmazás.



\---



\##Technológiai stack



\- \*\*Backend:\*\* Python (Flask / APIFlask, SQLAlchemy, Authlib)

\- \*\*Adatbázis:\*\* MySQL 8.0

\- \*\*Konténerizáció:\*\* Docker \& Docker Compose

\- \*\*Linter / Formatter:\*\* Ruff



\---



\##Előfeltételek



A projekt futtatásához a következő eszközökre van szükség:

\- \[Git](https://git-scm.com/)

\- \[Docker Desktop](https://www.docker.com/products/docker-desktop/) (bekapcsolt WSL2 / Virtualizáció támogatással)



\---



\##Telepítés és Indítás



\### 1. Tároló klónozása

Klónozd a tárolót, majd lépj be a projekt mappájába:

```bash

git clone https://github.com/SteigerwaldEszter/Keys.git

cd keys





Konténerek indítása:



docker compose up -d --build



Az első indítás pár percet igénybe vehet, amíg a Docker letölti a szükséges képeket és felépíti a környezetet.



Adatbázis inicializálása:



docker compose exec backend python \_\_init\_\_db.py



\##Elérhetőségek



swaggerek:



http://localhost:5000/swagger/



http://localhost:5000/api/auth/



MySQL adatbázis:



Host: localhost



Port: 3306



Felhszanáló: user vagy root



Jelszó: password



Adatbázis neve: kulcskezelo







\##Hasznos fejlesztői parancsok



Konténer leállítása(adatok megőrzésével):



docker compose stop



Konténer újraindítása:



docker compose up -d



Konténer leállítása és teljes törlése (adatbázis-kötet nullázása):



docker compose down -v



Backend naplófájlok követése futás közben:



docker compose logs -f backend



Kódformázás és linting ellenőrzése (Ruff) commitolás előtt:



python -m ruff check --fix

python -m ruff check format



























