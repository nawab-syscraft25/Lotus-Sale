
Author: Nawab Khan
GitHub: [https://github.com/nawabkh2040](https://github.com/nawabkh2040)

---

# Agentic AI for E-Commerce

This project is an AI-powered agent for e-commerce that provides product recommendations, store details, and smart product search.
It is built with Flask, Gunicorn, Redis, and Nginx for a production-ready setup.

---

Features:

* Product recommendations based on queries
* Smart product search (AI + semantic search)
* Show product details in card format
* Find nearby stores (lotus\_stores.db)
* Terms & Conditions support
* Production-ready deployment with Docker, Gunicorn, and Nginx

---

Project Structure:

* app.py, app\_production.py, app\_simple\_production.py → Flask application entry points
* chat.py → Core chatbot logic
* tools/ → Tools for AI agent (search, product details, store info, terms & conditions)
* templates/ and static/ → Frontend templates and assets
* docker-compose.prod.yml → Docker setup for production
* gunicorn.conf.py, nginx.conf → Server configurations
* requirements.txt, requirements-production.txt → Dependencies
* tests/ → Unit and integration tests
* README\_API.md → Detailed API documentation
* README\_Redis.md → Redis setup and integration guide

---

Installation:

1. Clone the repository

```
git clone https://github.com/your-org/ecommerce-agentic-ai.git
cd ecommerce-agentic-ai
```

2. Create and activate virtual environment

```
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

3. Install dependencies

```
pip install -r requirements.txt
```

For production:

```
pip install -r requirements-production.txt
```

---

Running the App:

Development mode:

```
python app.py
```

Production (Gunicorn):

```
gunicorn -c gunicorn.conf.py app_production:app
```

Using Docker:

```
docker-compose -f docker-compose.prod.yml up --build -d
```

---

Testing:

```
pytest tests/
```

---

More Documentation:

* For API usage and endpoints → see `README_API.md`
* For Redis setup and usage → see `README_Redis.md`

---

Roadmap:

* Add multi-language product search
* Personalization with user history
* External marketplace integration
* Analytics dashboard

---


