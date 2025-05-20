# AutoRia Scraper

## 📌 Business Task

Create an application that periodically scrapes the AutoRia platform (used cars section). The app should start from a hardcoded URL and visit each car listing page to extract relevant data.

---

## 🚀 Features

- Daily scraping of AutoRia's used car listings.
- Saves structured data to a PostgreSQL database.
- Prevents duplicate entries.
- Dumps the PostgreSQL database daily at a specified time.
- Dockerized environment using `docker-compose`.
- Logging of all operations.
- High-performance and efficient data collection.

---

## 📥 Usage

### 1. Configure Environment Variables

```bash
cp .env.sample .env
```

### 2. Build and Run with Docker

```bash
docker-compose up -d --build
```



